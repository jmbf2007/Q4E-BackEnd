import sys
sys.path.append("..")
from main import app, DB

from models.models import Model, Strategy
from models.modelsSetting import Setting, StrategyParameters, TradeManagement
from lib.ClassData import cDataCandle
from lib.ClassCase import cCase
from lib.ClassPosition import Position
from functions.functions_api import get_document_info, get_market_data, store_dataframe

# Método GET para obtener los valores del setting
@app.get("/get_settings/")
async def get_settings(model: Model)-> dict:
    return {"result": get_document_info(model.objectID, 'setting')}


# Método GET para obtener los valores por defecto de la estrategia
@app.get("/get_default_settings/")
async def get_default_settings(strategy: Strategy) -> dict:
    strategyInfo = DB.db['strategies'].find_one({'name':strategy.name})
    return {'result': strategyInfo['settings']}


# Metodo POST crear los documentos del setting
@app.post("/create_settings/")
async def create_settings(model: Model, data: dict) -> dict:
    data['model_id'] = model.objectID
    DB.db['setting'].insert_one(data)
    return {"result": "Success"}

# Método PUT para actualizar de los documentos del setting
@app.delete("/delete_settings/")
async def delete_settings(model: Model)-> dict:
    DB.db['setting'].delete_one({'model_id': model.objectID}) 
    return {"result": "Success"}

@app.post("/save_settings/")
async def save_settings(model: Model, data: dict)-> dict:
    doc = DB.db['settings'].find_one({'model_id': model.objectID})
    if doc is None:
        data['model_id'] = model.objectID
        DB.db['setting'].insert_one(data)
    else: 
        DB.db['setting'].update_one({'model_id': model.objectID},{"$set": data})         
        
    return {"result": "Success"}

@app.post("/model_data_calculation")
async def model_data_calculation(model: Model)-> dict:
    #Creamos el objeto setting   
    setting = Setting(data = get_document_info(model.objectID, 'setting'))

    #Creamos el objeto data y calculamos los datos del modelo
    data = cDataCandle(get_market_data(setting.instrument.ticker, setting.instrument.tf, setting.instrument.start_date, setting.instrument.end_date),
                       setting.to_dict())
    data.Calculate_Model()

    # Datos de m1
    m1data = get_market_data(setting.instrument.ticker, 1, setting.instrument.start_date, setting.instrument.end_date)[['Time','High','Low','Close']]
    
    # Creamos el objeto case
    strategy_id = DB.db['models'].find_one({'_id': model.objectID})['strategy_id']
    strategy_info = DB.db['strategies'].find_one({'_id': strategy_id})
    case = cCase(data=data.data, 
                 setting=setting.to_dict(), 
                 m1data = m1data, 
                 tc_assumptions= strategy_info['tc_assumptions'],
                 strategy_settings= strategy_info['settings'],
                 strategy_type = strategy_info['strategy_type'] ) 
    
    # Creamos el loop para chequear todas las velas 
    # Vamos a dividir los dias de mercado por el numero de cpu que tiene el procesador
    """
    period_days = int(len(set(case.data.Market_Day))/cpu_count())
    initial_days = [1+period_days*x for x in range(cpu_count()-1)]+[period_days*(cpu_count()-1)]
    final_days = [period_days*(x+1) for x in range(cpu_count()-1)]+[len(set(case.data.Market_Day))]

    # Corutinas
    tasks = [case.check_period_market_days(initial_day=ini, final_day=fin) for ini,fin in zip(initial_days,final_days)]
    await asyncio.gather(*tasks)
    """
    
    for day in set(case.data.Market_Day):
        case.check_session(day)
        
    # Creamos el objeto result y filter
    _data = []
    for pos in case.positions:
        position = Position()
        position.from_dict(pos)
        _data.append(position.data_to_result())
    
    case.get_result()
    
    
    #TODO ver la posibilidad de actulizar los registros en lugar de borrarlos y guardarlos de nuevo
    # Si no es la primera version del modelo, primero eliminamos los documentos anteriores y se vuelven a almacenar
    if model.version>0:        
        DB.db['data'].delete_one({'model_id': model.objectID, 'super': 'case'})
        DB.db['data_chunks'].delete_many({'model_id': model.objectID, 'super': 'case'})
        DB.db['positions'].delete_one({'model_id': model.objectID, 'super':'case'})
        DB.db['orders'].delete_one({'model_id': model.objectID, 'super':'case'})
        DB.db['levels'].delete_one({'model_id': model.objectID, 'super': 'case'})
        DB.db['result'].delete_one({'model_id': model.objectID, 'super': 'case'})
        DB.db['result_chunks'].delete_many({'model_id': model.objectID, 'super': 'case'})
        DB.db['dailyresult'].delete_one({'model_id': model.objectID, 'super': 'case'})
        DB.db['filter'].delete_one({'model_id': model.objectID})
        if hasattr(case.strategy_logic,'tc'):
            DB.db['tc'].delete_one({'model_id': model.objectID, 'super': 'case'})
        if hasattr(case.strategy_logic,'rc'):
            DB.db['rc'].delete_one({'model_id': model.objectID, 'super': 'case'})
        if hasattr(case,'impulses'):
            DB.db['impulses'].delete_one({'model_id': model.objectID, 'super': 'case'})

        
    # Alamacenamos Objeto DataCandle             
    DB.db['data'].insert_one({'model_id': model.objectID, 'super': 'case', 'columns': case.data.columns.to_list()})
    store_dataframe(case.data,'data',super='case', model_id=model.objectID)
    
    # Almacenamos las posiciones 
    DB.db['positions'].insert_one({'model_id': model.objectID, 'super': 'case', 'positions': case.positions})
    
    # Almacenamos las ordenes
    DB.db['orders'].insert_one({'model_id': model.objectID, 'super': 'case', 'orders': case.orders})
    
    # Almacenamos las velas de toque si existen 
    if hasattr(case.strategy_logic,'tc'):
        DB.db['tc'].insert_one({'model_id': model.objectID, 'super': 'case', 'tc': case.strategy_logic.tc})
    
    # Almacenamos los impulsos si existen
    if hasattr(case,'impulses'):
        DB.db['impulses'].insert_one({'model_id': model.objectID, 'super': 'case', 'impulses': case.impulses})
    
    # Almacenamos los niveles
    DB.db['levels'].insert_one({'model_id': model.objectID, 'super': 'case', 'levels': case.levels_to_list()})
    
    
    # Almacenamos el objeto de resultados diarios
    document = {'model_id': model.objectID,
                'data': case.filter.result.dailyresult.data.to_json(),
                'super': 'case',
                'marketdays': max(case.data.Market_Day)
    }

    DB.db['dailyresult'].insert_one(document)
    dailyresult_id = DB.db['dailyresult'].find_one(document)['_id']
    
    #Objeto Result
    document = {
        'model_id': model.objectID,
        'super': 'case',
        'dailyresult_id': dailyresult_id
    }
    DB.db['result'].insert_one(document)
    store_dataframe(case.filter.result.data,'result',super='case',model_id=model.objectID)
    
    #Objeto Filter
    filter_data = case.filter.filter_setting.to_dict()
    filter_data.update({'model_id': model.objectID})
    DB.db['filter'].insert_one(filter_data)

    
    #Actualizamos la version del analisis
    DB.db['models'].update_one({'_id':model.objectID},{"$set":{'version': model.version+1}})           
    
    #Borramos las instancias de objetos creados
    del case
    del data
    del setting
    
    return {"result": "Success"}


    
    
    
    