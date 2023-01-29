import sys
sys.path.append("..")

from main import app, DB

from functions.functions_api import restore_dataframe

from models.models import Model, DataObjectType


@app.get('/get_data_table/')
async def get_data_table(object: DataObjectType, model: Model):
    data = restore_dataframe('data',object.super, model.objectID) 
    return {'result': data.to_json()}


@app.get('/get_positions_table/')
async def get_positions_table(model: Model, object: DataObjectType):
    document = DB.db['positions'].find_one({'model_id': model.objectID, 'super': object.super})
    return {'result': document['positions']}


@app.get('/get_orders_table/')
async def get_orders_table(model: Model, object: DataObjectType):
    document = DB.db['orders'].find_one({'model_id': model.objectID, 'super': object.super})
    return {'result': document['orders']}


@app.get('/get_data_columns/')
async def get_data_columns(object: DataObjectType, model: Model):
    document = DB.db['data'].find_one({'model_id': model.objectID, 'super': object.super})
    return {'result': document['columns']}


