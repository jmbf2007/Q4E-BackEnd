
import jwt
import aiosmtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os
import random
import string
from datetime import datetime,timedelta
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from login.login_messages import USER_ALREADY_CREATED, VERIFICATION_FAILED, VERIFICATION_SUCCESSFUL, EXPIRED_TOKEN, INVALID_TOKEN, RECOVERY_PASSWORD_SUCCESSFUL

import sys
sys.path.append("..")

from main import app,DB

from models.models import LoginUser, TokenEmail

#---- Variables de entorno para los correo de verificacion
SECRET_KEY = 'quant4everybody'  
#SERVER_HOST="http://localhost:8000"
SMTP_HOST = "smtp.office365.com"
SMTP_PORT = 587

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

@app.post("/check_user/")
async def check_user(login_data: LoginUser) -> dict:
    # sourcery skip: assign-if-exp, reintroduce-else
    # Buscamos el documento de la colleccion users con nombre el username pasado
    user_name = DB.db["users"].find_one({"name": login_data.username})       

    # Buscamos el documento de la colleccion users con email el email pasado
    user_email = DB.db["users"].find_one({"email": login_data.email}) 
        
    # Si existe el user_name devolvemos el codigo 5
    if user_name is not None:     
        return {"result": 5}
    
    # Si existe el user_email devolvemos el codigo 6
    if user_email is not None:
        return {"result": 6}
    
    # Si no existe devolvemos el codigo 7
    return {"result": 7}

@app.post("/send_verification_email/")
async def send_verification_email(login_data: LoginUser, email_info: TokenEmail) -> None:
    # Leemos el password de la cuenta support@quant4everybody
    load_dotenv("VARIABLES.env")  # Carga las variables de entorno desde .env

    email_password = os.environ.get("EMAIL_PASSWORD")
    SERVER_HOST = os.environ.get("SERVER_HOST")
    if not email_password:
        raise ValueError("No se encontró la contraseña del email en las variables de entorno.")
    
    # Generar token con toda la información del usuario
    payload = {
        'name': login_data.username,
        'password': login_data.password,
        'email': login_data.email,
        'exp': datetime.utcnow() + timedelta(hours=24)  # Token válido por 24 horas
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    # Configurar y enviar email
    message = EmailMessage()
    message["From"] = "support@quant4everybody.com"
    message["To"] = login_data.email
    message["Subject"] = email_info.subject
    link_verificacion = f'{SERVER_HOST}/{email_info.function}?token={token}'
    message.set_content(f'Haz clic en el siguiente enlace para {email_info.content} del usuario {login_data.username}: {link_verificacion}')

    # Inicia sesión y envía el correo
    async with aiosmtplib.SMTP(SMTP_HOST, SMTP_PORT, start_tls=True) as smtp:
        await smtp.login("support@quant4everybody.com", email_password)
        await smtp.send_message(message)

    return {"message": "Correo de verificación enviado."}


@app.get("/verify_user_email/")
async def verify_user_email(token: str):    
    try:
        # Decodificar el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        
        # Extraer la información del usuario del token
        name = payload.get("name")
        password = payload.get("password")
        email = payload.get("email")

        if not all([name, password, email]):
            raise HTTPException(status_code=400, detail=INVALID_TOKEN)
        
        user = DB.db["users"].find_one({"name": name})
        if user is not None:
            return HTMLResponse(content=USER_ALREADY_CREATED)
        

        # Insertar el nuevo usuario
        new_user = {
            "name": name,
            "password": password,
            "email": email,
            "date": datetime.now(),  # Fecha y hora actual
            "level": "0",
            "favorites": []
        }
        DB.db["users"].insert_one(new_user)

        new_user = DB.db["users"].find_one({"name": name})

        if new_user is None:                       
            raise HTTPException(status_code=400, detail=VERIFICATION_FAILED)
        
        return HTMLResponse(content=VERIFICATION_SUCCESSFUL)
        

    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail=EXPIRED_TOKEN)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail=INVALID_TOKEN)


@app.post("/check_recovery_password/")
async def check_recovery_password(login_data: LoginUser) -> dict:
    # sourcery skip: assign-if-exp, reintroduce-else
    # Buscamos el documento de la colleccion users con nombre el username pasado
    if login_data.username is not None:
        user_name = DB.db["users"].find_one({"name": login_data.username})    
        # Si no existe el user_name devolvemos el codigo 5
        if user_name is None:     
            return {"result": 5}
    else:
        # Buscamos el documento de la colleccion users con email el email pasado
        user_email = DB.db["users"].find_one({"email": login_data.email}) 
        # Si no existe el user_email devolvemos el codigo 6
        if user_email is None:     
            return {"result": 6}

    # Si no hay errores devolvemos el codigo 7
    return {"result": 7}

@app.get("/verify_recovery_password/")
async def verify_recovery_password(token: str):
    try:
        # Decodificar el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        
        # Extraer la información del usuario del token
        name = payload.get("name")
        password = payload.get("password")
        email = payload.get("email")

        if not all([name, password, email]):
            raise HTTPException(status_code=400, detail=INVALID_TOKEN)     
      

        # Actualizamos el password del usuario
        DB.db["users"].update_one({"name": name}, {"$set": {"password": password}})
        
        return HTMLResponse(content=RECOVERY_PASSWORD_SUCCESSFUL)
        

    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail=EXPIRED_TOKEN)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail=INVALID_TOKEN)
    

@app.get("/get_username_by_email/")
def get_username_by_email(login_data: LoginUser) -> dict:
    return {'result':DB.db['users'].find_one({'email': login_data.email})['name']}

@app.get("/get_email_by_username/")
def get_email_by_username(login_data: LoginUser) -> dict:
    return {'result': DB.db['users'].find_one({'name': login_data.username})['email']}