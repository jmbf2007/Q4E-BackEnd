import math
import numpy as np
import sys
sys.path.append("..")

from main import app,DB



from models.models import Model
from functions.functions_api import get_document_info, get_filtered_object

@app.get('/get_filter_setting/')
async def get_filter_setting(model: Model):
    return {"result": get_document_info(model_id=model.objectID, collection="filter")}
    

@app.get('/get_filtered_graph/')
async def get_filtered_graph(model: Model, param: dict, filterdata: dict, selection: dict) -> dict:
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

    #Instanciamos el objeto filter ya filtrado
    _filter = get_filtered_object(model,filterdata)

    _attributegroup, _dailybalances, _dailyresulthistogram, _hourlyinformation, _dailysummary = {}, {}, {}, {}, {}    

    if selection['attributegroup']:
        _attributegroup =  _filter.result.get_attributegroup_option(param['attributegroup'])

    elif selection['dailybalances']:
        _filter.result.get_all_result_attributes()
        _dailybalances =  _filter.result.dailyresult.get_dailybalances_option(param['dailybalances'])

    elif selection['dailyresulthistogram']:
        _dailyresulthistogram =  _filter.result.dailyresult.get_dailyresulthistogram_option(data=np.array(_filter.result.dailyresult.data.Balance_Percentage.tolist()),
                                                                    _min=math.floor(_filter.result.dailyresult.data.Balance_Percentage.min()),
                                                                    _max=math.ceil(_filter.result.dailyresult.data.Balance_Percentage.max()),
                                                                    param= param['dailyresulthistogram']
        )

    elif selection['hourlyinformation']:
        _hourlyinformation = _filter.result.get_hourlyinformation_option(param['hourlyinformation'])

    return (
        {
            "result": {
                "attributegroup": _attributegroup,
                "dailybalances": _dailybalances,
                "dailyresulthistogram": _dailyresulthistogram,
                "hourlyinformation": _hourlyinformation,
                "dailysummary": _dailysummary,
            }
        }
        #if _attributegroup
        #else {"result": 'No data to show'}
    )  
        

@app.get('/get_levelsinformation/')
async def get_levelsinformation(model: Model, filterdata: dict):
    #Instanciamos el objeto filter ya filtrado
    _filter = get_filtered_object(model,filterdata)

    # Cargamos los datos
    rows=[]
    data = [] 

    if 'Session_VWAP' in _filter.filter_setting.levels.levels:
        data.append(_filter.above_below_level_info(level='Session_VWAP'))
        rows.append('Session VWAP')
    if 'PP' in _filter.filter_setting.levels.levels:
        for level in ['PP','S1','S2','S3','R1','R2','R3']:
            data.append(_filter.above_below_level_info(level=level))
            rows.append(f'Pivot Point ({level})')
    if 'LDL'in _filter.filter_setting.levels.levels:
        for level in ['LD_High','LD_Low','LD_Close']:
            data.append(_filter.above_below_level_info(level=level))
            rows.append(f'Last Day Level ({level})')

    return {"result": {'data': data, 'rows': rows}}


@app.get('/get_dailysummary_piechart/')
async def get_dailysummary_piechart(model: Model, filterdata: dict) -> dict:
    #Instanciamos el objeto filter ya filtrado
    _filter = get_filtered_object(model,filterdata)
    return {"result": {
                'option_pie': _filter.result.dailyresult.get_pie_echart(),
                'dataframe': _filter.result.dailyresult.get_summaryDataFrame('summary')
            }
    }


@app.get('/get_strategy_parameters/')
async def get_strategy_parameters(model: Model) -> dict:
    model = DB.db['models'].find_one({'_id': model.objectID})
    strategy_id = model['strategy_id']
    strategy = DB.db['strategies'].find_one({'_id': strategy_id})
    strategy_parameters = [param['name'] for param in strategy['settings']['strategyparameters']]
    return {"result": strategy_parameters}



@app.get('/get_strategy_parameters_information/')
async def get_strategy_parameters_information(model: Model, filterdata: dict, strategy_parameters: dict):
    #Instanciamos el objeto filter ya filtrado
    _filter = get_filtered_object(model,filterdata)
    if strategy_parameters['selected_parameter'] == "Interval by Days":
        option = _filter.result.get_interval_daily_option(num_days=10)
    elif strategy_parameters['selected_parameter'] == "Interval same Session":
        option =  _filter.result.get_parameter_option(parameter='Interval',
                                                     data=_filter.get_data_tc_for_option(parameter='Interval'),
                                                     initial_range=1,
                                                     final_range = 50,
                                                     #datatype='lineal',
                                                     step=2,
                                                     title = 'Interval')
    elif strategy_parameters['selected_parameter'] == "Range Min":
        option = _filter.result.get_parameter_option(parameter='Range', 
                                                     data=_filter.get_data_level_for_option(parameter='Range'), 
                                                     initial_range=_filter.filter_setting.strategyparameters.range_min, 
                                                     final_range=50, 
                                                     #datatype='lineal',
                                                     step=1,
                                                     title='Range Level Candle')
                                                    
    elif strategy_parameters['selected_parameter'] == 'Body/Range Ratio Min':
        option = _filter.result.get_parameter_option(parameter='BR', 
                                                     data=_filter.get_data_level_for_option(parameter='BR'), 
                                                     initial_range=_filter.filter_setting.strategyparameters.br_min, 
                                                     final_range = 100,
                                                     #datatype='percentage',
                                                     step=5,                                                     
                                                     title='Body/Range Level Candle')

    elif strategy_parameters['selected_parameter'] == 'MVC Max':
        option = _filter.result.get_parameter_option(parameter='MVC_Percentage', 
                                                     data=_filter.get_data_level_for_option(parameter='MVC_Percentage'), 
                                                     initial_range=0, 
                                                     final_range=_filter.filter_setting.strategyparameters.mvc_max,  
                                                     #datatype='percentage',
                                                     step=5,
                                                     title='MVC Level Candle')

    elif strategy_parameters['selected_parameter'] == 'MVC TC Min':
        option = _filter.result.get_parameter_option(parameter='MVC_Percentage',
                                                     data=_filter.get_data_tc_for_option(parameter='MVC_Percentage'),
                                                     initial_range=_filter.filter_setting.strategyparameters.mvc_tc_min,
                                                     final_range = 100,
                                                     #datatype='percentage',
                                                     step=5,
                                                     title = 'MVC Touch Candle')
                                                

    elif strategy_parameters['selected_parameter'] == 'Bounce Max':
        option = {}
    elif strategy_parameters['selected_parameter'] == 'Bounce Min':
        option =  {}
    return  {"result": option  }
               
