'''
Revision: 
25-5-21.                                Creación de la clase 
19/10/2021              v0.1.0          Version estable. Inlcuidos los filtros por niveles: Daily Change, Session_VWAP
'''

#------------------------------
# Importamos librerias externas
#------------------------------
import pandas as pd 
#import plotly.graph_objs as go
import sys
sys.path.append("..")
import json
#------------------------------
# Importamos Clases Propias
#-----------------------------
from lib.ClassResult import cResult
from models.modelsSetting import Setting


#------------------------------
# Clase
#------------------------------
class cFilter():
#---- Constantes



#---- Constructor

    def __init__(self, setting: dict, load: bool=False, data_loaded: dict=None, data_candle: dict=None, tc: list=None, empty: bool = False, strategy_settings: dict=None, strategy_type: str=None):

        #Si se solicita una instancia vacía se devuelve aquí
        if empty: 
            return

        self.filter_setting = Setting(data_loaded) if load else Setting(setting)
        if data_candle is not None:
            self.data_candle = data_candle
        
        if strategy_settings is not None:
            self.strategy_settings = strategy_settings

        if tc is not None:
            self.tc = tc
        
        if strategy_type is not None:
            self.strategy_type = strategy_type

#---- Bloque de properties
    def set_tp(self,_value):
        self.filter_setting.trademanagement.tp = _value

    def set_sl(self,_value):
        self.filter_setting.trademanagement.sl = _value

#---- Bloque para los metodos de la clase
    # Metodo para filtrar por los parametros del nivel principal y por la vela del toque
    def apply_strategy_parameters_filter(self, filter_list: list) -> list:
        _filter = filter_list               # lista con los datos de las posiciones a filtrar
        for attb in self.strategy_settings['strategyparameters']:
            if attb['filter']['active']:
                print(f'**** Aplicando filtro {attb["value"]} ****')
                name=attb['value']
                value = self.filter_setting.strategyparameters.__dict__[attb['value']]
                if attb['filter']['criteria']=='>=':     
                    if self.filter_setting.strategyparameters.__dict__[attb['value']] is not None:
                        if attb['filter']['candle']=="tc":
                            _filter = [x for x in _filter if self.tc[x['tc_list_index']][attb['filter']['column']] >=  self.filter_setting.strategyparameters.__dict__[attb['value']] ]
                        else:
                            _temp = []

                            for x in _filter:
                                if self.data_candle[str(x['level_index'])][attb['filter']['column']] >=  self.filter_setting.strategyparameters.__dict__[attb['value']] :
                                    _temp.append(x)
                            #_filter = [x for x in _filter if self.data_candle[str(x['level_index'])][attb['filter']['column']] >=  self.filter_setting.strategyparameters.__dict__[attb['value']] ] if self.strategy_type=='level+tc' else _filter
                        print(f'Despues de aplicar criterio  {name} >= {value} : {len(_filter)}')

                elif ['criteria']=='<=':
                    if self.filter_setting.strategyparameters.__dict__[attb['value']] is not None:
                        if attb['filter']['candle']=="tc":
                            _filter = [x for x in _filter if self.tc[x['tc_list_index']][attb['filter']['column']] <=  self.filter_setting.strategyparameters.__dict__[attb['value']] ]
                        else:
                            _filter = [x for x in _filter if self.data_candle[str(x['level_index'])][attb['filter']['column']] <=  self.filter_setting.strategyparameters.__dict__[attb['value']] ]
                        print(f'Despues de aplicar criterio {name} <= {value} : {len(_filter)}')
        return _filter


    # Método para filtrar por el Daily Change
    def apply_daily_change_filter(self, filter_list: list) -> list:
        filter_buy = [
            x for x in filter_list if x['trade_type']=='buy' and x['tc']['Daily_Change'] >= self.filter_setting.levels.LDL['buy_min'] \
                and  x['tc']['Daily_Change'] < self.filter_setting.levels.LDL['buy_max']
        ]
        
        filter_sell = [ 
            x for x in filter_list if x['trade_type']=='sell' and x['tc']['Daily_Change'] > self.filter_setting.levels.LDL['sell_min'] \
                and x['tc']['Daily_Change'] <= self.filter_setting.levels.LDL['sell_max']    
        ]
        if self.filter_setting.levels.LDL['conditional_buy'] and self.filter_setting.levels.LDL['conditional_sell']:
            _filter = filter_buy + filter_sell
            _filter.sort(key=_filter['close_time'])
        elif self.filter_setting.levels.LDL['conditional_buy']:
            _filter = filter_buy
        elif self.filter_setting.levels.LDL['conditional_sell']:
            _filter = filter_sell  
            
        return _filter
    
    # Método para filtrar por el Sesion VWAP
    def apply_session_vwap_filter(self, filter_list: list) -> list:
        if self.filter_setting.levels.Session_VWAP['buy_only_above']:
            filter_buy = [ x for x in filter_list if x['trade_type']=='buy' and self.condition(x['tc'],x['open_price'],'Session_VWAP','>= 0') ]               
        elif self.filter_setting.levels.Session_VWAP['buy_only_below']:
            filter_buy = [ x for x in filter_list if x['trade_type']=='buy' and self.condition(x['tc'],x['open_price'],'Session_VWAP','< 0')]
        else:
            filter_buy = [ x for x in filter_list if x['trade_type']=='buy' ]

        
        if self.filter_setting.levels.Session_VWAP['sell_only_above']:
            filter_sell =  [ x for x in filter_list if x['trade_type']=='sell' and self.condition(x['tc'],x['open_price'],'Session_VWAP','>= 0') ]  

        elif self.filter_setting.levels.Session_VWAP['sell_only_below']:
            filter_sell = [ x for x in filter_list if x['trade_type']=='sell' and self.condition(x['tc'],x['open_price'],'Session_VWAP','< 0')]
        else:
            filter_sell =[ x for x in filter_list if x['trade_type']=='sell' ]
    
        _filter = filter_buy + filter_sell

        return sorted(_filter,key=lambda i: i['close_time']) 
    
    def condition(self, index: int, price: float, column: str, logic: str):
        if logic == '>=':
            return price >= self.data_candle[str(index)][column]
        elif logic == '<=':
            return price <= self.data_candle[str(index)][column]
        elif logic == '>':
            return price > self.data_candle[str(index)][column]
        elif logic == '<':
            return price < self.data_candle[str(index)][column]
        elif logic == '==':
            return price == self.data_candle[str(index)][column]
        elif logic == '!=':
            return price != self.data_candle[str(index)][column]
        else:
            return False

    # Método para filtrar por los Pivot Points
    def apply_pivot_points_filter(self, filter_list: list) -> list:
        if self.pp_buy_above:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' and x['tc']['PP_Change']>=0]
        elif self.pp_buy_below:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' and x['tc']['PP_Change'] < 0]
        elif self.s1_buy_above:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' and x['tc']['S1_Change']>=0]
        elif self.s1_buy_below:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' and x['tc']['S1_Change'] < 0]
        elif self.s2_buy_above:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' and x['tc']['S2_Change']>=0]
        elif self.s2_buy_below:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' and x['tc']['S2_Change'] < 0]
        elif self.s3_buy_above:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' and x['tc']['S3_Change']>=0]
        elif self.s3_buy_below:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' and x['tc']['S3_Change'] < 0]
        elif self.r1_buy_above:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' and x['tc']['R1_Change']>=0]
        elif self.r1_buy_below:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' and x['tc']['R1_Change'] < 0]
        elif self.r2_buy_above:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' and x['tc']['R2_Change']>=0]
        elif self.r2_buy_below:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' and x['tc']['R2_Change'] < 0]
        elif self.r3_buy_above:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' and x['tc']['R3_Change']>=0]
        elif self.r3_buy_below:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' and x['tc']['R3_Change'] < 0]       
        else:
            _filter_buy = [x for x in filter_list if x['trade_type']=='buy' ]
            
        if self.pp_sell_above:
            _filter_buy = [x for x in filter_list if x['trade_type']=='sell' and x['tc']['PP_Change']>=0]
        elif self.pp_sell_below:
            _filter_buy = [x for x in filter_list if x['trade_type']=='sell' and x['tc']['PP_Change'] < 0]
        elif self.s1_sell_above:
            _filter_buy = [x for x in filter_list if x['trade_type']=='sell' and x['tc']['S1_Change']>=0]
        elif self.s1_sell_below:
            _filter_buy = [x for x in filter_list if x['trade_type']=='sell' and x['tc']['S1_Change'] < 0]
        elif self.s2_sell_above:
            _filter_buy = [x for x in filter_list if x['trade_type']=='sell' and x['tc']['S2_Change']>=0]
        elif self.s2_sell_below:
            _filter_buy = [x for x in filter_list if x['trade_type']=='sell' and x['tc']['S2_Change'] < 0]
        elif self.s3_sell_above:
            _filter_buy = [x for x in filter_list if x['trade_type']=='sell' and x['tc']['S3_Change']>=0]
        elif self.s3_sell_below:
            _filter_buy = [x for x in filter_list if x['trade_type']=='sell' and x['tc']['S3_Change'] < 0]
        elif self.r1_sell_above:
            _filter_buy = [x for x in filter_list if x['trade_type']=='sell' and x['tc']['R1_Change']>=0]
        elif self.r1_sell_below:
            _filter_buy = [x for x in filter_list if x['trade_type']=='sell' and x['tc']['R1_Change'] < 0]
        elif self.r2_sell_above:
            _filter_buy = [x for x in filter_list if x['trade_type']=='sell' and x['tc']['R2_Change']>=0]
        elif self.r2_sell_below:
            _filter_buy = [x for x in filter_list if x['trade_type']=='sell' and x['tc']['R2_Change'] < 0]
        elif self.r3_sell_above:
            _filter_buy = [x for x in filter_list if x['trade_type']=='sell' and x['tc']['R3_Change']>=0]
        elif self.r3_sell_below:
            _filter_buy = [x for x in filter_list if x['trade_type']=='sell' and x['tc']['R3_Change'] < 0]
        else:
            _filter_sell =[x for x in filter_list if x['trade_type']=='sell' ]
        
        _filter = _filter_buy + _filter_sell

        return sorted(_filter,key=lambda i: i['close_time']) 
    
    # Método que aplica el filtro de las sesiones de mercado
    def apply_market_sessions_filter(self, filter_list: list, candle: str) -> list:
        session = self.filter_setting.timeconstraints.ms_origin if candle=="level" else self.filter_setting.timeconstraints.ms_tc
        index = 'level_index' if candle=='level' else 'tc'
        return [x for x in filter_list if self.data_candle[str(x[index])]['Session'] == session] 

    # Método que aplica los filtros para las horas relativas
    def apply_relative_hour_filter(self,filter_list: list) -> list:
         return [x for x in filter_list if self.tc[x['tc_list_index']]['Relative_Hour'] >= self.filter_setting.timeconstraints.min_hour \
                                        and  self.tc[x['tc_list_index']]['Relative_Hour'] < self.filter_setting.timeconstraints.max_hour]
                
    # Metodo que aplica los filtros del RSI
    def apply_rsi_filter(self, filter_list: list) -> list:    
        filter_sell = [ x for x in filter_list if self.data_candle[str(x['tc'])]['RSI'] >= self.filter_setting.indicators.rsi['max'] and x['trade_type']=='sell']
        filter_buy = [ x for x in filter_list if self.data_candle[str(x['tc'])]['RSI'] <= self.filter_setting.indicators.rsi['min'] and x['trade_type']=='buy']
        _filter = filter_sell + filter_buy
        return sorted(_filter,key=lambda i: i['close_time']) 
    
    # Método que aplica los filtros del ATR
    def apply_atr_filter(self, filter_list: list) -> list:
        return [x for x in filter_list if self.data_candle[str(x['tc'])]['ATR'] >= self.filter_setting.indicators.atr['min'] and self.data_candle[str(x['tc'])]['ATR'] <= self.filter_setting.indicators.atr['max']]
    
    # Método que aplica los filtros del AR
    def apply_ar_filter(self, filter_list: list) -> list:
        return [x for x in filter_list if self.data_candle[str(x['tc'])]['AR'] >= self.filter_setting.indicators.ar['min'] and self.data_candle[str(x['tc'])]['AR'] <= self.filter_setting.indicators.ar['max']]
    
    # Método que aplica los filtros de los limites diarios de balance
    def apply_daily_balance_limit_filter(self, filter_list: list) -> list:
        #Generator para el balance diario
        def DailyBalance(_result, _marketdays, _tickvalue, _size, _fee):
            _dailybalance=0
            _day=0
            for _res, _md in zip(_result,_marketdays):
                if _md!=_day:
                    _day = _md
                    _dailybalance = 0
                _dailybalance += _res*_size*_tickvalue -_fee*_size
                yield _dailybalance
        
        #Generator para chequear los tp y sl diarios
        def Check_Daily_Balance(_balance,_marketdays,_daily_tp,_daily_sl):
            _day=0
            _reached = False
            _last_reached = False
            for _bal, _md in zip(_balance,_marketdays):
                if _md != _day:
                    _day = _md
                    _reached = False
                    _last_reached = False

                if _last_reached == False:
                    if _daily_tp>0 and _bal >= _daily_tp:
                        _last_reached = True    
                    elif _daily_sl > 0 and _bal <= -1*_daily_sl:
                        _last_reached = True
                else:
                    _reached = True
                yield _reached


        _filter['daily_balance']=list(DailyBalance(_filter.ST1_Result,_filter.TC_Market_Day,self.filter_setting.instrument.tickvalue,
                                                    self.filter_setting.trademanagement.size,self.filter_setting.account.fee))
        _filter['daily_reached']=list(Check_Daily_Balance(_filter.daily_balance,_filter.TC_Market_Day,self.filter_setting.account.daily_take_profit, self.filter_setting.account.daily_stop_loss))
        _delete_rows = _filter[_filter.daily_reached==True].index
        _filter = _filter.drop(_delete_rows,axis=0)
      
    #Funcion que aplica los filtros y almacena el dataframe filtrado
    def get_filtered_data(self, positions: list) -> None: 
        """
        Funcion que recibe una lista con las posiciones, aplica los filtros y lo almacena en un dataframe filtrado 
        para despues ser usado en la obtención de las graficas
        *Arg: positions: Lista con las posiciones antes de aplicar los filtros
        """
        
        _filter = positions
        print(f'Positions antes de todos los filtros: {len(_filter)} \n')

     #Filtros de los Parametros de la Estregia 
        print(f'Positions antes de los filtros de los parametros de la  estrategia: {len(_filter)}')
        _filter = self.apply_strategy_parameters_filter(filter_list=_filter)
        print(f'Positions despues de los filtros de los parametros de la  estrategia: {len(_filter)} \n')
    
        
     #Filtros de niveles
        #TODO: Repensar lo de los filtros por niveles


     #Filtro del VWAP   
        if 'Session_VWAP' in self.filter_setting.levels.levels:
            print(f'Positions antes de los filtros del nivel VWAP: {len(_filter)}')
            _filter = self.apply_session_vwap_filter(filter_list=_filter)
            print(f'Positions despues de los filtros del nivel VWAP: {len(_filter)} \n')
        
     # Filtro de los PP
        if 'pp' in self.filter_setting.levels.levels:
            print(f'Positions antes de los filtros del nivel PP: {len(_filter)}')
            _filter = self.apply_pivot_points_filter(filter_list=_filter)
            print(f'Positions despues de los filtros del nivel PP: {len(_filter)} \n')
            
     #Filtros de las sessiones de mercado
        if hasattr(self.filter_setting.timeconstraints,'ms_origin') and self.filter_setting.timeconstraints.ms_origin != 'All Sessions' and self.filter_setting.timeconstraints.ms_origin is not None:
            print(f'Positions antes de los filtros de la sesion de mercado para la vela origen: {len(_filter)}')
            _filter = self.apply_market_sessions_filter(filter_list=_filter, candle='level')
            print(f'Positions despues de los filtros de la sesion de mercado para la vela origen: {len(_filter)} \n')
            
        if hasattr(self.filter_setting.timeconstraints,'ms_level') and self.filter_setting.timeconstraints.ms_tc != 'All Sessions' and self.filter_setting.timeconstraints.ms_tc is not None:
            print(f'Positions antes de los filtros de la session de mercado para la vela tc: {len(_filter)}')
            _filter = self.apply_market_sessions_filter(filter_list=_filter, candle="tc")
            print(f'Positions despues de los filtros de la session de mercado para la vela tc: {len(_filter)} \n')

     #Filtros para el rango horario
        print(f'Positions antes de los filtros para el rango horario: {len(_filter)} ')
        _filter = self.apply_relative_hour_filter(filter_list= _filter)
        print(f'Positions despues de los filtros para el rango horario: {len(_filter)} \n')

     #Filtros de Indicadores
       #Filtros de RSI
        if 'rsi' in self.filter_setting.indicators.indicators and self.filter_setting.indicators.rsi['included']:
            print(f'Positions antes de los filtros para el inidcador RSI: {len(_filter)}')
            _filter = self.apply_rsi_filter(filter_list=_filter)
            print(f'Positions despues de los filtros para el inidcador RSI: {len(_filter)} \n')
            
       #Filtro del ATR
        if 'atr' in self.filter_setting.indicators.indicators and self.filter_setting.indicators.atr['included']:
            print(f'Positions antes de los filtros para el inidcador ATR: {len(_filter)}')
            _filter = self.apply_atr_filter(filter_list=_filter)
            print(f'Positions despues de los filtros para el inidcador ATR: {len(_filter)} \n')
       #Filtro del Rango Medio 
        if 'ar' in self.filter_setting.indicators.indicators and self.filter_setting.indicators.indicators.ar['included']:
            print(f'Positions antes de los filtros para el inidcador AR: {len(_filter)}')
            _filter = self.apply_ar_filter(filter_list=_filter)
            print(f'Positions despues de los filtros para el inidcador AR: {len(_filter)} \n')
        #Filtro de daily_change
        if 'daily_change' in self.filter_setting.indicators.indicators and self.filter_setting.indicators.indicators.daily_change['included']:
            print(f'Positions antes de los filtros del Daily Change: {len(_filter)}')
            _filter = self.apply_daily_change_filter(filter_list=_filter)
            print(f'Positions despues de los filtros del Daily Change: {len(_filter)} \n')    

     #Filtros de la Gestion de la Cuenta
        if self.filter_setting.account.limited_daily_balance:
            print(f'Positions antes de los filtros para el limite del daily balance: {len(_filter)}')
            _filter = self.apply_daily_balance_limit_filter(filter_list=_filter)
            print(f'Positions despues de los filtros para el limite del daily balance: {len(_filter)} \n')
            

     #Ordenamos los trades y lo almacenamos 
        self.filter_case = _filter
        print(f'Desspues de todos los filtros nos quedan {len(self.filter_case)}')

    
    #TODO Esto hay que cambiarlo todo, vamos a intentar no tener pd.Dataframe
    #Funcion que devuelve informacion sobre los trades buy y sell sobre y bajo un nivel
    def above_below_level_info(self, level)-> list:
        """Funcion que devuelve la informacion desglosada de los trade de compra y venta, sobre y bajo un nivel dado. 

        Args:
            level (str): Nombre de la columna con el nivel sobre el que dar la informacion.

        Returns:
            list :  Lista con los valores de la tabla correspondiente a Compra (Sobre y Bajo el nivel) y Venta (Sobre y Bajo el nivel)
        """           
     
        buy_above_level_rwin = round((self.positions_above_level('buy','win',level)/self.positions_above_level('buy','total',level))*100,2) if  self.positions_above_level('buy','total',level)> 0 else 0        
        sell_above_level_rwin = round((self.positions_above_level('sell','win',level)/self.positions_above_level('sell','total',level))*100,2) if  self.positions_above_level('sell','total',level)> 0 else 0
        buy_below_level_rwin = round((self.positions_below_level('buy','win',level)/self.positions_below_level('buy','total',level))*100,2) if  self.positions_below_level('buy','total',level)> 0 else 0       
        sell_below_level_rwin = round((self.positions_below_level('sell','win',level)/self.positions_below_level('sell','total',level))*100,2) if  self.positions_below_level('sell','total',level)> 0 else 0
        
        #_columns=['Total','Win','Loss','Ratio Win']
        _buy_above = [self.positions_above_level('buy','total',level), self.positions_above_level('buy','win',level), self.positions_above_level('buy','loss',level),buy_above_level_rwin]
        _buy_below = [self.positions_below_level('buy','total',level), self.positions_below_level('buy','win',level), self.positions_below_level('buy','loss',level), buy_below_level_rwin]
        _sell_above = [self.positions_above_level('sell','total',level), self.positions_above_level('sell','win',level), self.positions_above_level('sell','loss',level),sell_above_level_rwin]
        _sell_below = [self.positions_below_level('sell','total',level), self.positions_below_level('sell','win',level), self.positions_below_level('sell','loss',level), sell_below_level_rwin]
                
        _row = []
        for x in [_buy_above,_buy_below,_sell_above,_sell_below]:
            _row.extend(x)

        return _row

    def positions_above_level(self, trade_type: str, value: str, level: float):
        if value=="total":
            return sum(pos['trade_type'] == trade_type and pos['open_price'] >= pos['levels'][level] for pos in self.filter_case) 
        elif value=="win":
            return sum(pos['trade_type'] == trade_type and pos['open_price'] >= pos['levels'][level] and pos['trade_result'] in ['win','pwin'] for pos in self.filter_case) 
        else:
            return sum(pos['trade_type'] == trade_type and pos['open_price'] >= pos['levels'][level] and pos['trade_result'] in ['loss','ploss'] for pos in self.filter_case) 

    def positions_below_level(self, trade_type: str, value: str, level: float):
        if value=="total":
            return sum(pos['trade_type'] == trade_type and pos['open_price'] <= pos['levels'][level] for pos in self.filter_case) 
        elif value=="win":
            return sum(pos['trade_type'] == trade_type and pos['open_price'] <= pos['levels'][level] and pos['trade_result'] in ['win','pwin'] for pos in self.filter_case) 
        else:
            return sum(pos['trade_type'] == trade_type and pos['open_price'] <= pos['levels'][level] and pos['trade_result'] in ['loss','ploss'] for pos in self.filter_case) 


    # Función que calcula el objeto resultado con los filtros 
    def get_filter_result(self):
        # cuando se lee de la base de datos el indice de self.data_candle es un str pero cuando se ejecuta un nuevo analisis el indice del dict es un int
        # Esto es un parche , hay que cambiarlo
        #if isinstance(list(self.data_candle.keys())[0],int):
        #    interval_days = [self.tc[x['tc_list_index']]['Market_Day'] - self.data_candle[x['level_index']]['Market_Day'] for x in self.filter_case] 
        #else:
        #    interval_days = [self.tc[x['tc_list_index']]['Market_Day'] - self.data_candle[str(x['level_index'])]['Market_Day'] for x in self.filter_case] 
        data = {
            'open_time':    [x['open_time'] for x in self.filter_case],
            'open_price':   [x['open_price'] for x in self.filter_case],
            'close_price':  [x['close_price'] for x in self.filter_case],
            'close_time':   [x['close_time'] for x in self.filter_case],
            'type':         [x['trade_type'] for x in self.filter_case],
            'trade_result': [x['trade_result'] for x in self.filter_case],
            'tick_result':  [x['tick_result'] for x in self.filter_case],
            'cash_result':  [x['cash_result'] for x in self.filter_case],
            'market_day':   [x['market_day'] for x in self.filter_case],
            'relative_hour':[x['relative_hour'] for x in self.filter_case],
            'interval':     [x['interval'] for x in self.filter_case],
            'interval_days':[x['interval_days'] for x in self.filter_case],   
        }

        self.result = cResult(setting = self.filter_setting.to_dict(), data = data) 


    # Método de devuelve una lista con los datos para el calculo del option de la grafica del parametro que se le pase. El parametro es de la vela del nivel que provoca la posicion
    def get_data_level_for_option(self, parameter: str) ->list:
        return [{parameter: self.data_candle[str(x['level_index'])][parameter], 'tick_result': x['tick_result']} for x in self.filter_case]
    
    # Método de devuelve una lista con los datos para el calculo del option de la grafica del parametro que se le pase. El parametro es de la vela del nivel que provoca la posicion
    def get_data_tc_for_option(self, parameter: str) ->list:
        return [{parameter: self.tc[x['tc_list_index']][parameter], 'tick_result': x['tick_result']} for x in self.filter_case]