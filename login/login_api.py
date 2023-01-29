import sys
sys.path.append("..")

from main import app,DB

from models.models import LoginUser

#---- Funciones de la API para Login
@app.post("/check_login/")
async def check_login(login_data: LoginUser) -> dict:

    user = DB.db["users"].find_one({"name": login_data.username})        # Buscamos el documento de la colleccion users con nombre el username pasado
        
    if user is not None and user['password'] == login_data.password:     # Si existe comprobamos el password
        return {"result": True}
    
    return {"result": False}
    
@app.get("/get_user_id/")
def get_user_id(login: LoginUser) -> dict:
    return {"result": str(DB.db['users'].find_one({'name': login.username})['_id'])}