
#------------------------------
# Importamos librerias externas
#------------------------------
import pandas as pd
import numpy as np
import math

import sys
sys.path.append("..")

MARKET_SESSIONS_CANDLE_INDEX={
    1:  [480,930,1335],
    5:  [96,186,267],
    15: [32,62,89],
    30: [16,31,44],
    60: [8,15,22]
}

#------------------------------
# Importamos Clases Propias
#-----------------------------
import lib.functions as fn
from models.modelsSetting import Setting
#------------------------------
# Clase
#------------------------------
class cDataCandle():
#---- Constructor
    def __init__(self,data: pd.DataFrame, setting: dict, super: str='case', load=False, strategy_type: str=None):

        if not load:
            self.data = data
            self.setting = Setting(data=setting)
            self.strategy_type = strategy_type


#---- Bloque de Properties para cambiar atributos

    #Metodo que asigna la lista levels
    def Set_Setting(self, _value: dict):
        self.setting = Setting(_value)
      
    #Método que asigna el dataframe 
    def set_data(self,_value:dict) -> None:
        self.data = pd.DataFrame(_value)

#---- Bloque de metodos para la obtención de datos de la vela 
    #Calcula el tipo de DP: 1 alcista -1 bajista 0 doji
    def get_candle_type(self)-> None:
        self.data['Candle_Type']=list(map(lambda op, cl: fn.candle_type(op,cl), self.data['Open'], self.data['Close']))
    
    # Método que numera las velas dentro de la sesion de mercado
    def get_candle_session_index(self)-> None:
        self.data['Candle_Session_Index']=list(fn.candle_session_index(self.data.NewSession))
    
    #Método que calcula el Rango, Cuerpo y la relacion Cuerpo/Rango
    def get_range(self)-> None:
        self.data['Range']=fn.candle_range(self.data.High, self.data.Low, self.setting.instrument.ticksize)
    
    def get_body(self) -> None:
        self.data['Body']=fn.candle_body(self.data.Open, self.data.Close, self.setting.instrument.ticksize)
        
    def get_bodyrange_ratio(self) -> None:
        self.data['BR']=round((self.data.Body/self.data.Range)*100)        

    #Método que calcula el pullback de una vela desde el cierre de la vela anterior
    def get_pullback(self)-> None:
        self.data['Pullback_Buy'] = list(fn.candle_pullback(self.data.index, self.data.High, self.data.Low, self.data.Close,self.setting.instrument.ticksize,"Buy"))
        self.data['Pullback_Sell'] = list(fn.candle_pullback(self.data.index, self.data.High, self.data.Low, self.data.Close,self.setting.instrument.ticksize,"Sell"))

    #Método para calcular la posicion del MVC en % desde el origen    
    def get_mvc_percentage(self)-> None:
        self.data['MVC_Percentage']=list(map(lambda o,h,l,c,m: fn.candle_mvc_percentage(o, h, l, c, m),
                                   self.data['Open'],
                                   self.data['High'],
                                   self.data['Low'],
                                   self.data['Close'],
                                   self.data['MVC']))
    
    # Metodo que calcula el gap entre el CVM y el cuerpo de la vela
    def get_mvc_gap(self)-> None:
        self.data['MVC_Gap']=list(map(lambda o,m,d: fn.candle_mvc_gap(o, m, d, self.setting.instrument.ticksize),
                                   self.data['Open'],
                                   self.data['MVC'],
                                   self.data['Candle_Type']))


    #Método que calcula la hora de mercado de la vela respecto a la apertura de la sesion 
    def get_relative_hour(self)-> None:
        self.data['Relative_Hour'] = list(fn.candle_relative_hour(self.data.NewSession,self.data.Time))

    #Método que calcula la sesion de mercado pertenece las velas (DEPRECATED)
    def get_market_sessions(self):
        self.data['Session']=list(fn.market_session(self.data.Candle_Session_Index, self.setting.instrument.tf))
    
    #Método para calcular el delta acumulado de cada día
    def get_cummulative_delta(self)-> None:
        self.data['CumDelta']=list(fn.candle_cummulative_delta(self.data.NewSession,self.data.Delta))
    
    #Método que calcula el volumen acumulado de la vela horaria
    def get_volume_h1(self)-> None:
        self.data['Vol_H1']=list(fn.candle_1h_volume(self.data.Time,self.data.Volume))

    #Método que calcula la mecha superior de la vela
    def get_shadow_upper(self)-> None:
        self.data['Shadow_Upper']=list(map(lambda candletype,copen,high,close: fn.candle_shadow_up(candletype,copen,high,close,self.setting.instrument.ticksize),
                                        self.data.Candle_Type, self.data.Open,self.data.High,self.data.Close))
        
    #Método que calcula la mecha superior de la vela 
    def get_shadow_lower(self)-> None:
        self.data['Shadow_Lower']=list(map(lambda candletype,copen,low,close: fn.candle_shadow_down(candletype,copen,low,close,self.setting.instrument.ticksize),
                                        self.data.Candle_Type, self.data.Open,self.data.Low,self.data.Close))

    # Método que calcula la relacion head/tail en %
    def get_head_tail(self)-> None:
        self.data['HT']=list(map(lambda shadow_upper,shadow_lower, candle_type: fn.candle_head_tail(shadow_upper,shadow_lower, candle_type),
                                self.data.Shadow_Upper,self.data.Shadow_Lower,self.data.Candle_Type))

    #Metódo que cuenta los días de mercado
    def get_market_days(self,_initial_market_day)-> None:
        self.data['Market_Day']=list(fn.count_market_days(self.data.NewSession,_initial_market_day))
        
        
    #Método que devuelve calcula si una vela es operable o no en funcion a la sesion de mercado y las limitaciones de las aperturas
    def get_tradeable(self):
        def checkTradeable(session, index) -> bool:
            if session == "Asia" and self.setting.timeconstraints.avoid_opening_asia != 0 and 0 <= index < self.setting.timeconstraints.avoid_opening_asia:
                return False
            elif session == "EU" and self.setting.timeconstraints.avoid_opening_eu != 0 and \
                 MARKET_SESSIONS_CANDLE_INDEX[self.setting.instrument.tf][0] <= index < MARKET_SESSIONS_CANDLE_INDEX[self.setting.instrument.tf][0] + self.setting.timeconstraints.avoid_opening_eu:
                return False
            elif session == "USA" and self.setting.timeconstraints.avoid_opening_usa != 0 and \
                 MARKET_SESSIONS_CANDLE_INDEX[self.setting.instrument.tf][1] <= index < MARKET_SESSIONS_CANDLE_INDEX[self.setting.instrument.tf][1] + self.setting.timeconstraints.avoid_opening_usa:
                return False
            elif session == "Overnigth":
                return False
            else:
                return True                    
        
        self.data['Tradeable']=list(map(lambda session,index: checkTradeable(session, index),
                                        self.data.Session,
                                        self.data.Candle_Session_Index))  
        
    #Método para calcular los indicadores
    def get_outchart_indicators(self)-> None:
        if 'cumdelta' in self.setting.indicators.indicators:
            self.get_cummulative_delta()
        if 'rsi' in self.setting.indicators.indicators:
            self.get_rsi(self.setting.indicators.rsi['period'])
        if 'atr' in self.setting.indicators.indicators:
            self.get_atr(self.setting.indicators.atr['period'])   
        if 'ar' in self.setting.indicators.indicators:
            self.get_ar(self.setting.indicators.atr['period'])
        if 'daily_change' in self.setting.indicators.indicators:
            self.get_daily_change()
        if 'tls' in self.setting.indicators.indicators or self.strategy_type == 'tls':
            self.get_trappedlongshort()
    #Método que calcula el Rango Medio de las ultimas _period velas
    def get_ar(self, period)-> None:
        self.data['AR']=[int(x) if math.isnan(x)==False else 1 for x in self.data.Range.rolling(window=period).mean()]

    #Método que calcula el ATR del perido seleccionado
    def get_atr(self,period)-> None:
        period = int(period)          # Forzamos que el periodo sea un entero
        self.data['TR']=list(fn.true_range(self.data.High,self.data.Low,self.data.Close,self.data.index,self.setting.instrument.ticksize))
        self.data['ATR']=0
        self.data.ATR.iat[period-1]=self.data.TR[1:period-1].mean()
        for i in range(period,len(self.data)):           
            self.data.ATR.iat[i]=(self.data.ATR.iat[i-1]*(period-1)+self.data.TR.iat[i])/period

    #Método que calcula el RSI 
    def get_rsi(self, period)-> None:     
        self.data['RSI']=fn.rsi(self.data.Close, int(period))


    # Método que calcula los parametros del  Trapped Long Short
    def get_trappedlongshort(self) -> None:
        # Mecha superior
        # Delta total
        self.data['TLS_Upper_Delta'] = list(map(lambda ask, bid,shadow_upper: 
                                                fn.shadow_delta(ask,bid,"upper",shadow_upper),
                                                self.data.Ask,self.data.Bid,self.data.Shadow_Upper))
        # Volumen total
        self.data['TLS_Upper_Volume'] = list(map(lambda ask, bid,shadow_lower:
                                                fn.shadow_volume(ask,bid,"upper",shadow_lower),
                                                self.data.Ask,self.data.Bid,self.data.Shadow_Lower))

        # Delta porcentual
        self.data['TLS_Upper_Ask_Percentage'] = list(map(lambda delta, volume: 
                                                    int(round((delta+volume)/(2 * volume) * 100,0)) if volume!=0 else 0,
                                                    self.data.TLS_Upper_Delta,self.data.TLS_Upper_Volume))
        # Porcentaje de niveles delta postivo en mecha superior
        self.data['TLS_Upper_Ask_Levels_Percentage'] = list(map(lambda ask, bid, shadow_upper:
                                                            fn.shadow_delta_levels_percentage(ask,bid,"upper",shadow_upper),
                                                            self.data.Ask,self.data.Bid,self.data.Shadow_Upper))

        #Precio en el que se da el máximo ask en la vela
        self.data['TLS_Max_Ask_Price'] = list(map(lambda ask, low:
                                                  fn.max_ask_price(ask,low,self.setting.instrument.ticksize),
                                                    self.data.Ask,self.data.Low))

        # Si el Max Ask Price esta en la mecha superior ponemos 1, si no 0
        self.data['TLS_Max_Ask_In_Upper_Shadow'] = list(map(lambda max_ask_price, open, close:
                                                            max_ask_price>close if open<close else max_ask_price>open,
                                                            self.data.TLS_Max_Ask_Price,self.data.Open,self.data.Close)) 

        # Mecha inferior
        # Delta total
        self.data['TLS_Lower_Delta'] = list(map(lambda ask, bid,shadow_lower:
                                                fn.shadow_delta(ask,bid,"lower",shadow_lower),
                                                self.data.Ask,self.data.Bid,self.data.Shadow_Lower))
        # Volumen total
        self.data['TLS_Lower_Volume'] = list(map(lambda ask, bid,shadow_lower:
                                                fn.shadow_volume(ask,bid,"lower",shadow_lower),
                                                self.data.Ask,self.data.Bid,self.data.Shadow_Lower))
        # Delta porcentual
        self.data['TLS_Lower_Bid_Percentage'] = list(map(lambda delta, volume:
                                                    int(round(((volume-delta) / (2*volume)) * 100,0)) if volume!=0 else 0,
                                                    self.data.TLS_Lower_Delta,self.data.TLS_Lower_Volume))
        # Porcentaje de niveles delta negativo en mecha inferior
        self.data['TLS_Lower_Bid_Levels_Percentage'] = list(map(lambda ask, bid, shadow_lower:
                                                            fn.shadow_delta_levels_percentage(ask,bid,"lower",shadow_lower),
                                                            self.data.Ask,self.data.Bid,self.data.Shadow_Lower))

        #Precio en el que se da el max bid en la vela
        self.data['TLS_Max_Bid_Price'] = list(map(lambda bid, low:
                                                    fn.max_bid_price(bid,low,self.setting.instrument.ticksize),
                                                    self.data.Bid,self.data.Low))


        # Si el Max Bid Price esta en la mecha inferior ponemos 1, si no 0
        self.data['TLS_Max_Bid_In_Lower_Shadow'] = list(map(lambda max_bid_price, open, close:
                                                            max_bid_price<close if open>close else max_bid_price<open,
                                                            self.data.TLS_Max_Bid_Price,self.data.Open,self.data.Close))

        # Comprobamos si se dan las condiciones de TLS. Si se dan ponemos 1 si hay largos atrapados, -1 si hay cortos, si no 0
        self.data['TLS_Result'] = list(
            map(
                lambda upper_delta, upper_ask_percentage, upper_ask_levels_percentage, max_ask_in_upper_shadow, lower_delta, lower_bid_percentage, lower_bid_levels_percentage, max_bid_in_lower_shadow, candle_type: 1
                if upper_delta >= self.setting.indicators.tls['upper_delta_min']
                and upper_ask_percentage>= self.setting.indicators.tls['upper_delta_percentage_min']
                and upper_ask_levels_percentage >= self.setting.indicators.tls['upper_delta_level_percentage_min']
                and (
                    self.setting.indicators.tls['max_delta_shadow'] == False
                    or max_ask_in_upper_shadow == 1
                )
                and (
                    self.setting.indicators.tls['concordance'] == False
                    or candle_type != -1
                )
                else -1
                if lower_delta <= self.setting.indicators.tls['lower_delta_max']
                and lower_bid_percentage >= self.setting.indicators.tls['lower_delta_percentage_min']
                and lower_bid_levels_percentage >= self.setting.indicators.tls['lower_delta_level_percentage_min']
                and (
                    self.setting.indicators.tls['max_delta_shadow'] == False
                    or max_bid_in_lower_shadow == 1
                )
                and (
                    self.setting.indicators.tls['concordance'] == False
                    or candle_type != 1
                )
                else 0,
                self.data.TLS_Upper_Delta,
                self.data.TLS_Upper_Ask_Percentage,
                self.data.TLS_Upper_Ask_Levels_Percentage,
                self.data.TLS_Max_Ask_In_Upper_Shadow,
                self.data.TLS_Lower_Delta,
                self.data.TLS_Lower_Bid_Percentage,
                self.data.TLS_Lower_Bid_Levels_Percentage,
                self.data.TLS_Max_Bid_In_Lower_Shadow,
                self.data.Candle_Type,
            )
        )
                                         



    #Metodo para lanzar el cálculo de todos los parámetros del bloque de datos de vela
    def calculate_candle_params(self,_initial_market_day)-> None:
        self.get_candle_type()        
        self.get_candle_session_index()
        self.get_range()
        self.get_body()   
        self.get_bodyrange_ratio()
        self.get_pullback()     
        self.get_mvc_percentage()
        self.get_mvc_gap()
        self.get_market_sessions()
        self.get_volume_h1()
        self.get_shadow_upper()
        self.get_shadow_lower()
        self.get_head_tail()
        self.get_market_days(_initial_market_day)
        self.get_relative_hour()
        self.get_tradeable()            
        

    def get_indicators(self) -> None:
        self.get_outchart_indicators()
        self.get_onchart_indicators()

#---- Bloque de metodos para la obtencion de niveles
    #Metodo para calcular los VWAP diario: Session, semanal: Week o mensual: Month
    def get_vwap(self,_type)-> None:     
        self.data[f'{_type}_VWAP']=list(fn.vwap(self.data[f'New{_type}'],self.data.Close,self.data.Volume,self.data.index,self.setting.instrument.digit))
       
    #Método que calculas los Máximos y Mínimo del día actual
    def get_current_day_levels(self)-> None:
        self.data['CD_High']=list(fn.current_day_level(self.data.NewSession, self.data.High,'High'))
        self.data['CD_Low']=list(fn.current_day_level(self.data.NewSession, self.data.Low,'Low'))

    #Método que calcula los Minimo, Maxímo y Cierre del día anterior
    def get_last_day_levels(self)-> None:
        self.data['LD_High']=list(fn.last_day_level(self.data.NewSession, self.data.CD_High)) 
        self.data['LD_Low']=list(fn.last_day_level(self.data.NewSession, self.data.CD_Low)) 
        self.data['LD_Close']=list(fn.last_day_level(self.data.NewSession,self.data.Close))            
        
    #Método que calcula los minimo y máximos del día actual divididos por sesiones de mercado
    def get_market_session_levels(self)->None:
        self.data['Asia_High']=list(fn.market_session_level(self.data.NewSession, self.data.High,self.data.Session,'High','Asia'))
        self.data['Asia_Low']=list(fn.market_session_level(self.data.NewSession, self.data.Low,self.data.Session,'Low','Asia'))
        self.data['EU_High']=list(fn.market_session_level(self.data.NewSession, self.data.High,self.data.Session,'High','EU'))
        self.data['EU_Low']=list(fn.market_session_level(self.data.NewSession, self.data.Low,self.data.Session,'Low','EU'))
        self.data['USA_High']=list(fn.market_session_level(self.data.NewSession, self.data.High,self.data.Session,'High','USA'))
        self.data['USA_Low']=list(fn.market_session_level(self.data.NewSession, self.data.Low,self.data.Session,'Low','USA'))

    #Método que calcula los Pivot Points y sus niveles R1,R2,R3 y S1,S2,S3
    def get_pivot_ponts(self)-> None:

        for level in ['PP','S1','S2','S3','R1','R2','R3']:
            self.data[level]=fn.pivot_points(self.data.LD_High,self.data.LD_Low,self.data.LD_Close,self.setting.instrument.digit,level)

          
    #Método que calcula el high o low de la ZCE que se le pida W o M
    def get_zce(self,_type,_level)-> None:
        _serie = self.data.NewWeek if _type=="W" else self.data.NewMonth
        self.data[f'ZCE_{_type}_{_level}']=list(fn.zce_level(_serie,self.data.Open,self.data.High,self.data.Low,self.data.Close,self.data.index,_level))

    #Método para calcula el High o Low de la ZCC del día que se pida
    def get_zcc(self,_num,_level)-> None:
        self.data[f'ZCC_{str(_num)}_{_level}']=list(fn.zcc_level(self.data.Time,self.data.NewSession,self.data.index,self.data.Open,
                                                    self.data.High,self.data.Low,self.data.Close,self.data.Vol_H1,_num,_level))
      
    # Método que calcula el indicador Daily Change
    def get_daily_change(self):
        if 'LD_Close' not in self.data.columns.to_list():
             self.data['LD_Close']=list(fn.last_day_level(self.data.NewSession,self.data.Close))
        self.data['Daily_Change'] = list(fn.daily_change(self.data.Close, self.data.LD_Close))


    #Método que repasa los niveles y pone un 1 si es tocado por la vela de toque
    #TODO: Rehacer este metodo

            
    #Método para calcular todos los niveles en bloque
    def get_onchart_indicators(self) -> None:
        def level_name_to_column(level_name):
            if level_name == "Pivot Point":
                return "PP"
            elif level_name == "Session VWAP":
                return "Session_VWAP"
            elif level_name == "Daily VWAP":
                return "Daily_VWAP"
            elif level_name == "Weekly VWAP":
                return "Weekly_VWAP"
            elif level_name == "LD_High" or level_name == "LD_Low" or level_name == "LD_Close":
                return level_name
            elif level_name == "Current Day Levels":
                return "CDL"
            elif level_name == "Market Session Levels":
                return "MSL"
            else:
                return level_name

        if len(self.setting.levels.levels) == 0:
            return
        for _level in self.setting.levels.levels:
            _level = level_name_to_column(_level)
            if _level=='Session_VWAP':
                self.get_vwap('Session')                
            elif _level=="Week_VWAP":
                self.get_vwap('Week')                
            elif _level=="Month_VWAP":
                self.get_vwap('Month')                
            elif _level=="CDL":
                if 'CD_High' not in self.data.columns:
                    self.get_current_day_levels()             
            elif _level=="LD_High" or _level=="LD_Low" or _level=="LD_Close":
                #Si no estan la columnas de niveles del dia actual las creamos
                if 'CD_High' not in self.data.columns:
                    self.get_current_day_levels()
                self.get_last_day_levels()
                #Si los niveles del día actual no esta en los niveles borramos las columnas creadas
                if 'CDL' not in self.setting.levels.levels:
                    self.data=self.data.drop(['CD_High','CD_Low'],axis=1)
            elif _level=="MSL":
                self.get_market_session_levels()
            elif _level=="ZCE_M":
                self.get_zce('M','High')
                self.get_zce('M','Low')                
            elif _level=="ZCE_W":
                self.get_zce('W','High')
                self.get_zce('W','Low')
            elif _level=="ZCC_H":
                if 'Vol_H1' not in self.data.columns:
                    self.get_volume_h1()
                for i in range(1,6):
                    self.get_zcc(i,'High')
                    self.get_zcc(i,'Low')
            elif _level=="PP":
                if 'LD_High' not in self.data.columns:
                    if 'CD_High' not in self.data.columns:
                        self.get_current_day_levels()
                        self.get_current_day_levels()
                    self.get_last_day_levels()
                    self.get_last_day_levels()
                    self.get_last_day_levels()
                    #Si los niveles del día actual no esta en los niveles borramos las columnas creadas
                    if 'CDL' not in self.setting.levels.levels:
                        self.data=self.data.drop(['CD_High','CD_Low'],axis=1)
                self.get_pivot_ponts()
                if 'LD_High' not in self.setting.levels.levels:
                    self.data=self.data.drop(['LD_High','LD_Low','LD_Close'],axis=1)
       

    
#---- Bloque de métodos para la gestion clase

    #Metodo que ejecuta la preparación del modelo segun las opciones elegidas en la configuracion
    def Calculate_Model(self,_initial_market_day=1)-> None:
        """ 
        Función que prepara el modelo para el posterior analisis en funcion de las opciones que se han seleccionado en la configuracion del modelo
        *Arg:  
              
        *Ret:
              - Nada pero actualiza el dataframe del modelo
        """
        #Calculamos primero el bloque de los datos relativos a las velas
        self.calculate_candle_params(_initial_market_day)
        
        # Calculamos los indicadores sobre el grafico
        self.get_onchart_indicators()

        # Calculamos los indicadores sobre el grafico
        self.get_outchart_indicators()









