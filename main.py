from fastapi import FastAPI
import sys
sys.path.append("..")


from db.mongo_manager import MongoManager

# Instancia para la API
app =FastAPI()                          


# Instancia para la Base de Datos
DB=MongoManager()

@app.on_event("startup")
def startup():
    DB.connect_to_database(path = "mongodb+srv://admin:admin@clusterq4e.mgux7.mongodb.net/db?retryWrites=true&w=majority")

@app.on_event("shutdown")
def shutdown():
    DB.close_database_connection()    


# Funciones de las api de cada app

from login.login_api import *
from strategy_selection.strategy_selection_api import *
from parameter_settings.parameter_settings_api import *
from chart.chart_api import *
from table.table_api import *
from sensitivity_analysis.sensitivity_analysis_api import *
from parametric_analysis.parametric_analysis_api import *
from wfa.wfa_api import *
from porfolio.porfolio_api import *
from strategy_builder.strategy_builder_api import *
