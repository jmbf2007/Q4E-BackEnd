from bson import ObjectId
import sys
sys.path.append("..")

from main import app,DB
from models.models import LoginUser, StrategyBuilder, UserId, Strategy

@app.get('/get_available_strategies_name/')
async def get_available_strategies_name(login: LoginUser) -> dict:
    doc=DB.db['strategies'].find({'owner_name': login.username})
    strategies_name = [st['name'] for st in doc]
    return {'result': []} if strategies_name is None else {"result": strategies_name}


@app.post('/create_strategy/')
async def create_strategy(strategy: StrategyBuilder) -> dict:
    strategy_id = DB.db['strategies'].insert_one(strategy.dict()).inserted_id
    return {'result': str(strategy_id)}

@app.post("/add_strategy_to_favorites/")
async def add_strategy_to_favorites(user: UserId, strategy: Strategy) -> dict:
    strategy_id = DB.db['strategies'].find_one({'name': strategy.name})['_id']
    favorites_id = DB.db['users'].find_one({"_id": user.objectID})['favorites']
    favorites_id.append(strategy_id)
    DB.db['users'].update_one({'_id': user.objectID},{"$set": {"favorites": favorites_id}})
    return {"result": "Success"}

@app.get("/get_all_available_strategies/")
async def get_all_available_strategies(user: UserId) -> list:
    all_strategies = DB.db['strategies'].find({})
    all_strategies_name = [strategy['name'] for strategy in all_strategies  if strategy['public'] or strategy['owner_name'] == user.username]   
    return {"result": all_strategies_name}

@app.post('/remove_strategy_from_favorites/')
async def remove_strategy_from_favorites(user: UserId, strategy: Strategy) -> dict:
    strategy_id = DB.db['strategies'].find_one({'name': strategy.name})['_id']
    favorites_id = DB.db['users'].find_one({"_id": user.objectID})['favorites']
    favorites_id.remove(strategy_id)
    DB.db['users'].update_one({'_id': user.objectID},{"$set": {"favorites": favorites_id}})
    return {"result": "Success"}
    
