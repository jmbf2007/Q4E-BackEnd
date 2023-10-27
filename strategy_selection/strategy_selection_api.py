import sys
sys.path.append("..")

from main import app, DB


from models.models import LoginUser, Strategy, UserId, Model


MODEL_COLLECTIONS=['setting','data','data_chunks','case','result','result_chunks','dailyresult','filter','param','parametricinfo','wfa','levels','positions','orders','tc','impulses']


@app.get("/get_user_strategies/")
async def get_user_strategies(login: LoginUser) -> dict:
    doc=DB.db['users'].find_one({'name': login.username})    
    strategies_id = [str(std_id) for std_id in doc['favorites']]     
    return {"result": {'strategies': strategies_id}}

@app.get("/get_all_public_strategies/")
async def get_all_public_strategies() -> dict:
    strategies = DB.db['strategies'].find({"public": True})
    strategies_id = [str(std["_id"]) for std in strategies]
    return {"result": {'strategies': strategies_id}}

@app.get("/get_strategy/")
async def get_strategy(strategy: Strategy) -> dict:
    doc=DB.db['strategies'].find_one({'_id': strategy.objectID})
    return {"result": {"name": doc["name"], "description": doc["description"], "type": doc["strategy_type"],} if doc is not None else {"name": None, "description": None, "type": None}}

@app.get("/get_strategy_id/")
async def get_strategy_id(strategy: Strategy) -> dict:
    strategyInfo = DB.db['strategies'].find_one({'name':strategy.name})
    return {"result": str(strategyInfo['_id'])}

@app.get("/get_models/")
async def get_models(user: UserId, strategy: Strategy, model: Model) -> dict:
    if model.name is None:
        models = list(DB.db['models'].find({"user_id": user.objectID,"strategy_id": strategy.objectID}))
    else: 
        models = list(DB.db['models'].find({"user_id": user.objectID,"strategy_id": strategy.objectID, "name": model.name}))
    list_models = [{"_id": str(mdl["_id"]), "name": mdl["name"], "summary": mdl["summary"], "version": mdl["version"]} for mdl in models]

    return {"result": list_models }

@app.delete("/delete_model/")
async def delete_model(user: UserId, strategy: Strategy, model: Model) -> dict:
    # Primero leemos el modelo a eliminar
    selected_model = DB.db['models'].find_one({"user_id": user.objectID,"strategy_id": strategy.objectID, "name": model.name})

    for col in MODEL_COLLECTIONS:            
        DB.db[col].delete_many({'model_id': selected_model['_id']})

    # Borramos el documento de la collecion models
    DB.db['models'].delete_one({'_id': selected_model['_id']})
    
    return {"result": "Removed Model"}

@app.post("/create_model/")
async def create_model(user: UserId, strategy: Strategy, model: Model)->dict:
    selected_model = DB.db['models'].find_one({"user_id": user.objectID,"strategy_id": strategy.objectID, "name": model.name})
    if selected_model is None:
        new_model = {'name': model.name,
                    'user_id': user.objectID,
                    'strategy_id': strategy.objectID,
                    'summary': model.summary,
                    'version': 0
                }

        DB.db['models'].insert_one(new_model)
        return {"result": "Success"}
    return {"result": "Error"}

@app.put("/update_model/")
async def update_model(model:Model, data: dict) -> dict:
    DB.db['models'].update_one({'_id': model.objectID},{"$set": data}) 
    return {"result": "Success"}
    

@app.post("/remove_strategy_from_favorites/")
async def remove_strategy_from_favorites(user: UserId, strategy: Strategy) -> dict:
    strategy_id = DB.db['strategies'].find_one({'name': strategy.name})['_id']
    DB.db['users'].update_one({'_id': user.objectID},{"$pull": {"favorites": strategy_id}})
    return {"result": "Success"}

@app.get("/get_user_favorites_name/")
async def get_user_favorites_name(user: UserId) -> dict:
    # sourcery skip: for-append-to-extend, list-comprehension
    favorites_id = DB.db['users'].find_one({"_id": user.objectID})['favorites']
    favorites_name = []
    for fav_id in favorites_id:
        favorites_name.append(DB.db['strategies'].find_one({'_id': fav_id})['name'])

    return {"result": favorites_name}


