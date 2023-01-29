import math
import sys
import numpy as np
sys.path.append("..")

from main import app,DB

from models.models import Model
from functions.functions_api import get_document_info, get_market_data, restore_dataframe, store_dataframe, get_result_object
from lib.ClassWalkForward import cWalkForward

REQUIRED_ATTRIBUTES = ['is_days','oos_days','periods','param1_name','param1_values',
                        'param2_name','param2_values','param3_name','param3_values','objective_function']



@app.get("/get_wfa_info/")
async def get_wfa_info(model: Model)-> dict:
    document = DB.db['wfa'].find_one({'model_id': model.objectID})
    if document is not None:
        del document["_id"]
        del document["model_id"]

    if document is not None:
        document['unified_oos_id'] = str(document['unified_oos_id'])       

    return {'result': document}
    
@app.get("/get_wfa_periods/")
async def get_wfa_periods(model: Model, data: dict) -> dict:
    #Creamos el objeto setting   
    _total_market_days = get_document_info(model.objectID, 'dailyresult')['marketdays']
    _total_oos_market_days = _total_market_days - (data['is_days'] +1)
    periods = math.ceil(_total_oos_market_days / data['oos_days'])
    initial_is_days=[(1+data['oos_days']*(x-1)) for x in range(1,periods+1)]  
    
    #Funcion que devuelve un objeto figure de Plotly con las barras horizontales de la distribución de periodos IS y OOS
    y=[str(n) for n in range(1,periods+1)]
    x1=[int(x-1) for x in initial_is_days]
    x2=[int(data['is_days']) for x in range(1,periods+1)]
    x3=[int(data['oos_days']) for x in range(1,periods+1)]
    x3[-1]=(_total_market_days- (data['is_days'] +1))-sum(x3[0:-1])
    
    option = {
        'color': ['rgba(255,255,255,0)', 'green', 'orange'],
        'xAxis': {
            'type': 'value',
            'name': 'Market Days',
            'nameLocation': "center",
            "nameTextStyle": {
                "fontSize": 14,
                "verticalAlign": "top",
                "padding": [15,15]
            }       
            
        },
        'legend':{           
        },
        'yAxis': {
            'type': 'category',
            'data': y,
            'inverse': True,
            'name': 'Period',
            'nameLocation': 'start'
        },
        'series':[
            {
                'name': '',
                'type': 'bar',
                'stack': 'total',
                'label': {'show': False},
                'data': x1,
            },                        
            {
                'name': 'IS',
                'type': 'bar',
                'stack': 'total',
                'label': {'show': False},
                'data': x2,
            },
            {
                'name': 'OOS',
                'type': 'bar',
                'stack': 'total',
                'label': {'show': False},
                'data': x3,
            }
        ]       
    }

    return {'result': {
            'option': option,
            'periods': periods,
        }
    }
    

@app.post("/run_wfa/")
async def run_wfa(model: Model, data_wfa: dict) -> dict:
    #Primero creamos el objeto de la clase cWalkForward. Necesitamos setting y data
    setting = get_document_info(model.objectID, 'setting')   
    data = restore_dataframe('data','case', model.objectID)    
    m1_data = get_market_data(setting['instrument']['ticker'], 1, setting['instrument']['start_date'], setting['instrument']['end_date'])[['Time','High','Low','Close']]
    
    #Leemos las hipotesis de la estrategia
    strategy_id = DB.db['models'].find_one({'_id': model.objectID})['strategy_id']
    strategy_info = DB.db['strategies'].find_one({'_id': strategy_id})
    
    wfa = cWalkForward(data=data, 
                       data_wfa=data_wfa, 
                       setting=setting,
                       m1_data=m1_data,
                       tc_assumptions = strategy_info['tc_assumptions'],
                       strategy_settings = strategy_info['settings'],
                       strategy_type = strategy_info['strategy_type']                 
            )
    
    #Ejecutamos la optimización de los periodos del wfa 
    for i in range(data_wfa['periods']):     
        wfa.optimize_period(i)
    
    #Pasamos ahora a aplicar los parametros optimizidados sobre los periodos
    for i in range(len(wfa.oos_settings)):
        wfa.run_optimized_period(i,strategy_settings=strategy_info['settings'], strategy_type=strategy_info['strategy_type'])

    #Unificamos los OOS en un objeto de resultado unico
    wfa.unify_oos_result()

    #Guardamos los resultados
    # 1) Si existe alguno ya almacenado lo eliminamos para evitar duplicidades
    doc = DB.db['wfa'].find_one({'model_id': model.objectID})
    if doc is not None:
        DB.db['wfa'].delete_one({'model_id': model.objectID})
        DB.db['result'].delete_many({'model_id': model.objectID, 'super':'wfa'})
        DB.db['result_chunks'].delete_many({'model_id': model.objectID, 'super': 'wfa'})
        DB.db['dailyresult'].delete_many({'model_id': model.objectID, 'super':'wfa'})
        DB.db['data'].delete_many({'model_id': model.objectID, 'super': 'wfa'})
        DB.db['data_chunks'].delete_many({'model_id': model.objectID, 'super': 'wfa'})
        DB.db['positions'].delete_one({'model_id': model.objectID, 'super': 'wfa'})
        DB.db['orders'].delete_one({'model_id': model.objectID, 'super': 'wfa'})
        
        
    # 2) Alamacenamos Objeto DataCandle             
    DB.db['data'].insert_one({'model_id': model.objectID, 'super': 'wfa', 'columns': wfa.oos_data.columns.to_list()})
    store_dataframe(wfa.oos_data,'data',super='wfa', model_id=model.objectID)
    

    # 2.5) Almacenamos las posiciones y ordenes
    DB.db['positions'].insert_one({'model_id': model.objectID, 'super': 'wfa', 'positions':[x for y in wfa.oos_positions for x in y]})
    DB.db['orders'].insert_one({'model_id': model.objectID, 'super': 'wfa', 'orders': [x for y in wfa.oos_orders for x in y]})

    # 3) Almacenamos el objeto de resultados diarios
    document = {'model_id': model.objectID,
                'data': wfa.unified_oos.dailyresult.data.to_json(),
                'super': 'wfa',
                'marketdays': max(wfa.data.Market_Day)
    }

    DB.db['dailyresult'].insert_one(document)
    dailyresult_id = DB.db['dailyresult'].find_one(document)['_id']
    
    # 4) Objeto Result
    document = {
        'model_id': model.objectID,
        'super': 'wfa',
        'dailyresult_id': dailyresult_id
    }
    DB.db['result'].insert_one(document)
    unified_oos_id = DB.db['result'].find_one(document)['_id']
    store_dataframe(wfa.unified_oos.data,'result',super='wfa',model_id=model.objectID)
       
    # 5) Atributos identificativos
    document = {'model_id':model.objectID,
                'unified_oos_id': unified_oos_id,
    }
    # 6) Atributos requeridos
    #document.update(dict((str(attb),wfa.__dict__[str(attb)]) for attb in REQUIRED_ATTRIBUTES))
    document.update(
                    {str(attb): wfa.__dict__[str(attb)] for attb in REQUIRED_ATTRIBUTES}
    )
    
    # 7) Dataframe de la optimizacion
    document.update({
        'optimization_matrix': wfa.optimization_matrix.to_json(),
        'oos_settings': wfa.oos_settings.to_json(),
        'oos_results_periods':  wfa.oos_results_periods,
        'periods': wfa.periods,
        'oos_results_periods': wfa.oos_results_periods
    })
    
    DB.db['wfa'].insert_one(document)
    
    if DB.db['wfa'].find_one(document) is None:
        return {'result': 'Error'} 
    
    return {'result': 'Success'}
    

@app.get('/get_wfa_graph/')
async def get_wfa_graph(model: Model, param: dict, selection: dict, periods: dict) -> dict:
    # Primero verificamos que hay alguna seleccion no False
    if sum(list(selection.values()))==0:
        return {"result": 
            {
                "attributegroup": {},
                "dailybalances": {},
                "dailyresulthistogram": {},
                "hourlyinformation": {},
                "dailysummary": {}
            }
        }
    

    #Instanciamos el objeto result
    result = get_result_object(model,'wfa')

    _attributegroup, _dailybalances, _dailyresulthistogram, _hourlyinformation, _dailysummary = {}, {}, {}, {}, {}    
    
    if selection['attributegroup']:
        _attributegroup =  result.get_attributegroup_option(param['attributegroup'])
        #Modificamos el eje de los % para que vaya de 0 a 100
        _attributegroup['yAxis'][1]['max'] = 100
        
        #Añadimos las lineas verticales de las separaciones de los OOS
        for i in range(len(periods['oos_results_periods'])-1):
            _attributegroup['series'].append(
                {
                    "name": f'oos_{i}',
                    "type": 'line',
                    "data": [[periods['oos_results_periods'][i],0],[periods['oos_results_periods'][i],100]],   
                    "smooth": True,
                    "yAxisIndex": 1,    
                    "xAxisIndex": 0,    
                    "lineStyle": {
                        "color": "green",
                        "width": 2,
                        "type": "dashed"                        
                    },
                    "markPoint": {
                        "data": [
                            {
                                "name": f'00S{i}', 
                                "value": f'00S {i+1}',
                                "xAxis": periods['oos_results_periods'][i],
                                "symbolSize": 65,
                                "yAxis": 100,
                                "label": {
                                    "color": "white"
                                },
                                "itemStyle": {
                                    "color": "green"
                                }
                            }
                        ]                    
                    }            
                }            
            )

        
        
    if selection['dailybalances']:
        #result.get_all_result_attributes()  
        _dailybalances =  result.dailyresult.get_dailybalances_option(param['dailybalances'])
        
    if selection['dailyresulthistogram']:
        _dailyresulthistogram = result.dailyresult.get_dailyresulthistogram_option(data=np.array(result.dailyresult.data.Balance_Percentage.tolist()),
                                                                    _min=math.floor(result.dailyresult.data.Balance_Percentage.min()),
                                                                    _max=math.ceil(result.dailyresult.data.Balance_Percentage.max()),
                                                                    param= param['dailyresulthistogram']
        )
        
    if selection['hourlyinformation']:
        _hourlyinformation = result.get_hourlyinformation_option(param['hourlyinformation'])
          
    if selection['dailysummary']:
        pass
    
    return {"result": 
        {
            "attributegroup": _attributegroup,
            "dailybalances": _dailybalances,
            "dailyresulthistogram": _dailyresulthistogram,
            "hourlyinformation": _hourlyinformation,
            "dailysummary": _dailysummary
        }
    }  
        
@app.get('/get_wfa_dailysummary_piechart/')
async def get_wfa_dailysummary_piechart(model: Model) -> dict:
    #Instanciamos el objeto result unificado
    result = get_result_object(model,'wfa')
    return {"result": {
                'option_pie': result.dailyresult.get_pie_echart(),
                'dataframe': result.dailyresult.get_summaryDataFrame('summary')
            }
    }

@app.get('/get_wfa_default_parameters/')
async def get_wfa_default_parameters(model: Model) -> list:
    # Esta funcion devuelve los parámetros que están seleccionados como default en los settings de la estrategia
    strategy_id = DB.db['models'].find_one({'_id': model.objectID})['strategy_id']
    strategy_settings = DB.db['strategies'].find_one({'_id': strategy_id})['settings']
    default = []
    for collection in list(strategy_settings.keys()):
        default.extend(param_object['name'] for param_object in strategy_settings[collection] if 'wfa' in param_object.keys() and param_object['wfa']['active'] and param_object['wfa']['default'])

    return {'result': default}


@app.get('/get_wfa_available_parameters/')
async def get_wfa_available_parameters(model: Model) -> dict:
    strategy_id = DB.db['models'].find_one({'_id': model.objectID})['strategy_id']
    strategy_settings = DB.db['strategies'].find_one({'_id': strategy_id})['settings']
    available_parameters = {}
    for collection in list(strategy_settings.keys()):
        for param_object in strategy_settings[collection]:
            if 'wfa' in param_object.keys() and param_object['wfa']['active']:
                available_parameters[param_object['name']] = param_object['value']

    return {'result': available_parameters}