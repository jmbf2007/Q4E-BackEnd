
import sys
sys.path.append("..")

from main import app,DB


from functions.functions_api import restore_dataframe
from models.models import Model, DataObjectType
from lib.ClassCandlestickECharts import CandelstickEChart


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
    if show['impulses']:
        impulses = DB.db['impulses'].find_one({'model_id': model.objectID, 'super': object.super})['impulses']
    echart = CandelstickEChart(data=data,result=result, show=show, tooltip=tooltip, positions=positions, levels=levels, orders= orders, impulses=impulses if show['impulses'] else None)
    
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