import sys
sys.path.append("..")


from main import app,DB

from models.models import Model, Strategy
from functions.functions_api import get_document_info, get_market_data, get_parameter_behavior
from models.modelsSetting import Setting
from lib.ClassData import cDataCandle
from lib.ClassCase import cCase
from lib.ClassParametricAnalysis import cParametric
from bson import ObjectId




ATTRIBUTES={'Total Trades':'total',
        'Total Win Trades':'win',
        'Total Loss Trades':'loss',
        'Total Doubt Trades':'doubt',
        'Total Breakeven Trades':'beven',
        'Partial Win Trades':'pwin',
        'Partial Loss Trades':'ploss',
        'Balance PnL Ticks':'tick_balance',
        'Average PnL Ticks':'avrg_ticks',
        'Cash Balance':'cash_balance',
        'Average Cash Balance':'avrg_cash',
        'Cash Drawdown %':'cash_drawdown',
        'Max Cash Drawdown %':'cash_drawdown_max',
        'Total Win Ticks':'win_ticks',
        'Total Loss Ticks':'loss_ticks',
        'Average Win Ticks':'avrg_win_ticks',
        'Average Loss Ticks':'avrg_loss_ticks',
        'Best Trade Ticks':'best',
        'Worst Trade Ticks':'worst',
        'Ratio Win':'rwin',
        'Profit Factor':'profit_factor',
        'Recovery Factor':'recovery_factor',
        'Return of Investement(ROI)':'roi',
}

#---- Funciones para la API de Parametric Analysis
@app.get('/get_parametric_analysis_info/')
async def get_parametric_analysis_info(model: Model)-> dict:
    document = DB.db['param'].find_one({'model_id': model.objectID, 'name': model.name})
    if document is not None:
        del document["_id"]
        del document["model_id"]
    return {"result": document}

@app.get('/get_available_parametric_analysis/')
async def get_available_parametric_analysis(model: Model)-> dict:
    documents = DB.db['param'].find({'model_id': model.objectID})
    available_pa = [{
            'name': doc['name'],
            'description': doc['description'],
            'param1_name': doc['param1_name'],
            'param1_values': doc['param1_values'],
            'param2_name': doc['param2_name'],
            'param2_values': doc['param2_values']
        } for doc in list(documents)]
    return {'result': available_pa}
          
@app.delete('/delete_parametric_analysis/')
async def delete_parametric_analysis(model: Model) -> dict:
    DB.db['param'].delete_one({'model_id': model.objectID, 'name': model.name})    
    return {"result": "Success"}    

@app.post('/run_parametric_analysis/')
async def run_parametric_analysis(model: Model, param: dict) -> dict:
    # Leemos el objeto setting
    setting = Setting(data = get_document_info(model.objectID, 'setting'))

    # Leemos los datos de mercado
    data_df = get_market_data(setting.instrument.ticker, 
                              setting.instrument.tf, 
                              setting.instrument.start_date, 
                              setting.instrument.end_date)

    data_m1 =  get_market_data(ticker = setting.instrument.ticker,
                               tf = 1,
                               start_date = setting.instrument.start_date, 
                               end_date = setting.instrument.end_date)[['Time','High','Low','Close']]

    # Leemos las hipotesis de la estrategia
    strategy_id = DB.db['models'].find_one({'_id': model.objectID})['strategy_id']
    strategy_info = DB.db['strategies'].find_one({'_id': strategy_id})


    # Creamos el objeto param
    parametric = cParametric(parameters=param)

    behavior1 = get_parameter_behavior(model.objectID, parametric.parameters.param1_name)
    behavior2 = get_parameter_behavior(model.objectID, parametric.parameters.param2_name)

    # Definimos el bucle    
    for _p1,_p1_value in enumerate(parametric.parameters.param1_values):
        for _p2,_p2_value in enumerate(parametric.parameters.param2_values):  
            # Iniciamos el objeto data temporal
            temp_data=cDataCandle(data_df,setting.to_dict())              

            # Asignación del parámetro 1 y 2
            temp_data.setting.__dict__[behavior1[0]].__dict__[behavior1[1]]=_p1_value                                  
            temp_data.setting.__dict__[behavior2[0]].__dict__[behavior2[1]]=_p2_value           

            #Preparacion del modelo
            if (_p1+_p2)==0:
                parametric.initialize_dataframes()

            temp_data.Calculate_Model()

            #Creamos el objeto case 
            temp_case = cCase(
                data=temp_data.data, 
                setting=temp_data.setting.to_dict(), 
                m1data = data_m1, 
                tc_assumptions = strategy_info['tc_assumptions'],
                strategy_settings = strategy_info['settings'],
                strategy_type = strategy_info['strategy_type']
            ) 

            # Resolvemos
            for day in set(temp_case.data.Market_Day):
                temp_case.check_session(day)

            # Creamos el objeto result y filter
            temp_case.get_result()     


            # Almacenamos los resultado en los dataframe                   
            if _p2==0:                                                                                          #Estamos en el primer elemento del bucle sl iniciamos los np array
                for attb in ATTRIBUTES.values():
                    parametric.__dict__['np_'+str(attb)] =[]                        
                    parametric.__dict__['np_'+str(attb)].append(list(temp_case.filter.result.Get_Attribute_Serie(attb).to_list()))
            else:
                for attb in ATTRIBUTES.values():
                    parametric.__dict__['np_'+str(attb)].append(list(temp_case.filter.result.Get_Attribute_Serie(attb).to_list()))

            #Si es el ultimo valor de p2 añadimos la fila al df
            if _p2==len(parametric.parameters.param2_values)-1:
                for attb in ATTRIBUTES.values():
                    parametric.__dict__['df_'+str(attb)][str(_p1_value)] = parametric.__dict__['np_'+str(attb)]   

    # Eliminamos los array np utilizados para el analisis
    for attb in ATTRIBUTES.values():
        del parametric.__dict__['np_'+str(attb)]

    # Almacenamos el resultado
    doc =  {'model_id': model.objectID,
            'name': parametric.parameters.name,
            'description':parametric.parameters.description,
            'param1_name': parametric.parameters.param1_name,
            'param1_values': parametric.parameters.param1_values,
            'param2_name':parametric.parameters.param2_name,
            'param2_values': parametric.parameters.param2_values
    }
    df_result = {}
    df_result.update(dict((('df_'+str(attb)),parametric.__dict__['df_'+str(attb)].to_json()) for attb in list(ATTRIBUTES.values())))

    doc['df_result'] = df_result

    DB.db['param'].insert_one(doc)
    return {"result": 'Success'}


@app.get('/get_parametric_default_parameters/')
async def get_parametric_default_parameters(strategy: Strategy) -> dict:
    try:
        # Esta funcion devuelve los parámetros que están seleccionados como default en los settings de la estrategia
        strategy_settings = DB.db['strategies'].find_one({'_id': strategy.objectID})['settings']
        default = []
        for collection in list(strategy_settings.keys()):
            for param_object in strategy_settings[collection]:                    
                if 'parametric' in list(param_object.keys()):
                    if param_object['parametric']['active']:
                        if 'default' in list(param_object['parametric'].keys()) and param_object['parametric']['default']:
                            default.append(param_object['name'])
            #default.extend(param_object['name'] for param_object in strategy_settings[collection] if 'parametric' in param_object.keys() and param_object['parametric']['active'] and param_object['parametric']['default'])
        return {'result': default}
    except Exception as e:
        return {'result': 'Error'}

@app.get('/get_available_parameters/')
async def get_available_parameters(model: Model) -> dict:
    # Esta funcion devuelve los parámetros que están seleccionados como default en los settings de la estrategia
    strategy_id = DB.db['models'].find_one({'_id': model.objectID})['strategy_id']
    strategy_settings = DB.db['strategies'].find_one({'_id': strategy_id})['settings']
    available = []
    for collection in list(strategy_settings.keys()):
        for param_object in strategy_settings[collection]:           
            if 'parametric' in list(param_object.keys()) and param_object['parametric']['active'] and param_object['hidden']==False:
                available.append(param_object['name'])
    return {'result': available}