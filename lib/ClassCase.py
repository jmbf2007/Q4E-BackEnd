import pandas as pd
from typing import List,Optional
import datetime as dt
import asyncio



from models.modelsSetting import Setting
from lib.ClassStrategyLogic import StrategyLogic
from lib.ClassLevel import cLevel
from lib.ClassOrder import Order
from lib.ClassPosition import Position
from lib.ClassResult import cResult
from lib.ClassCandle import Candle
from lib.ClassFilter import cFilter
from lib.ClassImpulse import Impulse
import lib.functions as fn


class cCase():
    data: pd.DataFrame                      # Dataframe con los valores de las velas
    m1data: pd.DataFrame                    # DataFrame con los High y Low de m1 para el análisis  fino 
    setting: Setting                        # Objeto Setting
    levels: Optional[List[cLevel]]          # Almacena la lista de niveles
    orders: Optional[List[dict]]            # Almacena las ordenes cerradas
    positions: Optional[List[dict]]         # Almacenas las posiciones cerradas
    result: Optional[cResult]               # Objeto result para los resultados
    position: Optional[Position]            # Para las positiones activas
    order: Optional[Order]                  # Para las ordenes activas
    candle: Optional[Candle]                # Objeto vela en análisis
    strategy_logic: StrategyLogic           # Objeto con la lógica de la estrategia          
    strategy_settings: Optional[dict]       # Diccionario con la configuracion de la estrategia
    last_impulse: Optional[Impulse]         # Ultimo impulso
    impulses: Optional[List[dict]]          # Lista de impulsos
    
    def __init__(self, data: pd.DataFrame, setting: dict, m1data: pd.DataFrame, tc_assumptions: dict, strategy_settings: dict, strategy_type: str): 
        self.data = data
        self.setting = Setting(data=setting)
        self.m1data = m1data
        self.levels = []
        self.orders = []
        self.positions = []
        self.strategy_settings = strategy_settings
        self.strategy_logic = StrategyLogic(setting=setting,
                                            tc_assumptions = tc_assumptions, 
                                            strategy_type= strategy_type)
        self.strategy_type = strategy_type


      
    async def check_period_market_days(self, initial_day: int, final_day: int) -> None:
        for day in range(initial_day, final_day):
            self.check_session(day)
            await asyncio.sleep(0)
      
      
    # Método que chequea un dia completo 
    def check_session(self,market_day: int) -> None:
        session_candles = self.data[self.data['Market_Day']==market_day]
        columns = ['Index']+ session_candles.columns.to_list()
        for row in session_candles.itertuples():
            self.check_new_candle(candle=Candle(row,columns))   
              
    # Método que evalua una nueva vela   
    def check_new_candle(self, candle: Candle):        


        # Actualizamos los parametros de la vela        
        self.candle = candle        

        # Buscamos nuevos niveles la informacion de los niveles
        self.update_new_levels()        

        # Actualizamos los indicadores
        self.update_indicators()

        # Si hay una posicion abierta
        if hasattr(self,'position') and self.position.active:
            self.check_position()
        
        # Si hay una orden en mercado
        elif hasattr(self,'order') and self.order.active:

            # Si se ha tocado
            if self.reached_order():
                self.open_new_position()
                self.check_position()                            
            else: 
                self.manage_order()
        
        #TODO Pensar bien el punto de decision de chequear una entrada despues de que una order en mercado que no ha sido activada
        else:
            self.check_new_entry()

        # Actualizamos los nivelesl tocados
        self.update_touched_levels()   

    

## ----------------- Indicadores ----------------- ##
    # Metodo que actualiza los indicadores
    def update_indicators(self) -> None:
        #TODO: Los indicadores se tendrían que actualizar en cada vela, ahora se calculan enteros en el Data
        # Si hay impulsos
        if 'zigzag' in self.setting.indicators.indicators:
            if not hasattr(self,'impulses'):
                self.start_impulses(self.candle)
            else:
                self.check_new_impulse()
        elif 'adx' in self.setting.indicators.indicators:
            self.check_new_ADX()

    # Métdo que inicia los impulsos
    def start_impulses(self, candle: Candle) -> None:
        self.impulses = []
        if candle.Close >= candle.Open:
            self.last_impulse = Impulse(
                initial=[candle.Time, candle.Low],
                final=[candle.Time, candle.High],
                direction=1,
                method=self.setting.indicators.zigzag['method']
            )
        else:
            self.last_impulse = Impulse(
                initial=[candle.Time, candle.High],
                final=[candle.Time, candle.Low],
                direction=-1,
                method=self.setting.indicators.zigzag['method']
            )

    # Metodo chequea un nuevo impulso
    def check_new_impulse(self) -> None:
        # Primero chequeamos si el impulso sigue activo y actualziamos los valores
        if self.setting.indicators.zigzag['method']=='Pullback Percentage':
            self.last_impulse.check_new_candle(self.candle.High, self.candle.Low, self.candle.Time, self.setting.indicators.zigzag['pullback_percentage'])
        elif self.setting.indicators.zigzag['method'] == 'Heiken Ashi':
            ha_close = (self.candle.Open + self.candle.High + self.candle.Low + self.candle.Close)/4
            previous_candle = self.data.iloc[self.candle.Index-1]
            ha_open = (previous_candle.Open + previous_candle.Close)/2
            self.last_impulse.check_new_candle(
                high = self.candle.High, 
                low = self.candle.Low, 
                time = self.candle.Time, 
                ha_close = ha_close, 
                ha_open = ha_open
            )
        if self.last_impulse.last:
            self.close_impulse()
 
    def close_impulse(self):
        self.impulses.append(self.last_impulse.to_dict())
        if self.last_impulse.direction == 1:    
            self.last_impulse = Impulse(                            # Creamos el nuevo impulso
                initial=self.last_impulse.final,                    # El punto inicial es el final del impulso anterior
                final=[self.candle.Time,self.candle.Low],           # El punto final es el máximo del pullback
                direction = -1,                                     # El nuevo impulso es bajista
                method=self.setting.indicators.zigzag['method']     # El método de cierre es el mismo que el de apertura
            )
        else:
            self.last_impulse = Impulse(                            # Creamos el nuevo impulso
                initial=self.last_impulse.final,                    # El punto inicial es el final del impulso anterior
                final=[self.candle.Time,self.candle.High],          # El punto final es el mínimo del pullback
                direction = 1,                                      # El nuevo impulso es alcista
                method=self.setting.indicators.zigzag['method']     # El método de cierre es el mismo que el de apertura
            )

    # Metodo que chequea un nuevo ADX
    def check_new_ADX(self):
        pass
    
## ----------------- Niveles ----------------- ##
    #Método que actulizalos niveles
    def update_new_levels(self) -> None:
        # Las estrategias basadas en el retesto a un nivel tiene siempre un main level que será el que da la entrada: P.ej. DP
        # Actualziamos el nivel principal
        if hasattr(self.setting.levels,'main') and self.setting.levels.main is not None:
            if self.setting.levels.main=="DP":
                self.check_newDP(main=True)
            elif self.setting.levels.main=="Imbalance":
                self.check_newImbalances(main=True)
            elif self.setting.levels.main=="Session_VWAP_Gap":
                self.check_newVWAPGap(main=True, vwapType="Session")
            elif self.setting.levels.main=="Opening_Gap":
                self.check_newOpeningGap(main=True)
            
        
        # A todas las estrategias se le pueden añadir niveles adicionales que pueden ser o no filtros para la entradas
        # Actualziamos los niveles añadidos
        for level in self.setting.levels.levels:
            if level=="DP":
                self.check_newDP(main=False)
            elif level=="Imbalance":
                self.check_newImbalances(main=False)
            elif level=="Session_VWAP_Gap":
                self.check_newVWAPGap(main=False, vwapType="Session")
            elif level=="Opening_Gap":
                self.check_newOpeningGap(main=False)
            
    # Método que comprueba si una vela tiene DP
    def check_newDP(self, main:bool):

        if fn.dp(_open =self.candle.Open, 
                 _high = self.candle.High, 
                 _low = self.candle.Low, 
                 _close = self.candle.Close, 
                 _mvc = self.candle.MVC, 
                 _range_min = self.setting.strategyparameters.range_min,
                 _br_min = self.setting.strategyparameters.br_min,
                 _mvc_max = self.setting.strategyparameters.mvc_max if hasattr(self.setting.strategyparameters,'mvc_max') else 50,
                 _delta = self.candle.Delta, 
                 _delta_check = False, 
                 _ticksize = self.setting.instrument.ticksize):            
         
            self.levels.append(
                cLevel(level_type = "DP",
                       index= self.candle.Index,
                       price = self.candle.MVC,
                       start_time = self.candle.Time,
                       delta = self.candle.Delta,
                       volume = self.candle.Volume,
                       direction = "buy" if self.candle.Close > self.candle.Open  else "sell",
                       main= main
                )
            )

    # Método que actuliza los niveles ya tocados
    def update_touched_levels(self) -> None:
        for level in self.levels:
            if level.active and self.candle.Low <= level.price <= self.candle.High and self.candle.Index > level.index:
                level.active = False
                level.end_time = self.candle.Time
                level.interval = self.candle.Index - level.index
       
    # Metodo que cuenta el numero de nivels activos
    def active_levels(self)  -> int :
        return sum(1 if level.active else 0 for level in self.levels)
  
    # Método que comprueba si una vela tiene Imbalances
    def check_newImbalances(self, main:bool):
        pass
    
    # Método que devuelve los niveles como una lista de diccionarios para poder almacenarlos en la base datos    
    def levels_to_list(self) ->  list:
        return [level.to_dict() for level in self.levels]
    

    # Método que comprueba si hay gap de VWAP 
    def check_newVWAPGap(self, main:bool, vwapType: str):        
        if not self.candle.Newsession:
            return
        
        self.levels.append(
                cLevel(
                    level_type=f"{vwapType}_VWAP_Gap",
                    index= self.candle.Index,
                    price = self.data[f'{vwapType}_VWAP'].iat[self.candle.Index-1],
                    start_time= self.candle.Time,
                    delta = self.candle.Delta,
                    volume = self.candle.Volume,
                    direction= None,
                    main = main
                )
            )
        
    # Método que comprueba si hay gap de apertura
    def check_newOpeningGap(self, main:bool):
        if not self.candle.Newsession:
            return
        
        #Tomamos el cierre de la vela anterior
        lastclose = self.data['Close'].iat[self.candle.Index-1]
        gap = self.candle.Low - lastclose if self.candle.Open > lastclose else lastclose - self.candle.High

        if gap <=0:
            return

        # Hay niveles de Gap de apertura
        gapdirection = 1 if self.candle.Open > lastclose else -1
        for i in range(gap):
            self.levels.append(
                cLevel(
                    level_type="Opening_Gap",
                    index= self.candle.Index,
                    price = lastclose + gapdirection*self.setting.instrument.ticksize*(i+1),
                    start_time= self.candle.Time,
                    delta = self.candle.Delta,
                    volume = self.candle.Volume,
                    direction= None,
                    main=main,
                )
            )
   
## ----------------- Ordenes ----------------- ##
    # Metodo que realiza todos los preocesos para el chequeo de una posicion
    def check_position(self):
        self.update_profit_loss()        

        if self.reached_tpsl():
            if self.reached_both():
                self.fine_check("Both")
            elif self.one_candle_trade():
                self.fine_check("1Candle")
            else:    
                self.position.active = False
                self.position.trade_result = "win" if self.position.maxProfit>=self.position.tp else "loss"    


            if not self.position.active:
                self.close_position()
            else:
                self.manage_position()
        else:
            self.manage_position()   

        if hasattr(self.setting.trademanagement,'consecutive_trades') and self.setting.trademanagement.consecutive_trades:
            self.check_new_entry()
         
    # Metodo que comprueba si se ha alcanzado una orden
    def reached_order(self) -> bool:
        if 'market' in self.order.order_type:
            return True
  
        return self.candle.Low <= self.order.open_price <= self.candle.High
    
    # Método que actualiza las perdidas y ganancias de la posición
    def update_profit_loss(self):
        profit = (self.candle.High - self.position.open_price)/self.setting.instrument.ticksize if self.position.trade_type == "buy" else (self.position.open_price - self.candle.Low)/self.setting.instrument.ticksize
        loss = (self.position.open_price - self.candle.Low)/self.setting.instrument.ticksize if self.position.trade_type == "buy" else (self.candle.High - self.position.open_price)/self.setting.instrument.ticksize

        self.position.maxProfit = max(profit, self.position.maxProfit)
        self.position.maxLoss = max(loss, self.position.maxLoss)
          
    # Devuelve True se alcanza el TP or SL
    def reached_tpsl(self) -> bool:
        #print(f'Position: {self.position.open_time} - MaxProfit: {self.position.maxProfit} - TP: {self.position.tp} - MaxLoss: {self.position.maxLoss} - SL: {self.position.sl}')
        return (self.position.maxProfit>=self.position.tp) or (self.position.maxLoss>=self.position.sl)
    
    # Devuelve True se alcanza el TP y SL a la vez en la misma vela
    def reached_both(self) -> bool:
        return (self.position.maxProfit>=self.position.tp) and (self.position.maxLoss>=self.position.sl)                                            
                                            
    # Devuelve True si el trade es de una sola vela
    def one_candle_trade(self) -> bool:
        return self.reached_tpsl() and self.position.open_time == self.candle.Time
          
    # Metodo que chequea en velas de 1m 
    def fine_check(self,text: str=None) -> None:

        tp_price = self.position.open_price + self.position.tp*self.setting.instrument.ticksize if self.position.trade_type == "buy" else self.position.open_price - self.position.tp*self.setting.instrument.ticksize
        sl_price = self.position.open_price - self.position.sl*self.setting.instrument.ticksize if self.position.trade_type == "buy" else self.position.open_price + self.position.sl*self.setting.instrument.ticksize                             

        actived, reached_tp, reached_sl = False, False, False
        activation_time = self.candle.Time
        for cont, (high, low, close) in enumerate(zip(self.get_m1_serie('High'), self.get_m1_serie('Low'), self.get_m1_serie('Close'))):
            if not actived:
                actived = low <= self.position.open_price <= high
                activation_time = self.candle.Time + dt.timedelta(minutes=cont)

            if actived:

                # Actualizamos los reached tp y sl
                if self.position.trade_type == "buy":                
                    reached_tp = high >= tp_price                 
                    reached_sl = low <= sl_price 
                else:
                    reached_tp = low <= tp_price                 
                    reached_sl = high >= sl_price

                if reached_tp or reached_sl:
                    close_time = self.candle.Time + dt.timedelta(minutes=cont)
                    if reached_tp and reached_sl:                                   # Si activan los dos en la misma vela de 1m es duda
                        self.position.trade_result = "doubt"
                        self.position.active = False

                    elif close_time > activation_time or self.setting.trademanagement.entry_type not in ['LimitOrder', 'StopOrder']:      # Si la vela de activacion no es la toque o para entradas Market 
                        self.position.active = False                 
                        self.position.trade_result = "win" if reached_tp else "loss" 

                    elif self.setting.trademanagement.entry_type == 'LimitOrder':                       #Se alcanza la entrada y el TP o SL en la misma vela de 1m entradas Limit
                        self.limit_order_fine_check(reached_tp, reached_sl, close, tp_price)

                    else:
                        self.stop_order_fine_check(reached_tp, reached_sl, close, sl_price)             #Se alcanza la entrada y el TP o SL en la misma vela de 1m entradas Stop

                    if not self.position.active:
                        return

                if cont==self.setting.instrument.tf-1:                          # Hemos llegadoa a la ultima vela y La orden se activa pero no se tocan ti TP ni SL
                    self.position.maxProfit = self.position.maxLoss = 0 

    # Metodo que devuelve una serie en formato numpy.array del parametero m1 que se le pida
    def get_m1_serie(self, serie: str):
        return self.m1data[serie].loc[(self.m1data['Time']>=self.candle.Time) & (self.m1data['Time'] < self.candle.Time + dt.timedelta(minutes = self.setting.instrument.tf))].to_numpy()

    # Metodo que comprueba el fine check para ordenes tipo Limit
    def limit_order_fine_check(self, reached_tp: bool, reached_sl: bool, close, tp_price):
        if reached_sl:
            self.position.active = False
            self.position.trade_result = "loss"
        elif  (self.position.trade_type=="buy" and close >= tp_price) or (self.position.trade_type=="sell" and close <= tp_price):
            self.position.active = False
            self.position.trade_result = "win"       
        else:
            self.position.active = True  
    
    # Metodo que comprueba el fine check para ordenes tipo Stop
    def stop_order_fine_check(self,reached_tp: bool, reached_sl: bool, close, sl_price):
        if reached_tp:
            self.position.active = False
            self.position.trade_result = "win"
        elif  (self.position.trade_type=="buy" and close <= sl_price) or (self.position.trade_type=="sell" and close >= sl_price):
            self.position.active = False
            self.position.trade_result = "loss"       
        else:
            self.position.active = True  
  
    # Metodo que cierra la posicion 
    def close_position(self):  # sourcery skip: assign-if-exp, remove-redundant-if, switch
        # Cálculo de los parámetros 
        if not hasattr(self.position, 'close_time'):
            self.position.close_time = self.candle.Time 

        if self.position.trade_result =="win":
            if self.position.trade_type == "buy":
                self.position.close_price = self.position.open_price + self.position.tp * self.setting.instrument.ticksize
            else:  
                self.position.close_price = self.position.open_price - self.position.tp * self.setting.instrument.ticksize
            
            self.position.tick_result = self.position.tp

        elif self.position.trade_result == "loss":
            if self.position.trade_type == "buy":
                self.position.close_price = self.position.open_price - self.position.sl * self.setting.instrument.ticksize
            else:
                self.position.close_price = self.position.open_price + self.position.sl * self.setting.instrument.ticksize
            
            self.position.tick_result = -self.position.sl
        else:                       # Para los casos pwin, ploss, beven y doubt
            self.position.close_price = self.candle.Close
            if self.position.trade_result in ["doubt", "beven"]:
                self.position.tick_result = 0
            else :
                net_ticks = abs((self.position.close_price - self.position.open_price)/self.setting.instrument.ticksize)
                self.position.tick_result = net_ticks if self.position.trade_result=="pwin" else -net_ticks

        self.position.cash_result = self.position.tick_result*self.position.size*self.setting.instrument.tickvalue - self.setting.account.fee*self.position.size 
        self.position.duration =  int((self.position.close_time - self.position.open_time + dt.timedelta(minutes = self.setting.instrument.tf)).total_seconds()/60)

        # Almacenamos la posicion cerrada en la lista
        self.positions.append(self.position.to_dict())

        # Borramos la posicion
        del self.position
        
    # Metodo que gestiona una posicion abierta que no se ha tocado ni el TP si SL    
    def manage_position(self): 
        # Si es superado el tiempo máximo de la posicion o estamos en la ultima vela de la session cerramos la posicion
        timelimit = 22*60+10        # tiempo limite para cerrar las operaciones que no tienen overnight. 22h10min. Es relativo al inicio de la session
        if (int((self.candle.Time - self.position.open_time + dt.timedelta(minutes = self.setting.instrument.tf)).total_seconds()/60) >= self.setting.timeconstraints.duration) or \
            ((self.candle.Relative_Hour*60 + self.candle.TimeMinutes) >= timelimit):       
            if self.position.open_price == self.candle.Close:
                self.position.trade_result = "beven"
            elif self.position.trade_type == "buy":
                if self.candle.Close > self.position.open_price:
                    self.position.trade_result = "pwin"
                else:
                    self.position.trade_result = "ploss"
            elif self.position.trade_type == "sell":
                if self.candle.Close < self.position.open_price:
                    self.position.trade_result = "pwin"
                else:
                    self.position.trade_result = "ploss"              
            self.position.active = False
            self.close_position()
              
    # Metodo que crea una nueva posición en el mercado     
    def open_new_position(self) -> None:
        # Creamos el objeto position
        
        self.position = Position()
        self.position.newPosition(trade_type = "buy" if "buy" in self.order.order_type else "sell",
                                 open_time = self.candle.Time,
                                 open_price = self.order.open_price,
                                 size = self.order.size,
                                 tp = self.order.tp,
                                 sl = self.order.sl,
                                 tc = self.strategy_logic.tc[-1]['Index'],                      # Pasamos el indice la de vela de toque
                                 tc_list_index = self.strategy_logic.tc[-1]['tc_list_index'],   # Posicion que ocupa la tc en la lista de tc
                                 level_index = self.strategy_logic.tc[-1]['level_index'] if 'level_index' in self.strategy_logic.tc[-1].keys() else None,        # Indice de la vela que genera el nivel de entrada si es una estrategia de niveles
                                 levels = self.get_levels_position_time(),                                                  # Diccionario con el valor de los niveles cuando entra la posicion
                                 relative_hour = self.strategy_logic.tc[-1]['Relative_Hour'],    # Hora relativa de la vela de toque  
                                 market_day = self.strategy_logic.tc[-1]['Market_Day'],         # Día de mercado de la vela de toque
                                 interval = self.strategy_logic.tc[-1]['Index'] - self.strategy_logic.tc[-1]['level_index'] if 'level_index' in self.strategy_logic.tc[-1].keys() else None ,     # Intervalo entre la vela de toque y la vela que origina el nivel
                                 interval_days = int(self.strategy_logic.tc[-1]['Market_Day'] - self.data.Market_Day[self.strategy_logic.tc[-1]['level_index']]) if 'level_index' in self.strategy_logic.tc[-1].keys() else None# Diferencia de dias de mercado entre la vela de toque y la vela que origina el nivel

        )
        

        self.close_order("entry")
    


    # Metodo que devuelve un diccionario con los valores de los niveles (si los hay) en el precio de la posicion
    def get_levels_position_time(self):
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

        levels_position = {}
        for level in self.setting.levels.levels:
            level = level_name_to_column(level)
            if level == "PP":
                for pplevel in ['PP','S1','S2','S3','R1','R2','R3']:
                    levels_position[pplevel] = self.data[pplevel][self.strategy_logic.tc[-1]['Index']]

            else:
                levels_position[level] = self.data[level][self.strategy_logic.tc[-1]['Index']]

        return levels_position

    # Metodo que abre una orden
    def open_new_order(self) -> None:
        if self.strategy_logic.orders[-1] is not None:
            self.order = Order()
            self.order.newOrder(order_type= self.strategy_logic.orders[-1]['order_type'],
                                open_price = self.strategy_logic.orders[-1]['open_price'],
                                open_time  = self.strategy_logic.orders[-1]['open_time'],
                                size = self.strategy_logic.orders[-1]['size'],
                                tp = self.strategy_logic.orders[-1]['tp'],
                                sl = self.strategy_logic.orders[-1]['sl'],
            )
            self.order.active = True
            
        if self.order.order_type == "ExceededRisk":
            self.close_order('canceled')
                                  
    # Método que cierra una order
    def close_order(self, action: str) -> None:
        #Actualziamos y almacenamos los datos de la order y eliminamos el objeto
        self.order.active = False
        self.order.action = action
        self.order.close_time = self.candle.Time 
        
        self.orders.append(self.order.to_dict())
        
        del self.order
        
    # Metodo que gestiona una orden que ya está puesta
    def manage_order(self)  -> None:
        wait_minutes = (self.setting.trademanagement.wait_candles-1) * self.setting.instrument.tf if hasattr(self.setting.trademanagement,'wait_candles') else 0
        if self.candle.Time >= self.order.open_time + dt.timedelta(minutes = wait_minutes):
            self.close_order("canceled")
                      
    # Metodo que comprueba si se dan las condiciones para una nueva entrada
    def check_new_entry(self) -> None:       
        # Buscmaos entrada
        if self.strategy_logic.checkLogic(self.candle, levels = self.filter_active_main_levels()):            
            self.open_new_order()
        
    # Méteodo que comprueba si la vela es operable
    def check_tradeable_candle(self):
        return self.setting.timeconstraints.min_hour <= self.candle.Relative_Hour <= self.setting.timeconstraints.max_hour

    #Método que crea un objeto result
    def get_result(self):
        # Result lo generamos a traves de filter
        self.filter = cFilter(setting = self.setting.to_dict(), 
                              data_candle = self.data.to_dict(orient='index'),
                              tc = self.strategy_logic.tc if hasattr(self.strategy_logic, "tc") else None,
                              strategy_settings = self.strategy_settings,
                              strategy_type = self.strategy_type
                    )

        self.filter.filter_case = self.positions
        self.filter.get_filter_result()
        
    # Método que devuelve una lista de los datos de los niveles principales que quedan activos
    def filter_active_main_levels(self) -> list:
        return [{'price': level.price, 'direction': level.direction, 'index': level.index}  for level in self.levels if level.main and level.active] 

    # Método que devuelve el tipo de orden que se ha activado
    def set_order_type(self) -> str:
        if self.setting.trademanagement.entry_type == "Auto":
            return self.auto_order_type()
        elif self.setting.trademanagement.entry_type == "Invert":
            return self.invert_order_type()
        #print(f"{self.strategy_logic.tc[self.strategy_logic.tc_entry]['Direction']}  {self.setting.trademanagement.entry_type.replace('Order','')}")
        return self.strategy_logic.tc[self.strategy_logic.tc_entry]['Direction'] + self.setting.trademanagement.entry_type.replace('Order','')

    # Método que devuelve el tipo de entrada que se calcula de forma auto
    def auto_order_type(self):
        return self.strategy_logic.tc[self.strategy_logic.tc_entry]["auto_entry_type"]

    def invert_order_type(self):
        auto_entry = self.auto_order_type()
        if auto_entry == "buyMarket":
            return "sellMarket"     
        elif auto_entry == "sellMarket": 
            return "buyMarket"
        elif auto_entry == "buyStop":
            return "sellLimit"
        elif auto_entry == "sellStop":
            return "buyLimit"
        elif auto_entry == "buyLimit":
            return "sellStop"
        return "buyLimit"

    # Método que devuelve el precio al que se colaca la orden
    def set_order_price(self) -> float:
        if self.setting.trademanagement.entry_type == "LimitOrder":
            return self.candle.Close - self.setting.trademanagement.order_gap * self.setting.instrument.ticksize if self.strategy_logic.tc[self.strategy_logic.tc_entry]['Direction'] == "buy" else self.candle.Close + self.setting.trademanagement.order_gap * self.setting.instrument.ticksize

        elif self.setting.trademanagement.entry_type == "MarketOrder":
            return self.candle.Close
        
        elif self.setting.trademanagement.entry_type == "StopOrder":
            return self.candle.MVC + self.setting.trademanagement.order_gap * self.setting.instrument.ticksize if self.strategy_logic.tc[self.strategy_logic.tc_entry]['Direction'] == "buy" else  self.candle.MVC - self.setting.trademanagement.order_gap * self.setting.instrument.ticksize

        elif self.setting.trademanagement.entry_type in ["Auto","Invert"]:
            return self.strategy_logic.tc[self.strategy_logic.tc_entry]['auto_entry_price']
        

