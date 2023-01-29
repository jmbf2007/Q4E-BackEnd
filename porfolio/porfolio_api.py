from bson import ObjectId
import sys
sys.path.append("..")

from main import app,DB
from models.models import LoginUser, UserId, Porfolio
from lib.ClassPorfolio import cPorfolio


@app.get('/get_available_strategies_info/')
async def get_available_strategies_info(login: LoginUser, user: UserId,) -> dict:
    doc=DB.db['users'].find_one({'name': login.username})    
    strategies = []
    for st_id in doc['favorites']:
        models = list(DB.db['models'].find({"user_id": user.objectID,"strategy_id": st_id}))
        strategy_name = DB.db['strategies'].find_one({'_id':st_id})['name']
        strategy_models = [{"name": model['name'], "summary": model['summary'], "_id": str(model['_id'])} for model in models]
        strategies.append({'name': strategy_name,
                           '_id': str(st_id),
                           'models': strategy_models
                        })
    
    return {"result": strategies}

@app.post('/create_new_porfolio/')
async def create_new_porfolio(login: LoginUser, data: Porfolio) -> dict:
    models_info = [{'strategy': {'name': st_name, 'id': st_id}, 'model': {'name': mdl_name, 'id': model_id}} for st_name, st_id, mdl_name, model_id in zip(data.strategies_name, data.strategies_id, data.models_name, data.models_id)]

    doc = {
        'username': login.username,
        'name': data.name,
        'description': data.description,
        'account': data.account,
        'models': models_info,
        'initial_balance': data.initial_balance
    }

    #Comprobamos si existe otro porfolio con ese nombre
    porf = DB.db['porfolio'].find_one({'username': login.username, 'name': data.name})
    if porf is not None:
        return {'result': 'Error'}

    DB.db['porfolio'].insert_one(doc)

    return {'result': 'Success'}

@app.get('/get_porfolio_list/')
async def get_porfolio_list(login: LoginUser) -> dict:
    doc = DB.db['porfolio'].find({'username': login.username})
    porfolio = []
    for porf in doc:
        porf['id'] = str(porf['_id'])
        porf.pop('_id')
        porf.pop('username')
        porfolio.append(porf)

    return {'result': porfolio}


@app.delete('/delete_porfolio/')
async def delete_porfolio(data: Porfolio) -> dict:
    doc=DB.db['porfolio'].find_one({"username": data.username, "name": data.name})
    if doc is not None:
        DB.db['porfolio'].delete_one({'_id': doc['_id']})
        return {'result': 'Success'}
    return {'result': 'Error'}

@app.put('/update_porfolio/')
async def update_porfolio(data: Porfolio):
    models_info = [{'strategy': {'name': st_name, 'id': st_id}, 'model': {'name': mdl_name, 'id': model_id}} for st_name, st_id, mdl_name, model_id in zip(data.strategies_name, data.strategies_id, data.models_name, data.models_id)]
    doc = {
        'username': data.username,
        'name': data.name,
        'description': data.description,
        'account': data.account,
        'models': models_info,
        'initial_balance': data.initial_balance
    } 
    porfolio_id = DB.db['porfolio'].find_one({'username': data.username, 'name': data.name})['_id']
    DB.db['porfolio'].update_one({'_id': porfolio_id},{"$set": doc}) 
    return {"result": "Success"}


@app.get('/get_porfolio_object/')
async def get_porfolio_object(data: Porfolio):
    doc = DB.db['porfolio'].find_one({'username': data.username, 'name': data.name})
    models = [model['model'] for model in doc['models']]
    positions = []
    for mdl in models:
        document = DB.db['positions'].find_one({'model_id': ObjectId(mdl['id'])})
        simplified_positions = []
        simplified_positions.extend({'close_time': position['close_time'], 'cash_result': position['cash_result']} for position in document['positions'])
        positions.append({'model_name': mdl['name'], 'positions': simplified_positions})
    porfolio = cPorfolio(models_positions = positions, account_type = doc['account'], initial_balance = doc['initial_balance'])

    if data.required_object == "dataframe":
        return {'result': porfolio.get_dataframe()}
    elif data.required_object == "graph":
        return {'result': porfolio.get_graph_option(data.required_attb)}
    else:
        return {'result': 'Error'}


