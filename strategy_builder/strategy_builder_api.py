from bson import ObjectId
import sys
from fastapi import File, UploadFile, Request
import gridfs
sys.path.append("..")

from main import app,DB
from models.models import LoginUser, StrategyBuilder, UserId, Strategy, Favorites

@app.get('/get_available_strategies_name/')
async def get_available_strategies_name(login: LoginUser) -> dict:
    doc=DB.db['strategies'].find({'owner_name': login.username})
    strategies_name = [st['name'] for st in doc]
    return {'result': []} if strategies_name is None else {"result": strategies_name}


@app.post('/create_strategy/')
async def create_strategy(strategy: StrategyBuilder) -> dict:
    strategy_id = DB.db['strategies'].insert_one(strategy.dict()).inserted_id
    return {'result': str(strategy_id)}

@app.post('/sincronize_favorites/')
async def sincronize_favorites(user: UserId, favorites: Favorites) -> dict:
    # Obtenemos los id de las estrategias favoritas
    favorites_id = []
    for fav in favorites.favorites:
        strategy_id = DB.db['strategies'].find_one({'name': fav})['_id']
        favorites_id.append(strategy_id)

    DB.db['users'].update_one({'_id': user.objectID},{"$set": {"favorites": favorites_id}})
    return {"result": "Success"}

@app.post("/add_strategy_to_favorites/")
async def add_strategy_to_favorites(user: UserId, strategy: Strategy) -> dict:
    strategy_id = DB.db['strategies'].find_one({'name': strategy.name})['_id']
    favorites_id = DB.db['users'].find_one({"_id": user.objectID})['favorites']
    favorites_id.append(strategy_id)
    DB.db['users'].update_one({'_id': user.objectID},{"$set": {"favorites": favorites_id}})
    return {"result": "Success"}

@app.get("/get_all_available_strategies/")
async def get_all_available_strategies(user: LoginUser) -> dict:
    # Buscamos todos los registros de la collection strategies
    all_strategies = list(DB.db['strategies'].find({}, {'_id': 0}))
    all_strategies_name = [strategy['name'] for strategy in all_strategies if strategy['public'] or strategy['owner_name'] == user.username]
    return {"result": all_strategies_name}


@app.post('/remove_strategy_from_favorites/')
async def remove_strategy_from_favorites(user: UserId, strategy: Strategy) -> dict:
    strategy_id = DB.db['strategies'].find_one({'name': strategy.name})['_id']
    favorites_id = DB.db['users'].find_one({"_id": user.objectID})['favorites']
    favorites_id.remove(strategy_id)
    DB.db['users'].update_one({'_id': user.objectID},{"$set": {"favorites": favorites_id}})
    return {"result": "Success"}
    

@app.post('/create_strategy_doc/')
async def create_strategy_doc(request: Request, file: UploadFile = File(...) ) -> dict:
    strategy_id = request.query_params.get('strategy_id')
    if strategy_id is None:
        return {"error": "Strategy ID is required."}
    
    filename = file.filename
    contents = await file.read()

    # Guardado del archivo en la base de datos de MongoDB
    if len(contents) < 16777216: # 16MB en bytes
        DB.db['strategies_doc'].insert_one({'strategy_id': strategy_id,'filename': filename, 'file_content': contents})
    else:
        fs = gridfs.GridFS(DB.db['strategies_doc'])
        fs.put(contents, filename=filename)

        # Guarda la información adicional y el archivo PDF en MongoDB utilizando GridFS
        with fs.new_file(filename=filename, strategy_id=strategy_id) as fp:
            fp.write(contents)
            fp.close()

    return {"result": "Success"}