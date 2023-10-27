import sys
sys.path.append("..")
from main import app, DB

from models.models import Model, Strategy
from models.modelsSetting import Setting
from lib.ClassData import cDataCandle
from lib.ClassCase import cCase
from lib.ClassPosition import Position
from functions.functions_api import get_document_info, get_market_data, store_dataframe

# Método GET para obtener los valores del setting
@app.get("/get_settings/")
async def get_settings(model: Model)-> dict:
    return {"result": get_document_info(model.objectID, 'setting')}