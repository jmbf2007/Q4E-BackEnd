import math
import numpy as np
import sys
sys.path.append("..")

from main import app,DB



from models.models import Model
from functions.functions_api import get_document_info, get_filtered_object

@app.get('/get_filter_setting/')
async def get_filter_setting(model: Model):
    return {"result": get_document_info(model_id=model.objectID, collection="filter")}
    

@app.get('/get_filtered_graph/')
async def get_filtered_graph(model: Model, param: dict, filterdata: dict, selection: dict) -> dict:
    # Primero verificamos que hay alguna seleccion no False
    if sum(list(selection.values()))==0:
        return {"result": 
            {
                "attributegroup": {},
                "dailybalances": {},
                "dailyresulthistogram": {},
                "hourlyinformation": {},
                "dailysummary": {},
                "strategyparamertersinformation": {},
                "indicators": {}
            }
        }
        

    #Instanciamos el objeto filter ya filtrado
    _filter = get_filtered_object(model,filterdata)

    _attributegroup, _dailybalances, _dailyresulthistogram, _hourlyinformation, _dailysummary, _strategtparametersinformation = {}, {}, {}, {}, {}, {}

    if selection['attributegroup']:
        _attributegroup =  _filter.result.get_attributegroup_option(param['attributegroup'])

    elif selection['dailybalances']:
        _filter.result.get_all_result_attributes()
        _dailybalances =  _filter.result.dailyresult.get_dailybalances_option(param['dailybalances'])

    elif selection['dailyresulthistogram']:
        _dailyresulthistogram =  _filter.result.dailyresult.get_dailyresulthistogram_option(data=np.array(_filter.result.dailyresult.data.Balance_Percentage.tolist()),
                                                                    _min=math.floor(_filter.result.dailyresult.data.Balance_Percentage.min()),
                                                                    _max=math.ceil(_filter.result.dailyresult.data.Balance_Percentage.max()),
                                                                    param= param['dailyresulthistogram']
        )

    elif selection['hourlyinformation']:
        _hourlyinformation = _filter.result.get_hourlyinformation_option(param['hourlyinformation'])

    return (
        {
            "result": {
                "attributegroup": _attributegroup,
                "dailybalances": _dailybalances,
                "dailyresulthistogram": _dailyresulthistogram,
                "hourlyinformation": _hourlyinformation,
                "dailysummary": _dailysummary,
                "strategyparamertersinformation": _strategtparametersinformation,
                "indicators": {}
            }
        }
    )  
        

@app.get('/get_levelsinformation/')
async def get_levelsinformation(model: Model, filterdata: dict):


    #Instanciamos    el objeto filter ya filtrado
    _filter = get_filtered_object(model,filterdata)

    # Cargamos los datos
    rows=[]
    data = [] 

    if 'Session_VWAP' in _filter.filter_setting.levels.levels:
        data.append(_filter.above_below_level_info(level='Session_VWAP'))
        rows.append('Session VWAP')
    if 'PP' in _filter.filter_setting.levels.levels:
        for level in ['PP','S1','S2','S3','R1','R2','R3']:
            data.append(_filter.above_below_level_info(level=level))
            rows.append(f'Pivot Point ({level})')
    if 'LD_High'in _filter.filter_setting.levels.levels:
        data.append(_filter.above_below_level_info(level='LD_High'))
        rows.append('Last Day High')
    
    if 'LD_Low' in _filter.filter_setting.levels.levels:
        data.append(_filter.above_below_level_info(level='LD_Low'))
        rows.append('Last Day Low')
        
    if 'LD_Close' in _filter.filter_setting.levels.levels:
        data.append(_filter.above_below_level_info(level='LD_Close'))
        rows.append('Last Day Close')
                

    return {"result": {'data': data, 'rows': rows}}

@app.get('/get_touched_levelsinformation/')
async def get_touched_levelsinformation(model: Model, filterdata: dict):
    #Instanciamos el objeto filter ya filtrado
    _filter = get_filtered_object(model,filterdata)

    # Obtenemos los datos con el metodo de clase Filter get_tocuhed_levels_info
    return {"result": _filter.get_touched_levels_info()}



@app.get('/get_dailysummary_piechart/')
async def get_dailysummary_piechart(model: Model, filterdata: dict) -> dict:
    #Instanciamos el objeto filter ya filtrado
    _filter = get_filtered_object(model,filterdata)
    return {"result": {
                'option_pie': _filter.result.dailyresult.get_pie_echart(),
                'dataframe': _filter.result.dailyresult.get_summaryDataFrame('summary')
            }
    }


@app.get('/get_strategy_parameters/')
async def get_strategy_parameters(model: Model) -> dict:
    model = DB.db['models'].find_one({'_id': model.objectID})
    strategy_id = model['strategy_id']
    strategy = DB.db['strategies'].find_one({'_id': strategy_id})
    strategy_parameters = [param['name'] for param in strategy['settings']['strategyparameters'] if param['hidden']==False]
    return {"result": strategy_parameters}


@app.get('/get_strategy_parameters_information/')
async def get_strategy_parameters_information(model: Model, filterdata: dict, strategy_parameters: dict):
    option = {}

    #Instanciamos el objeto filter ya filtrado
    _filter = get_filtered_object(model,filterdata)
    if strategy_parameters['selected_parameter'] == "Interval by Days":
        option = _filter.result.get_interval_daily_option(num_days=10)
    elif strategy_parameters['selected_parameter'] == "Interval same Session":
        option =  _filter.result.get_parameter_option(parameter='Interval',
                                                     data=_filter.get_data_tc_for_option(parameter='Interval'),
                                                     initial_range=1,
                                                     final_range = 200,
                                                     #datatype='lineal',
                                                     step=strategy_parameters['step'],
                                                     title = 'Interval',
                                                     yAxis_zero=True,
                                                     show_label=strategy_parameters['show_label'])
    elif strategy_parameters['selected_parameter'] == "Range Min":
        option = _filter.result.get_parameter_option(parameter='Range', 
                                                     data=_filter.get_data_level_for_option(parameter='Range'), 
                                                     initial_range=_filter.filter_setting.strategyparameters.range_min, 
                                                     final_range=50, 
                                                     #datatype='lineal',
                                                     step=strategy_parameters['step'],
                                                     title='Range Level Candle',
                                                     yAxis_zero=True,
                                                     show_label=strategy_parameters['show_label'])
                                                    
    elif strategy_parameters['selected_parameter'] == 'Body/Range Ratio Min':
        option = _filter.result.get_parameter_option(parameter='BR', 
                                                     data=_filter.get_data_level_for_option(parameter='BR'), 
                                                     initial_range=_filter.filter_setting.strategyparameters.br_min, 
                                                     final_range = 100,
                                                     #datatype='percentage',
                                                     step=strategy_parameters['step'],                                                     
                                                     title='Body/Range Level Candle',
                                                     yAxis_zero=True,
                                                     show_label=strategy_parameters['show_label'])

    elif strategy_parameters['selected_parameter'] == 'MVC Max':
        option = _filter.result.get_parameter_option(parameter='MVC_Percentage', 
                                                     data=_filter.get_data_level_for_option(parameter='MVC_Percentage'), 
                                                     initial_range=0, 
                                                     final_range=_filter.filter_setting.strategyparameters.mvc_max,  
                                                     #datatype='percentage',
                                                     step=strategy_parameters['step'],
                                                     title='MVC Level Candle',
                                                     yAxis_zero=True,
                                                     show_label=strategy_parameters['show_label'])

    elif strategy_parameters['selected_parameter'] == 'MVC TC Min':
        option = _filter.result.get_parameter_option(parameter='MVC_Percentage',
                                                     data=_filter.get_data_tc_for_option(parameter='MVC_Percentage'),
                                                     initial_range=_filter.filter_setting.strategyparameters.mvc_tc_min,
                                                     final_range = 100,
                                                     #datatype='percentage',
                                                     step=strategy_parameters['step'],
                                                     title = 'MVC Touch Candle',
                                                     yAxis_zero=True,
                                                     show_label=strategy_parameters['show_label'])
                                                     
                                                

    elif strategy_parameters['selected_parameter'] == 'Bounce Max':
        option = {}
    elif strategy_parameters['selected_parameter'] == 'Bounce Min':
        option =  _filter.result.get_interval_single_day_option()
    return  {"result": option  }
               


@app.get('/get_indicator_atr_information/')
async def get_indicator_atr_information(model: Model, filterdata: dict, param_atr: dict)-> dict:
    option = {}
    #Instanciamos el objeto filter ya filtrado
    _filter = get_filtered_object(model,filterdata)

    option = _filter.result.get_parameter_option(
                        parameter='ATR',
                        data=_filter.get_data_tc_for_option(parameter='ATR'),
                        initial_range=param_atr['initial_range'],
                        final_range=param_atr['final_range'],
                        step = param_atr['step'],
                        title = 'ATR',
                        yAxis_zero=True,
                        show_label=param_atr['show_label']
    )

    return  {"result": option  }


@app.get('/get_indicator_ar_information/')
async def get_indicator_ar_information(model: Model, filterdata: dict, param_ar: dict) -> dict:
    option = {}
    #Instanciamos el objeto filter ya filtrado
    _filter = get_filtered_object(model,filterdata)

    option = _filter.result.get_parameter_option(
                        parameter='AR',
                        data=_filter.get_data_tc_for_option(parameter='AR'),
                        initial_range=param_ar['initial_range'],
                        final_range=param_ar['final_range'],
                        step = param_ar['step'],
                        title = 'AR',
                        yAxis_zero=True,
                        show_label=param_ar['show_label']
    )

    return  {"result": option  }

@app.get('/get_indicator_rsi_information/')
async def get_indicator_rsi_information(model: Model, filterdata: dict, param: dict) ->dict:
    option = {}
    #Instanciamos el objeto filter ya filtrado
    _filter = get_filtered_object(model,filterdata)

    option = _filter.result.get_percent_parameter_option(
                        parameter='RSI',
                        data=_filter.get_data_tc_for_option(parameter='RSI'),
                        step = param['step'],
                        title = 'RSI',
                        show_label=param['show_label']
    )

    return  {"result": option  }

@app.get('/get_indicator_tls_information/')
async def get_indicator_tls_information(model: Model, filterdata: dict, param: dict) -> dict:
    option = {}
    #Instanciamos el objeto filter ya filtrado
    _filter = get_filtered_object(model,filterdata)

    _data = _filter.get_data_tc_for_option_multiparameter(parameters=[
            'TLS_Upper_Delta',
            'TLS_Upper_Ask_Percentage',
            'TLS_Upper_Ask_Levels_Percentage',
            'TLS_Lower_Delta',
            'TLS_Lower_Bid_Percentage',
            'TLS_Lower_Bid_Levels_Percentage',
            'TLS_Result'
            ]),

    option = _filter.result.get_tls_information_options(
        data = _data[0],
        value_step = param['value_step'],
        percentage_step = param['percentage_step'],
        lower_delta_max = param['lower_delta_max'],
        lower_delta_min = param['lower_delta_min'],
        upper_delta_max = param['upper_delta_max'],
        upper_delta_min = param['upper_delta_min'],
        show_label = param['show_label']
    )

    return  {"result": option  }



