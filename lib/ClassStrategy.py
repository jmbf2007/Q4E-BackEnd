'''
15/10/21    v0.1.0     Incluido la opcion de rango horario para la operativa. De momento sólo para mostrar resultados. Falta implementarlo en la ejecucion del modelo
'''
#------------------------------
# Importamos librerias externas
#------------------------------
import pandas as pd
import datetime as dt
import numpy as np
#------------------------------
# Importamos Clases Propias
#-----------------------------
from lib.ClassData import cDataCandle
from lib.ClassResult import cResult
from lib.ClassFilter import cFilter

#------------------------------
# Clase
#------------------------------
class cStrategy():    
 
#---- Constructor
    def __init__(self, data: pd.DataFrame, setting: dict, tp=0, sl=0,load=False):

       
        # Atributo para el objeto data
        if not load:
            self.data = cDataCandle(data, setting)
            self.tp = self.data.setting.trademanagement.tp if tp == 0 else tp 
            self.sl = self.data.setting.trademanagement.sl if sl == 0 else sl
            # TODO: Comprobar si se puede eliminar la asignacion directa del tp y sl,  y hacerlo siempre via setting.trademanagent. Eso permitiría asignar dentro del Run_Case
            # Atributo para los filtros
            self.filter = cFilter(self.data.setting.to_dict(),self.tp, self.sl)

        
        # Atributos para la definicion de la estrategia
        self.lastcandle=int(self.data.setting.timeconstraints.duration/self.data.setting.instrument.tf)
       
#---- Bloque de funciones para el calculo de la entrada
    # Metodo para calcular las entradas conforme a los parámetros de rebote maximo y tipo de DP
    def Get_Entries(self):
        #Calculamos si la velas son operables o no        
        self.Get_Tradeable()              
        #Calculamos si la vela es un trade o no
        self.Get_Trade_Candle()
        #Calculamos el precio de entrada al trade en funcion al tipo de entrada a mercado que hallamos seleccionado    
        self.Get_Open_Price()
        #Calculamos los profit and loss despues de cada vela        
        self.Get_PL_After_Candle()

    #Método que calcula el precio de entrada al trade en función al tipo de entrada: entrada a mercado con o sin slippage, entrada Limit, entrada Stop
    def Get_Open_Price(self):
        if self.data.setting.trademanagement.entry_type=="MarketOrder":
            #El precio de entrada es el open de la vela siguiente a la de toque para los casos en que ST1 sea True    
            self.data.data['ST1_Open']=list(map(lambda st1,index: 
                                       (0 if st1==False  else (self.data.data['Open'].iat[index+1] if index < (len(self.data.data)-(self.lastcandle+1)) else 0)),
                                       self.data.data['ST1'],
                                       self.data.data['TC_Index']))
        elif self.data.setting.trademanagement.entry_type=="LimitOrder":
            #Implementar el código para poder entrar al mercado con ordenes limit
            def Limit_Order_Entry(_st1,_pullback_buy,_pullback_sell,_type,_close,_gap,_ticksize):
                if _st1==False:
                    return 0
                else:
                    if _type==1:                         
                        if _pullback_buy>=_gap:
                            return _close-_gap*_ticksize
                        else:
                            return 0
                    else:
                        if _pullback_sell>=_gap:
                            return _close+_gap*_ticksize
                        else:
                            return 0      

            self.data.data['ST1_Open'] = list(map(lambda st1,tc_index,candle_type,tc_close:
                                                  Limit_Order_Entry(st1,
                                                                    self.data.data['Pullback_Buy'].iloc[tc_index+1] if (tc_index+1)<len(self.data.data) else 1000,
                                                                    self.data.data['Pullback_Sell'].iloc[tc_index+1] if (tc_index+1)<len(self.data.data) else 1000,
                                                                    candle_type,
                                                                    tc_close,
                                                                    self.data.setting.trademanagement.order_gap,
                                                                    self.data.setting.instrument.ticksize),
                                                  self.data.data.ST1,
                                                  self.data.data.TC_Index,
                                                  self.data.data.Candle_Type,
                                                  self.data.data.TC_Close))

        elif self.data.setting.trademanagement.entry_type=="StopOrder":
            #Implementar el código para poder entrar al mercado con ordenes stop
            pass
        else:
            pass

    #Método que devuelve calcula si una vela es operable o no en funcion a la duracion maxima del trade y el cierre de session
    def Get_Tradeable(self):
        """
        Calculamos las velas que son operables para que no coja el cierre de mercado. 
        Para ello añadimos una columna que pondrá True todas las velas excepto las ultimas en funcion de la duracion
        """
        #Generator
        def Check_Tradeable(_new,_candles_session,_lastcandle):
            _tradeable=True
            _candle_num=1
            for _i,_n in enumerate(_new):
                if _i < (len(_new)- (_lastcandle+1)): 
                    if _n:
                        _candle_num=1
                    else:
                        _candle_num +=1
                        _tradeable = _candle_num <= _candles_session-(_lastcandle+1)
                else:
                    _tradeable=False
                yield _tradeable
        
        self.data.data['Tradeable']=list(Check_Tradeable(self.data.data.NewSession,self.Candles_per_Session(),self.lastcandle))  
        self.data.data['TC_Tradeable']=self.data.data.TC_Index.apply(lambda index: self.data.data['Tradeable'].iat[index] if index>0 else 0)

    #Metodo que calcula si es un trade o no en función al tipo de toque y rebote
    def Get_Trade_Candle(self):
     #Primero aplicamos las condiciones de los parámetros de la estrategia
        #Almacenamos True si el tipo de toque está catalogado como A, B o C y el rebote es menor el máximo permitido y la posicion del MVC de la TC >= que el min
        self.data.data['ST1']=list(map(lambda typeTC,bounce,tc_tradeable,tc_mvc,interval: 
            True if ((typeTC=="A" or typeTC=="B" or typeTC=="C") and \
                     (tc_mvc >= self.data.setting.strategyparameters.mvc_tc_min) and \
                     (bounce<self.data.setting.strategyparameters.bounce) and \
                     (tc_tradeable) and \
                     (interval >= self.data.setting.strategyparameters.interval_min)) else False,
            self.data.data['DP_TC_Type'],
            self.data.data['TC_Bounce'],
            self.data.data['TC_Tradeable'],
            self.data.data['TC_MVC%'],
            self.data.data['Interval']))
     # Si hay restricciones de indicadores se aplican los que han salido true en los parámetros de la estrategia
        #RSI
        if ('rsi' in self.data.setting.indicators.indicators) and (self.data.setting.indicators.rsi['included']):
            self.data.data['ST1']=list(map(lambda st1,type,tc_rsi: False if st1==False else 
                                            (True if (type==1 and tc_rsi<=self.data.setting.indicators.rsi['min']) or \
                                                     (type==-1 and tc_rsi>=self.data.setting.indicators.rsi['max']) else False),
                                            self.data.data.ST1,
                                            self.data.data.Candle_Type,
                                            self.data.data.TC_RSI))
        #ATR
        if ('atr' in self.data.setting.indicators.indicators) and (self.data.setting.indicators.atr['included']):
            self.data.data['ST1']=list(map(lambda st1,tc_atr: False if st1==False else 
                                            (True if tc_atr>=self.data.setting.indicators.atr['min'] else False),
                                            self.data.data.ST1,
                                            self.data.data.TC_ATR))
        #AR
        if ('ar' in self.data.setting.indicators.indicators) and (self.data.setting.indicators.ar['included']):
            self.data.data['ST1']=list(map(lambda st1,tc_ar: False if st1==False else 
                                            (True if tc_ar>=self.data.setting.indicators.ar['min'] else False),
                                            self.data.data.ST1,
                                            self.data.data.TC_AR))

    #Metodo que calcula como va la PL despues de n velas de la entrada. El numero de velas a calcular depende de la duracion del trade
    def Get_PL_After_Candle(self):
        self.data.data['ST1_PF0']=0
        self.data.data['ST1_LS0']=0
        for i in range(1,self.lastcandle+1):
            self.data.data['ST1_PF'+str(i)]=list(map(lambda dp,typeDP, index, opentrade, lastprofit, lastloss: 
                                                 self.Profit_Loss(self.data.setting.instrument.ticksize,
                                                                  opentrade,
                                                                  dp,
                                                                  typeDP,
                                                                  self.data.data['High'].iat[index+i] if index < (len(self.data.data)-i) else 0,
                                                                  self.data.data['Low'].iat[index+i] if index < (len(self.data.data)-i) else 0,
                                                                  "Profit",
                                                                  index,
                                                                  lastprofit,
                                                                  lastloss,
                                                                  len(self.data.data['Time']),
                                                                  i),
                                                 self.data.data['DP'],
                                                 self.data.data.Candle_Type,
                                                 self.data.data['TC_Index'],
                                                 self.data.data['ST1_Open'],
                                                 self.data.data['ST1_PF'+str(i-1)],
                                                 self.data.data['ST1_LS'+str(i-1)]))
            self.data.data['ST1_LS'+str(i)]=list(map(lambda dp,typeDP, index, opentrade, lastprofit, lastloss: 
                                                 self.Profit_Loss(self.data.setting.instrument.ticksize,
                                                                  opentrade,
                                                                  dp,
                                                                  typeDP,
                                                                  self.data.data['High'].iat[index+i] if index < (len(self.data.data)-i) else 0,
                                                                  self.data.data['Low'].iat[index+i] if index < (len(self.data.data)-i) else 0,
                                                                  "Loss",
                                                                  index,
                                                                  lastprofit,
                                                                  lastloss,
                                                                  len(self.data.data['Time']),
                                                                  i),
                                                 self.data.data['DP'],
                                                 self.data.data.Candle_Type,
                                                 self.data.data['TC_Index'],
                                                 self.data.data['ST1_Open'],
                                                 self.data.data['ST1_PF'+str(i-1)],
                                                 self.data.data['ST1_LS'+str(i-1)]))
        self.data.data=self.data.data.drop(['ST1_PF0','ST1_LS0'], axis=1) 

    #Metodo que calcula y devuelve los Profit o Loss de un trade
    def Profit_Loss(self,_ticksize,_level, _dp,_typeDP, _high, _low, _request, _index, _lastprofit, _lastloss, _length,_i):
        """
        *Arg:   _ticksize: Tamaño del tick 
                _level: precio de entrada del trade 
                _dp: 1 si es dp 0 si no lo es
                _typeDP: 1 dp alcista, -1 dp bajista
                _high:  High de la vela en evaluacion (va desde la entrada del trade a la ultima vela posible según la duración del trade)
                _low: Low de la vela en evaluacion (va desde la entrada del trade a la ultima vela posible según la duración del trade)
                _request: "Profit" o "Loss" según se pida
                _indice de la vela del DP
                _lastprofit: El profit de la vela anterior(va desde la entrada del trade a la ultima vela posible según la duración del trade)
                _lastloss: El loss de la vela anterior(va desde la entrada del trade a la ultima vela posible según la duración del trade)
                _length: Longitud de data set 
        *Ret: Devuelve el beneficio o perdida según se pida del trade en la vela i en ticks
        """
        #Si estamos al incio o al final del dataframe salimos
        if _index == (_length-1) or _index==0 :
            return 0
        #Si no es un DP salimos, que se da cuando _type==0 o cuando el nivel de entrada (opentrade) =0
        if _dp==0 or _level==0 :
            return 0
        #Calculamos loss y profit 
        if _typeDP==1:
            _loss = (_level - _low)/_ticksize
            _profit = (_high - _level)/_ticksize
        else:
            _loss = (_high - _level)/_ticksize
            _profit = (_level - _low)/_ticksize
        #Comprobamos si se superan los anteriores y actualizamos 
        if _lastloss > _loss:
            _loss = _lastloss
        if _lastprofit  > _profit:
            _profit = _lastprofit
        #Devolvemos el valor que se pida por request
        _value = _profit if _request=="Profit" else _loss
        return _value

    
        
#---- Bloque de funciones para calcular el modelo    
    #Metodo para correr el caso de estudio y obter el resultado
    def Run_Case(self,parametric=False):
        _range = self.data.setting.strategyparameters.range_min
        _br = self.data.setting.strategyparameters.br_min
        _bounce = self.data.setting.strategyparameters.bounce
        _tolerance = self.data.setting.strategyparameters.tolerance
        _mvc_dp = self.data.setting.strategyparameters.mvc_max
        _mvc_tc = self.data.setting.strategyparameters.mvc_tc_min
        _gap = self.data.setting.trademanagement.order_gap

        if parametric:
            self.Set_TPSL()
       
        #Hacemos una primera clasificacion de los trades        
        self.First_Clasification()
        
        #Chequeamos los dudosos primero por el método simplificado
        self.Simple_Check()                          
        
        #Chequeamos los dudosos en un time frame de 1min
        self.Fine_Check()

        #Calculamos el precio de cierre del trade
        self.Get_Close_Price()        
        
        #Calculamos el resultado en ticks
        self.Get_Tick_Result()
        
        #Actualizamos la columna TPSL con los ganados y perdidos parcialmente, que no han llegado ni al TP ni SL
        self.Update_Partial_Result()
        
        #Actualizamos la información de tiempos de trade
        self.Get_Time_Trades()

        #Chequeamos los que abren y cierran en la misma vela
        self.One_Candle_Trade_Check()

        #Creamos un objeto de la clase result con los resultados
        self.Create_Result_Object()

    def Set_TPSL(self):
        self.tp = self.data.setting.trademanagement.tp
        self.sl = self.data.setting.trademanagement.sl

    #Metodo que clasifica el trade en W(TP alcanzado) L(SL alcanzado) D(Duda , TP y SL se alcanzan en la misma vela) A(Activo, no llego ni a TP ni SL)
    def First_Clasification(self):
        #Método que asigna la primera clasificacion del trade
        def Get_TPSL(_tp,_sl, _profit, _loss):
            if _profit >=_tp and _loss < _sl:
                return "W"
            if _profit < _tp and _loss >= _sl:
                return "L"
            if _profit >= _tp and _loss >=_sl:
                return "D"
            if _profit < _tp and _loss < _sl:
                return "A"
            return "NP"  
        
        self.data.data['ST1_TPSL']=self.data.data['ST1'].apply(lambda x: "A" if x==True else "NT" )
        
 
        for i in range (1,self.lastcandle+1):
            if len(self.data.data[self.data.data['ST1_TPSL']=="A"])==0:
                break
            else:
                self.data.data['ST1_TPSL']=list(map(lambda tpsl,profit,loss:
                                          (Get_TPSL(self.tp,self.sl,profit,loss) if tpsl=="A" else tpsl),
                                           self.data.data['ST1_TPSL'],
                                           self.data.data['ST1_PF'+str(i)],
                                           self.data.data['ST1_LS'+str(i)]))
       
    #Métodos que chequean lo trades dudosos por el método simplificado
    def Simple_Check(self):
        self.data.data['ST1_TPSL']=list(map(lambda tpsl,index:
                                       self.Simple_Check_Doubt(int(index)) if tpsl=="D" else tpsl,
                                       self.data.data['ST1_TPSL'],
                                       self.data.data.index))     

    def Simple_Check_Doubt(self, _index,_initial=1):
        """
        Función que resuelve los casos dudosos por el método simplificado
        Se basa en ver los PF y LS de las primeras velas. 
        0) Primero verificamos la vela en la que se produce la duda: PF>TP y LS>SL. (i vela duda)
        1) Si PFi=PFi+1 y LSi<LSi+1 . Suponemos que el precio primero toco el TP y luego se alejó hacia el SL
        2) Si PFi<PFi+1 y LSi=LSi+1 . Suponemos que el precio primero tocó el SL y luego se alejó hacia el TP
        3) Si PFi=PFi+1 y LSi=LSi+1 . La duda persiste y hay que repetir incrementando i
        *Arg:  _index:   Indice absoluto de la vela DP que contiene el trade
               _initial: Vela a partir de la cual se inicia el chequeo. Normalmente es 1 pero puede ser distinta cuando se recalcula un trade
        *Ret: Devuevle el resultado del trade: W, L o D
        """
        i=_initial
        for k in range(1,self.lastcandle):
          if (self.data.data['ST1_PF'+str(k)].iat[_index]>=self.tp) and (self.data.data['ST1_LS'+str(i)].iat[_index]>self.sl):
            i=k
            break

        while i<(self.lastcandle-1):
              if (self.data.data['ST1_PF'+str(i)].iat[_index]!=self.data.data['ST1_PF'+str(i+1)].iat[_index]) and (self.data.data['ST1_LS'+str(i)].iat[_index]!=self.data.data['ST1_LS'+str(i+1)].iat[_index]):
                 i +=1
                 continue 
              if (self.data.data['ST1_PF'+str(i)].iat[_index]==self.data.data['ST1_PF'+str(i+1)].iat[_index]) and (self.data.data['ST1_LS'+str(i)].iat[_index]<self.data.data['ST1_LS'+str(i+1)].iat[_index]):
                 return "W"
              elif (self.data.data['ST1_PF'+str(i)].iat[_index]<self.data.data['ST1_PF'+str(i+1)].iat[_index]) and (self.data.data['ST1_LS'+str(i)].iat[_index]==self.data.data['ST1_LS'+str(i+1)].iat[_index]):
                 return "L" 
              else:
                 i +=1
        return "D"

    #Métodos que chequean los dudosos por en la resolución de 1m
    def Fine_Check(self):
        self.data.data['ST1_TPSL']=list(map(lambda tpsl,opentrade,index,typedp: 
                                      self.Check_Doubt(opentrade,typedp,self.data.data['Time'].iat[index+1]) if tpsl=="D" else tpsl,
                                      self.data.data['ST1_TPSL'],
                                      self.data.data['ST1_Open'],
                                      self.data.data['TC_Index'],
                                      self.data.data.Candle_Type))
        #Para no tener en cuenta  los dudosos que aun queden, ponemos a cero los precios de entrada de dudosos
        self.data.data['ST1_Open']=list(map(lambda tpsl,open: 0 if tpsl=="D" else open,
                                        self.data.data['ST1_TPSL'],
                                        self.data.data['ST1_Open']))

    #Método que chequea una vela concreta dudosa en resolucion de 1m
    def Check_Doubt(self,_open,_type,_start):
        """
        El método cheque el resultado de un trade dudoso en resolucion de 1m
        * Arg:  _open:   Precio de apetura de trade
                _type:   Tipo de trade Buy: 1, Sell: -1
                _start:  Tiempo de inicio del periodo a chequear
        * Ret:  Devuelve el resultado del trade: W, L o D
        """
        #Identificamos el periodo a analizar 
        
        if type(_start) is not dt.datetime:
            if type (_start).__module__==np.__name__:
                _start = dt.datetime.fromtimestamp(_start)
            else:
                _start=_start.to_pydatetime()
        _end=_start+dt.timedelta(minutes=self.lastcandle*self.data.setting.instrument.tf)

        '''
        if self.data.setting.instrument.data_source=="database":            
            _hl_data=DB.get_one_minute_data(self.data.setting.instrument.ticker, self.data.setting.instrument.start_date, self.data.setting.instrument.end_date)
            _hl_data = _hl_data[(_hl_data.Time>=_start) & (_hl_data.Time<_end)]
        else:
            #_hl_data=self.data.Get_Data_From_File(self.data.setting.instrument.ticker,1,_start,_end,True)
            pass
        
        '''
        
               
        _hlt_data = self.m1_data[(self.m1_data.Time>=_start) & (self.m1_data.Time<_end)]
        #_hl_data = np.array([_hlt_data['High'],_hlt_data['Low']],dtype=np.float32)   
        _hl_data = _hlt_data[['High','Low']]
            
        if len(_hl_data)==0:
            return "D"
        
        #Identificamos los precios objetivos
        _price_tp=_open+self.tp*self.data.setting.instrument.ticksize if _type==1 else _open-self.tp*self.data.setting.instrument.ticksize
        _price_sl=_open-self.sl*self.data.setting.instrument.ticksize if _type==1 else _open+self.sl*self.data.setting.instrument.ticksize
        _win=False
        _loss=False
        #Recorremos las velas de 1m
        for _high,_low in zip(_hl_data['High'],_hl_data['Low']):
            if _type==1:
                if _high >=_price_tp:
                    _win=True
                if _low <=_price_sl:
                    _loss=True
            else:
                if _high >=_price_sl:
                    _loss=True
                if _low <=_price_tp:
                    _win=True
            if _win and _loss:
                return "D"
            if _win:
                return "W"
            if _loss: 
                return "L"
        return "E"
 
    #Método que asigna el precio de cierre del trade en función del resultado
    def Get_Close_Price(self):
        #Método que devuelve el precio de cierre del trade en funcion al tipo
        def Get_Close(_tp,_sl,_ticksize,_tpsl,_typeDP,_close, _open):
            if _tpsl=="NT" or _tpsl=="D":
                return 0
            if _close==0 or _open==0:
                return 0
            if _tpsl=="W":
                if _typeDP==1:
                    return _open+(_tp*_ticksize)
                else:
                    return _open-(_tp*_ticksize)
            if _tpsl=="L":
                if _typeDP==1:
                    return _open-(_sl*_ticksize)
                else:
                    return _open+(_sl*_ticksize)
            return _close
        
        self.data.data['ST1_Close']=list(map(lambda tpsl, typeDP, index, opentrade:                     
                                        Get_Close(self.tp,
                                                       self.sl,
                                                       self.data.setting.instrument.ticksize,
                                                       tpsl,
                                                       typeDP,
                                                       (self.data.data['Close'].iat[index+self.lastcandle] if index < (len(self.data.data)-self.lastcandle) else 0),
                                                       opentrade),                                        
                                        self.data.data['ST1_TPSL'],
                                        self.data.data.Candle_Type,
                                        self.data.data['TC_Index'],
                                        self.data.data['ST1_Open']))   

    #Método que calcula el resultado del trade en ticks
    def Get_Tick_Result(self):
        #Metodo que devuelve el resultado de un trade en funcion del open y close. A los Doubt asigna un np.nan
        def Get_Result(_ticksize,_open,_close,_dp,_typedp,_tpsl):
            if _dp==0:
                return 0
            elif _tpsl=="D":
                return np.nan
            elif _typedp==1:
                return (_close-_open)/_ticksize 
            else:
                return (_open-_close)/_ticksize                                       
        self.data.data['ST1_Result']=0
        self.data.data['ST1_Result'] = list(map(lambda opentrade, closetrade, DP,typeDP, tpsl: 
                                        Get_Result(self.data.setting.instrument.ticksize,opentrade,closetrade,DP,typeDP,tpsl),
                                        self.data.data['ST1_Open'],
                                        self.data.data['ST1_Close'],
                                        self.data.data.DP,
                                        self.data.data.Candle_Type,
                                        self.data.data['ST1_TPSL']))

    #Metodo que actualiza la columna TPSL con los ganados y perdidos parcialmente, que no han llegado ni al TP ni SL
    def Update_Partial_Result(self):
        self.data.data['ST1_TPSL']=list(map(lambda tpsl, st1_result: 
                                       (tpsl if tpsl!="A" else ("BE" if st1_result==0 else ("PW" if st1_result>0 else "PL"))),
                                       self.data.data['ST1_TPSL'],
                                       self.data.data['ST1_Result']))

    #Método que chequea los trades de 1 vela
    def One_Candle_Trade_Check(self):
        # Si estamos en entrar a mercado no hay ese problema
        if self.data.setting.trademanagement.entry_type == "MarketOrder":
            return

        #Vamos a identificar los trades que se ejecutan en 1 sola vela (one candle trade oct)
        _oct=self.data.data[self.data.data.ST1_Open>0].copy()
        _oct=_oct[_oct.ST1_Open_Time == _oct.ST1_Close_Time]
        
        
        #Identificamos los potencialmente falsos positivos que se dan con las entradas tipo Order Limit
        if self.data.setting.trademanagement.entry_type == "LimitOrder":
            #Nos quedamos con los positivos
            _oct=_oct[_oct.ST1_Result>0]
            
            # Recorremos los trades e identificamos los potencialemente falsos positivos
            for _tc,_type,_tp,_open,_time,_index in zip(_oct.TC_Index,_oct.Candle_Type,_oct.ST1_Close,_oct.ST1_Open,_oct.TC_Time,_oct.index):               
                #Condición de potencial falso postivo para Sell. Que la vela del trade cierre por encima del TP
                _check_trade = False
                if _type == -1:
                    if self.data.data.Close.iat[_tc+1] > _tp:
                        _check_trade = True
                #Condición de potencial falso postivo para Buy. Que la vela del trade cierre por debajo del TP
                else:
                    if self.data.data.Close.iat[_tc+1] < _tp:
                        _check_trade = True
                
                if _check_trade:
                    _code = self.False_Result_Check(_time+dt.timedelta(minutes=self.data.setting.instrument.tf),_open,_tp,_type)
                    if _code == 1:
                        continue
                    elif _code == 2:
                        # Pasamos el resultado del trade a dudoso
                        self.Switch_Doubt(int(_index))
                    else:
                        # Invalidamos el cierre del trade. Chequeamos el resto de velas 
                        # Hay que volver a calcular los ST1_PF del trade ya que no son validos
                        self.data.data.ST1_PF1.iat[int(_index)]=0
                        for i in range(2,self.lastcandle+1):
                            self.data.data['ST1_PF'+str(i)].iat[int(_index)]=self.Profit_Loss(self.data.setting.instrument.ticksize, 
                                                                                         self.data.data.ST1_Open.iat[int(_index)],
                                                                                         1,
                                                                                         self.data.data.Candle_Type.iat[int(_index)],
                                                                                         self.data.data.High.iat[int(_tc)+i],
                                                                                         self.data.data.Low.iat[int(_tc)+i],
                                                                                         'Profit',
                                                                                         _index,
                                                                                         self.data.data['ST1_PF'+str(i-1)].iat[int(_index)],
                                                                                         0,
                                                                                         len(self.data.data),
                                                                                         i
                                                                                    )
                        
                        self.Recalculate_Trade(int(_index),_type)
        
        else:
            # Implementar los potenciales falso negativos en las entradas tipo Order Stop
            return

    #Método que recalcula el resultado resultado de un trade que ha sido Falso resultado
    def Recalculate_Trade(self, _index, _direction):        
        #Volvemos a calcular el resultado del trade a partir de la primera vela
        _result = "A"
        _candle = 1
        for i in range(2,self.lastcandle+1):
            if int(self.data.data['ST1_PF'+str(i)].iat[_index]) >= self.tp:
                _result = "W"
                _candle = i

            if int(self.data.data['ST1_LS'+str(i)].iat[_index]) >= self.sl:
                if _result == "W":
                    _result = "D"
                else:
                    _result = "L"
                    _candle = i
                    
            _pf = int(self.data.data['ST1_PF'+str(i)].iat[_index])
            _ls = int(self.data.data['ST1_LS'+str(i)].iat[_index])
            if _result != "A":
                break
        # Asignamos el nuevo resultado
        # Primero si es dudoso lo intentamos resolver por el metodo simplificado y si persiste lo calculamos de nuevo en resolución de 1m
        if _result == "D":            
            _result = self.Simple_Check_Doubt(_index,2)
        if _result == "D":
            _result = self.Check_Doubt(self.data.data.ST1_Open.iat[_index], self.data.data.Candle_Type.iat[_index],
                                       self.data.data.ST1_Open_Time.iat[_index] + dt.timedelta(minutes=self.data.setting.instrument.tf*(_candle-1)))

        if _result == "W":
            # El trade es ganador
            self.data.data.ST1_TPSL.iat[_index] = "W"
            self.data.data.ST1_Result.iat[_index] = self.tp
            self.data.data.ST1_Close_Time.iat[_index] = self.data.data.ST1_Open_Time.iat[_index] + dt.timedelta(minutes=self.data.setting.instrument.tf*(_candle-1))
            self.data.data.ST1_Close.iat[_index] = self.data.data.ST1_Open.iat[_index] + self.tp*self.data.setting.instrument.ticksize *_direction
        elif _result == "L":
            # El trade es perdedor
            self.data.data.ST1_TPSL.iat[_index] = "L"
            self.data.data.ST1_Result.iat[_index] = (-1)*self.sl
            self.data.data.ST1_Close_Time.iat[_index] = self.data.data.ST1_Open_Time.iat[_index] + dt.timedelta(minutes=self.data.setting.instrument.tf*(_candle-1))
            self.data.data.ST1_Close.iat[_index] = self.data.data.ST1_Open.iat[_index] - self.sl*self.data.setting.instrument.ticksize *_direction           
        elif _result == "A":
            # El trade sigue activo, tenemos un resultado parcial
            _partial_close = (self.data.data['Close'].iat[_index+self.lastcandle] if _index < (len(self.data.data)-self.lastcandle) else 0)
            if _partial_close !=0:
                self.data.data.ST1_Close.iat[_index]=_partial_close

                if _direction == 1:
                    self.data.data.ST1_Result.iat[_index] = (self.data.data.ST1_Close.iat[_index]-self.data.data.ST1_Open.iat[_index])/self.data.setting.instrument.ticksize
                else:
                    self.data.data.ST1_Result.iat[_index] = (self.data.data.ST1_Open.iat[_index]-self.data.data.ST1_Close.iat[_index])/self.data.setting.instrument.ticksize
                
                if self.data.data.ST1_Result.iat[_index] > 0:
                    self.data.data.ST1_TPSL.iat[_index] = "PW"
                    _result = "PW"
                elif self.data.data.ST1_Result.iat[_index] < 0:
                    self.data.data.ST1_TPSL.iat[_index] = "PL"
                    _result = "PL"
                else:
                    self.data.data.ST1_TPSL.iat[_index] = "BE"
                    _result = "BE"
                
                self.data.data.ST1_Close_Time.iat[_index] = self.data.data.Time.iat[_index+self.lastcandle]
            else:
                # Estamos en el extremo del rango de datos, el trade sigue activo al final del periodo de simulación. Los eliminamos y no lo consideramos para el analisis
                self.data.data.ST1_TPSL.iat[_index] = "NT"
                self.data.data.ST1_Result.iat[_index] = 0
                self.data.data.ST1_Close_Time.iat[_index] = 0
                self.data.data.ST1_Close.iat[_index] = 0
                self.data.data.ST1_Open.iat[_index] = 0
                self.data.data.ST1_Open_Time.iat[_index] = 0
                _result = "NT"
            
        elif _result == "D":
            # El trade siguie siendo dudoso, lo resolvemos por el metodo fino de 1m 
            self.data.data.ST1_TPSL.iat[_index] = "D"
            self.data.data.ST1_Result.iat[_index] = np.nan
            self.data.data.ST1_Close_Time.iat[_index] = self.data.data.ST1_Open_Time.iat[_index] + dt.timedelta(minutes=self.data.setting.instrument.tf*(_candle-1))
            self.data.data.ST1_Close.iat[_index] = 0

    # Método que cambia el resultado de un trade y lo pone como dudoso
    def Switch_Doubt(self, _index):
        #Ponemos a ST1_TPSL a D y a cero las columnas del trade
        self.data.data.ST1_TPSL.iat[int(_index)] = "D"
        self.data.data.ST1_Result.iat[int(_index)] = np.nan
        self.data.data.ST1_Open.iat[int(_index)] = self.data.data.ST1_Open_Time.iat[int(_index)] = self.data.data.ST1_Close.iat[int(_index)] = self.data.data.ST1_Close_Time.iat[int(_index)] = 0

    # Metodo que chequea un potencial falso resultado de un trade de 1 sola vela
    def False_Result_Check(self,_start, _order, _level,_direction,):
        #Identificamos el periodo a analizar
        _end=_start+dt.timedelta(minutes=self.data.setting.instrument.tf)
        
        # Capturamos el detalle de velas de 1m. Los parametros de fechas hay que pasarlos en formato str
        #_m1_data=self.data.Get_Query_Database(self.data.setting.instrument.ticker,1,_start.strftime('%Y-%m-%d %H:%M'),_end.strftime('%Y-%m-%d %H:%M'),True)
        #_m1_data = DB.get_one_minute_data(self.data.setting.instrument.ticker, self.data.setting.instrument.start_date, self.data.setting.instrument.end_date)
        _m1_data = self.m1_data[(self.m1_data.Time>=_start) & (self.m1_data.Time<_end)]
        
        #if len(_m1_data)>5:
        #    _m1_data=_m1_data.drop_duplicates()
            
        # Recorremos las velas y vemos si la orden limit se activa antes que el TP o no
        _order_touch = 0
        _level_touch = 0
        _close_check = False
        _candle = 0
        for _high,_low,_close in zip(_m1_data.High,_m1_data.Low,_m1_data.Close):
            _candle += 1
            if (_high >= _order) and (_low <= _order) and (_order_touch == 0):
                # Orden activada
                _order_touch = _candle
            if (_high >= _level) and (_low <= _level):
                # Nivel alcanzado
                _level_touch = _candle 
                # Comprobamos el cierre de la vela de 1m respecto del nivel
                if (_direction == -1 and _close <= _level) or (_direction == 1 and _close >= _level):
                    _close_check = True
        
        # Verificamos quien se toca antes. Tenemos tres posibles escenarios: Primero activa orden, Primero activa nivel o ambos se activan en la misma vela de 1min
        if _order_touch < _level_touch:
            # El trade es bueno 
            return 1
        elif _order_touch == _level_touch:
            if _close_check:
                # El trade es bueno
                return 1
            else:
                # El trade es dudoso 
                return 2
        else: 
            # Es falso resultado. El trade se ha activado por aun no se ha alcanzado el nivel hay que seguir chequeando el resto de velas para ver el resultado
            return 3

    #Metodo que crea un objeto de resultados
    def Create_Result_Object(self):
        """
        El objeto de resultado debe crearse con las filas con ST1=True y que el precio de entrada se distinto de cero para no incluir los
        trades que con Limit Order que al final no entran
        """
        # Primero seleccionamos los Trades
        _df=self.data.data[self.data.data['ST1']==True]

        
        # Despues los que tengan un precio de entrada >0 y reseteamos los indices
        _result_columns=['ST1_Result','TC_Market_Day','ST1_Close_Time','ST1_Open_Time','ST1_Close','ST1_Open','Candle_Type','TC_Relative_Hour']
        _df_result=_df[_result_columns].loc[(_df['ST1_Open']>0) & (_df.ST1_Close_Time!=0)].reset_index(drop=True)     
        
        #Creamos el objeto de resultado con los días de mercado 
        self.result=cResult(serie = _df_result.ST1_Result,
                            setting = self.data.setting.to_dict(),
                            market_day = _df_result.TC_Market_Day,
                            close_time = _df_result.ST1_Close_Time,
                            open_time = _df_result.ST1_Open_Time,
                            close_price = _df_result.ST1_Close,
                            open_price = _df_result.ST1_Open,
                            type = _df_result.Candle_Type,
                            relative_hour = _df_result.TC_Relative_Hour,
        )
        
    #Método que calcula la información de los trades
    def Get_Time_Trades(self):

       #La vela de entrada es la siguiente a la vela de toque 
        self.data.data['ST1_Open_Time']=self.data.data.TC_Time.apply(lambda tc_time: 0 if tc_time==0 else tc_time+dt.timedelta(minutes=self.data.setting.instrument.tf))

       #Calculamos el tiempo de salida con una función generator
        def Close_Time(_filter,duration,tf,tp,sl):
            close_time=dt.datetime.now()                                                #Iniciamos una variable tipo datetime que despues asigna
            for id,tpsl in zip(_filter.index,_filter.ST1_TPSL):
                open_time=_filter['ST1_Open_Time'].iat[int(id)]
                if tpsl=="NT":
                    close_time=0

                elif tpsl=="PL" or tpsl=="PW" or tpsl=="BE":
                    close_time=open_time+dt.timedelta(minutes=duration)

                elif tpsl=="W" or tpsl=="D":
                    for i in range(1,int(duration/tf)+1):
                        if _filter['ST1_PF'+str(i)].iat[int(id)]>=tp:
                            close_time=open_time+dt.timedelta(minutes=(i-1)*tf)     #La vela i=1 es la vela de entrada al trade
                            break
                elif tpsl=="L":
                    for i in range(1,int(duration/tf)+1):
                        if _filter['ST1_LS'+str(i)].iat[int(id)]>=sl:
                            close_time=open_time+dt.timedelta(minutes=(i-1)*tf)
                            break

                yield close_time
        
        self.data.data['ST1_Close_Time']=list(Close_Time(self.data.data,
                                                     self.data.setting.timeconstraints.duration,
                                                     self.data.setting.instrument.tf,
                                                     self.tp,
                                                     self.sl))
       
       #Hacemos la comprobación de multitrades para evitar abrir un trade si hay otro abierto
        self.Check_Multi_Trades()
    
       #Calculamos la duracion del trade en segundos
        self.data.data['ST1_Trade_Duration']=list(map(lambda close_time,open_time: 0 if close_time==0 else (close_time-open_time).total_seconds(),
                                                      self.data.data.ST1_Close_Time,
                                                      self.data.data.ST1_Open_Time))
                
    #Metodo que comprueba el multitrade. Si la opcion esta deshabilitada no permite mas de unas posicion abierta a la vez
    def Check_Multi_Trades(self):
        """
        Función que comprueba los operaciones multiples abiertas. Si la opción esta deshabilitada elimina las ordenes que se abren si ya hay una orden abierta
        Para ello recorre el dataframe de datos y busca la ordenes abiertas. Para el intervalo que hay desde el indice de la vela de toque menos las velas que 
        marcan la duracion del trade verificamos si hay trades. Si no hay trades en el intervalo no hay multitrades, si hay trades, se verifica si hay algun 
        tiempo de cierre mayor o igual al tiempo de apertura del trade.
        """
        #Si el multitrade está habilitado salimos
        if self.data.setting.timeconstraints.multitrade:
            return

        #Creamos la columna de salida
        self.data.data['ST1_Multitrade']=False

        #Filtramos el dataframe por el indice de la vela de toque
        tc_index_sorted = self.data.data[self.data.data['TC_Index']>0]
        tc_index_sorted = tc_index_sorted[tc_index_sorted['ST1_Open_Time']!=0].TC_Index.tolist()
        tc_index_sorted.sort()
        
        #Recorremos las velas de toque
        for i in tc_index_sorted:
            if (i-self.lastcandle)<0:
                continue
            #El tiempo de apertura del trade de la vela toque i 
            open_time_tc_i = self.data.data['ST1_Open_Time'].loc[self.data.data['TC_Index']==i].iat[0]
            if isinstance(open_time_tc_i,dt.datetime) == False:
                continue
       
            #Verificamos si hay velas en el intervalo de duracion de los trades
            for j in range(1,self.lastcandle+1):
                if (i-j) in tc_index_sorted:
                    #El tiempo de cierre del trade correspondiente a la vela de toque j
                    close_time_tc_j = self.data.data['ST1_Close_Time'].loc[self.data.data['TC_Index']==(i-j)].iat[0]
                    if isinstance(close_time_tc_j,dt.datetime) == False:
                        continue
                    #Si hay aun algun trade abierto o acaba de cerrar consideramos que se da multitrade y no seguimos buscando
                    if close_time_tc_j >= open_time_tc_i:
                        self.Set_Multitrade(i, True, loc=True)
                        break

 
        #Chequemos tambien cuando un vela de toque toca mas de un DP. En ese caso consideramos multitrades a todos 
        num_dp_touched_by_tc = {i:tc_index_sorted.count(i) for i in tc_index_sorted}
        tc_repeated = [x for x in list(num_dp_touched_by_tc.keys()) if num_dp_touched_by_tc[x]>1]

        for rp in tc_repeated:
            #Usamos un dataframe temporal filtrado por velas que toca el tc rp
            _temp = self.data.data[self.data.data['TC_Index']==rp]
            for rp_i in _temp.index:
                self.Set_Multitrade(rp_i, True, loc=False) 
                

        #Limipiamos las columnas de los multitrades
        num_trades_before = len(self.data.data[self.data.data['ST1_Open_Time']!=0])
        self.data.data['ST1_Open_Time'] = list(map(lambda op_tm,multi: (0 if multi else op_tm),
                                                    self.data.data.ST1_Open_Time,
                                                    self.data.data.ST1_Multitrade))
        self.data.data['ST1_Close_Time'] = list(map(lambda op_tm,cl_tm: (0 if op_tm==0 else cl_tm),
                                                    self.data.data.ST1_Open_Time,
                                                    self.data.data.ST1_Close_Time))   
        self.data.data['ST1_Open'] = list(map(lambda op_tm,op: (0 if op_tm==0 else op),
                                                    self.data.data.ST1_Open_Time,
                                                    self.data.data.ST1_Open))                                        
        self.data.data['ST1_Close'] = list(map(lambda op_tm,cl: (0 if op_tm==0 else cl),
                                                    self.data.data.ST1_Open_Time,
                                                    self.data.data.ST1_Close))
        self.data.data['ST1_Result'] = list(map(lambda op_tm,result: (0 if op_tm==0 else result),
                                                    self.data.data.ST1_Open_Time,
                                                    self.data.data.ST1_Result))
        num_trades_after = len(self.data.data[self.data.data['ST1_Open_Time']!=0])

    #Metodo para asignar un valor a Multitrade y que no de un warning por asignar en copia de dataframe. Es como una property
    def Set_Multitrade(self, index, value, loc=True):
        '''
        Hay dos opciones de asignación: directamente al indice de la vela del DP o mediante el indice de la vela de toque. 
        Para asignar mediante la vela de toque poner loc a True. Si se le pasa directemente el indice de la vela que contiene el dp hay que poner loc a False
        '''           
        if loc:
            self.data.data['ST1_Multitrade'].loc[self.data.data['TC_Index']==int(index)] = value
        else:
            self.data.data['ST1_Multitrade'].iloc[int(index)] = value

        
#---- Bloque de Properties    
    #Metodo para data
    def Set_Data(self,_value):
        self.data=_value
    
    #Métodos para asignar externamente tp 
    def Set_TP(self,_tp):
        self.tp=_tp
    
    #Métodos para asignar externamente sl
    def Set_SL(self,_sl):
        self.sl=_sl
    
    #Metodo para asignar externamente lastcandle
    def Set_Lastcandle(self,_value):
        self.lastcandle=_value

    #Método que devuelve el numero de velas que hay una session de mercado
    def Candles_per_Session(self):
        _first_loop=False
        for _candle in self.data.data['NewSession']:
            if _candle==True:
                if _first_loop==False:
                    _cont=1
                    _first_loop=True
                    continue
                else: 
                    return _cont
            else: 
                if _first_loop==False:
                    continue
                else:
                    _cont +=1
    

        #Generator
        def Sum_Cash_Balance(_data,_tpsl,_initial_balance,_tickvalue,_size):
            _cont=_initial_balance
            for r in _data:
                if ((_data!=np.nan) & (_tpsl!="D")):
                    _cont += r*_size*_tickvalue
                yield _cont
        self.data.data['Cash_Balance']=list(Sum_Cash_Balance(self.data.data.Result,self.data.data.TPSL,self.data.setting.account.initial_balance,self.data.setting.instrument.tickvalue,self.data.setting.account.size))


