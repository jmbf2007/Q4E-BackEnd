#----- API CommonFunctions

import json
from bson import ObjectId
import numpy as np
import pandas as pd
import datetime as dt
import sys
sys.path.append("..")

from main import DB, MD


from models.models import Model
from lib.ClassFilter import cFilter
from lib.ClassResult import cResult





class JSONEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, ObjectId):
            return str(item)
        return json.JSONEncoder.default(self, item)

def get_document_info(model_id: ObjectId, collection: str)-> dict:
    document = DB.db[collection].find_one({'model_id': model_id})
    del document["_id"]
    del document["model_id"]
    return document
    
def custom_encoder(obj):
    if isinstance(obj,np.datetime64):
        return pd.Timestamp(obj).to_pydatetime()
    elif isinstance(obj,np.floating):
        return float(obj)
    elif isinstance(obj,np.integer):
        return int(obj)
    elif isinstance(obj,np.ndarray):
        return obj.tolist()
    else:
        return obj

def store_dataframe(df: pd.DataFrame, collection: str, super: str,model_id: ObjectId,chunksize: int=10000000) -> None:
    '''
        El Método trocea un dataframe y lo almacena en partes usando dos coleciones: collection y collection_chunks
        *Arg:   db ->           Conexion a la base de datos
                df ->           Dataframe a almacenar
                collection ->   Nombre de la colección a almacenar. Pej: data, result, dailyresult, etc.
                chunksize ->    Tamaño máximo en bytes de los trozos. Por defecto está algo inferior al tamaño máximo que permite MongoDB para los documentos(16MB)
        *Ret:   El método no devuelve nada, almacena los trozos y actualiza el documento matriz con una lista de los id de cada trozo
        '''
    # El método to_json() de pandas da problemas al convertir a timestamp el datetime. Para evitar esto convertimos manualmente a timestamp 
    # las columnas del tipo datetime antes de llamar a to_json

    if 'Time' in df.columns.tolist():
        df.Time = df.Time.apply(lambda t: dt.datetime.timestamp(t)).astype(int)

    if 'TC_Time' in df.columns.tolist():
        try:
            df.TC_Time = df.TC_Time.apply(lambda t: dt.datetime.timestamp(t) if isinstance(t,dt.datetime) else t).astype(int)
        except Exception:
            df.TC_Time = df.TC_Time.apply(lambda t: 0 if pd.isnull(t) else dt.datetime.timestamp(t)).astype(int)


    if 'Open_Time' in df.columns.tolist():
        df.Open_Time = df.Open_Time.apply(lambda t: dt.datetime.timestamp(t) if isinstance(t,dt.datetime) else t).astype(int)

    if 'Close_Time' in df.columns.tolist():
        df.Close_Time = df.Close_Time.apply(lambda t: dt.datetime.timestamp(t) if isinstance(t,dt.datetime) else t).astype(int)

    if 'ST1_Open_Time' in df.columns.tolist():
        df.ST1_Open_Time = df.ST1_Open_Time.apply(lambda t: dt.datetime.timestamp(t) if isinstance(t,dt.datetime) else t).astype(int)

    if 'ST1_Close_Time' in df.columns.tolist():
        df.ST1_Close_Time = df.ST1_Close_Time.apply(lambda t: dt.datetime.timestamp(t) if isinstance(t,dt.datetime) else t).astype(int)


    # Calculamos el numero de trozos a dividr el dataframe en funcion del tamaño se trozo seleccionado
    num_chunks=int(df.memory_usage(deep=True).sum()/chunksize)+1
    # Numero de filas del df que contiene cada trozo
    rows_per_chunk = int(len(df)/num_chunks)
    chunks_id=[]

    for i in range(num_chunks):
        part=df[i*rows_per_chunk:(i+1)*rows_per_chunk]
        doc={'model_id': model_id,
             'super':super,
             'data':part.to_json(),
             'chunk':i                 
            }
        DB.db[f'{collection}_chunks'].insert_one(doc)
        chunks_id.append(DB.db[f'{collection}_chunks'].find_one({'model_id': model_id, 'super': super,'chunk':i})['_id'])

    # Actualizamos el documento matriz
    DB.db[collection].update_one({'model_id': model_id, 'super': super},{'$set': {'chunks':chunks_id}})

def get_market_data(ticker: str, tf: int, start_date: int, end_date: int, of_active: bool=False)-> pd.DataFrame:
    #Datos 
    database = ticker
    collection = f'{tf}M'
    start_date = dt.datetime.fromtimestamp(start_date)
    end_date = dt.datetime.fromtimestamp(end_date)  
    # Busqueda en la base de datos
    document = MD.client[database][collection].find({'Time': {"$gte": start_date, "$lt": end_date}})
    # Convertimos a df
    df = pd.DataFrame(list(document))
    # Eliminamos las columnas que no nos interesan
    df = df.drop(['_id'],axis=1)
    if of_active==False:
        df = df.drop(['Ask','Bid'],axis=1)
    # Eliminamos las filas iniciales hasta que tengamos una nueva session de mercado
    for i,_new in zip(df.index,df.NewSession):
        if _new==True:                
            break
        else:
            df= df.drop([i],axis=0)   
        
    return df.reset_index(drop=True)
   
def restore_dataframe(collection: str, super: str, model_id: ObjectId)-> pd.DataFrame:
    #Identificamos el documento que contiene los id de los trozos
    document = DB.db[collection].find_one({'model_id': model_id, 'super': super})
    # Creamos el df de salida
    df = pd.DataFrame()
    #Recorremos la lista con los id de los trozos, tomamos el atributo data del documento, lo convertimos a json, despues a Dataframe y lo unimos 
    for chunk_id in document['chunks']:
        data=DB.db[f'{collection}_chunks'].find_one({'_id': chunk_id,'super': super})['data']
        js = json.loads(data)      
        temp = pd.DataFrame(js)
        df = pd.concat([df,temp])

    # Adaptamos los formatos de fechas a datetime, se almacenan como Timestamp en segundos
            
    if 'Time' in df.columns.tolist():
        df.Time =df.Time.apply(lambda x: dt.datetime.fromtimestamp(x))           

    if 'TC_Time' in df.columns.tolist():
        df.TC_Time=df.TC_Time.apply(lambda x: dt.datetime.fromtimestamp(x) if x>0 else None)          
    
    if 'TC_Index' in df.columns.tolist():
        df.TC_Index = df.TC_Index.apply(lambda x: int(x))

    if 'Open_Time' in df.columns.tolist():
        df.Open_Time = df.Open_Time.apply(lambda x: dt.datetime.fromtimestamp(x) if x>0 else None)
    
    if 'Close_Time' in df.columns.tolist():
        df.Close_Time = df.Close_Time.apply(lambda x: dt.datetime.fromtimestamp(x) if x>0 else None)
    
    if 'ST1_Open_Time' in df.columns.tolist():
        df.ST1_Open_Time = df.ST1_Open_Time.apply(lambda x: dt.datetime.fromtimestamp(x) if x>0 else None)
    
    if 'ST1_Close_Time' in df.columns.tolist():
        df.ST1_Close_Time = df.ST1_Close_Time.apply(lambda x: dt.datetime.fromtimestamp(x) if x>0 else None)
            
    return df

def get_filtered_object(model: Model, filterdata: dict)->object:
    #Instanciamos el objeto filter
    _filter = cFilter(setting = filterdata, strategy_type=model.strategy_type)

    #Obtenemos el dataframe de los datos antes de ser filtrado
    positions =  DB.db['positions'].find_one({'model_id': model.objectID, 'super': 'case'})['positions']
    _filter.tc = DB.db['tc'].find_one({'model_id': model.objectID, 'super': 'case'})['tc']
    _filter.data_candle = restore_dataframe(collection='data', super='case', model_id=model.objectID).to_dict(orient='index')
    #Leemos las hipotesis de la estrategia
    strategy_id = DB.db['models'].find_one({'_id': model.objectID})['strategy_id']
    strategy_info = DB.db['strategies'].find_one({'_id': strategy_id})
    _filter.strategy_settings = strategy_info['settings']
    #Aplicamos los filtros a los datos
    _filter.get_filtered_data(positions)
    _filter.get_filter_result()
    
    return _filter

def is_strategy_type(model: Model, strategy_type:str)->bool:
    strategy_id = DB.db['models'].find_one({'_id': model.objectID})['strategy_id']
    strategy_info = DB.db['strategies'].find_one({'_id': strategy_id})
    return strategy_info['strategy_type']==strategy_type

def get_result_object(model: Model, datatype: str)-> object:
    # Leemos las posiciones
    positions = DB.db['positions'].find_one({'model_id': model.objectID, 'super': datatype})

    data = {
        'open_time':    [x['open_time'] for x in positions['positions']],
        'open_price':   [x['open_price'] for x in positions['positions']],
        'close_price':  [x['close_price'] for x in positions['positions']],
        'close_time':   [x['close_time'] for x in positions['positions']],
        'type':         [x['trade_type'] for x in positions['positions']],
        'trade_result': [x['trade_result'] for x in positions['positions']],
        'tick_result':  [x['tick_result'] for x in positions['positions']],
        'cash_result':  [x['cash_result'] for x in positions['positions']],
        'market_day':   [x['market_day'] for x in positions['positions']],
        'relative_hour':[x['relative_hour'] for x in positions['positions']],
        'interval':     [x['interval'] for x in positions['positions']],
        'interval_days':[x['interval_days'] for x in positions['positions']],   
    }

    return cResult(setting = get_document_info(model.objectID,'setting'), data = data) 

def get_parameter_behavior(model_id: ObjectId, param_name:str) -> tuple:
    strategy_id = DB.db['models'].find_one({'_id': model_id})['strategy_id']

    strategy_settings = DB.db['strategies'].find_one({'_id': strategy_id})['settings']

    for collection in list(strategy_settings.keys()):
        for param_object in strategy_settings[collection]:
            if param_object['name'] == param_name:
                return (collection, param_object['value'])

    return ("None", "None")


