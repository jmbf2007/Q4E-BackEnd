
import simplejson as json
import sys
sys.path.append("..")

from main import app,DB


from functions.functions_api import restore_dataframe
from models.models import Model, DataObjectType
from lib.ClassCandlestickECharts import CandelstickEChart
from functions.functions_api import get_market_data, get_document_info


@app.get("/exist_object/")
async def exist_object(model: Model, object: DataObjectType)-> dict:
    if DB.db[object.dataobject].find_one({'model_id': model.objectID, 'super': object.super}) is not None:
        return {"result": True}
    return {"result": False}

@app.get("/get_candlestickechart_option/")
async def get_candlestickechart_option(object: DataObjectType, model: Model, show: dict,tooltip: dict) -> dict:
    data = restore_dataframe('data',object.super, model.objectID)
    result = restore_dataframe('result',object.super, model.objectID)
    positions = DB.db['positions'].find_one({'model_id': model.objectID, 'super': object.super})['positions']
    levels = DB.db['levels'].find_one({'model_id': model.objectID, 'super': object.super})['levels']
    orders = DB.db['orders'].find_one({'model_id': model.objectID, 'super': object.super})['orders']
    tc = DB.db['tc'].find_one({'model_id': model.objectID, 'super': object.super})['tc']
    if show['impulses']:
        impulses = DB.db['impulses'].find_one({'model_id': model.objectID, 'super': object.super})['impulses']
    echart = CandelstickEChart(data=data,result=result, show=show, tooltip=tooltip, positions=positions, levels=levels, orders= orders, tc=tc, impulses=impulses if show['impulses'] else None)
    
    return {'result': echart.getOption()}

@app.get("/available_dp/")
async def available_dp(model: Model) -> dict:
    strategy_id= DB.db['models'].find_one({'_id': model.objectID})['strategy_id']
    strategy_info = DB.db['strategies'].find_one({'_id': strategy_id})
    if strategy_info['settings']['levels'][0]['default'] == 'DP':
        return {'result': True}
    return {'result': False}

@app.get("/get_impulses/")
async def get_impulses(model: Model, object: DataObjectType) -> dict:
    impulses = DB.db['impulses'].find_one({'model_id': model.objectID, 'super': object.super})['impulses']
    return {'result': impulses}

# --- Metodos que construyen el option de ECharts desde el frontend ---

@app.get("/get_datacandle/")
async def get_datacandle(model: Model, object: DataObjectType) -> dict:
    data = restore_dataframe('data', object.super, model.objectID)
    
    # Convertir objetos Timestamp a cadenas
    for col in data.select_dtypes(include=['datetime64', 'timedelta64']):
        data[col] = data[col].astype(str)
    
    # Convertir el DataFrame a una cadena JSON y luego a un dict
    json_str = data.to_json(orient='records', date_format='iso')
    return {'result': json.loads(json_str)}

@app.get("/get_ask_bid_profile/")
async def get_ask_bid_profile(model: Model) -> dict:
    """
    Funcion que devuelve los perfiles ask y bid de cada vela
    """
    # Recuperamos el setting del modelo
    setting = get_document_info(model.objectID, 'setting')
    # Recuperamos al fecha de inicio y fin del modelo
    start_date = setting['instrument']['start_date']
    end_date = setting['instrument']['end_date']
    tf = setting['instrument']['tf']
    ticker = setting['instrument']['ticker']
    data = get_market_data(ticker, tf, start_date, end_date, of_active=True)
    # Nos quedamos con las columnas Time,Ask y Bid
    data = data[['Time','Ask','Bid']]

    # Convertir el DataFrame a una cadena JSON y luego a un dict
    json_str = data.to_json(orient='records', date_format='iso')
    return {'result': json.loads(json_str)}

@app.get("/get_result_dataframe/")
async def get_result_dataframe(model: Model, object: DataObjectType) -> dict:
    """
    Funcion que devuelve el dataframe de resultados
    """
    data = restore_dataframe('result',object.super, model.objectID)
    # Convertir objetos Timestamp a cadenas
    for col in data.select_dtypes(include=['datetime64', 'timedelta64']):
        data[col] = data[col].astype(str)
    
    # Convertir el DataFrame a una cadena JSON y luego a un dict
    json_str = data.to_json(orient='records', date_format='iso')
    return {'result': json.loads(json_str)}

@app.get("/get_levels_list/")
async def get_levels_list(object: DataObjectType, model: Model) -> dict:
    levels = DB.db['levels'].find_one({'model_id': model.objectID, 'super': object.super})['levels']
    return {'result': levels}

@app.get("/get_touch_candle_list/")
async def get_touch_candle_list(model: Model, object: DataObjectType) -> dict:
    tc = DB.db['tc'].find_one({'model_id': model.objectID, 'super': object.super})['tc']
    return {'result': tc}

@app.get("/get_positions_list/")
async def get_positions_list(model: Model, object: DataObjectType) -> dict:
    positions = DB.db['positions'].find_one({'model_id': model.objectID, 'super': object.super})['positions']
    return {'result': positions}

@app.get("/get_orders_list/")
async def get_orders_list(model: Model, object: DataObjectType) -> dict:
    orders = DB.db['orders'].find_one({'model_id': model.objectID, 'super': object.super})['orders']
    return {'result': orders}

@app.get("/get_impulses_list/")
async def get_impulses_list(model: Model, object: DataObjectType) -> dict:
    impulses = DB.db['impulses'].find_one({'model_id': model.objectID, 'super': object.super})['impulses']
    return {'result': impulses}

#----------------------------------------------------


















