from lib.ClassLogic import Logic
from typing import List,Optional
from lib.ClassCandle import Candle
from lib.ClassTCCandle import TCCandle
from models.modelsSetting import Setting
from lib.ClassOrder import Order
import datetime as dt

import math


class LevelTCLogic(Logic):

    @classmethod
    def check_new_entry(cls, candle: Candle, tc_assumptions: dict, setting: Setting, tc_lenght: int, levels: dict) -> dict:
        
        if not levels:
            return {'tc': None, 'order': None}

        # Inicializamos el contador de entradas ya que pueden tocarse varios niveles en la misma vela 
        entries = 0

        # Inicializamos la lista de ordenes ya que pueden tocarse varios niveles en la misma vela generar disitintas ordenes
        orders = []

        level_tc = None
        # Comprobamos si la vela es de toque        
        for level in levels:
            if candle.Index>level['index'] and candle.Low <= level['price'] <= candle.High:
                # Evaluamos la vela toque
                level_tc = cls.strategy_level_tc(candle, level, tc_assumptions, setting, tc_lenght)
                entries +=1 if level_tc.Entry else entries
                orders.append(cls.set_order(level=level, setting=setting, candle=candle))

        if entries > 1:
            # Si hay mas de una entrada seleccionamos la mejor
            return {'tc': level_tc, 'order': cls.set_best_entry(orders)}

        return {'tc': level_tc, 'order': orders[0] if entries == 1 else None}


    @classmethod
    def strategy_level_tc(cls, candle: Candle, level: dict, tc_assumptions: dict, setting: Setting, tc_lenght) -> object:
        tc = TCCandle(index=candle.Index)

        # Calculamos los parámetros de la vela de toque y evaluamos su condicion
        for hypothesis,parameters in zip(list(tc_assumptions.keys()), list(tc_assumptions.values())):
            if parameters['param']=="Bounce" and not hasattr(tc,"Bounce"):
                tc.get_bounce(tc_close=candle.Close,level=level,ticksize=setting.instrument.ticksize)
                
            elif parameters['param']=="Interval":
                tc.get_interval(index = level['index'])
                
            elif parameters['param']=="Delta_Convergence":
                tc.get_delta_convergence(direction=level['direction'], delta=candle.Delta)
                
            elif parameters['param']=="CumDelta_Convergence":
                tc.get_cumdelta_convergence(direction=level['direction'], cumdelta=candle.CumDelta)
                
            elif parameters['param']=="MVC_Percentage":
                tc.MVC_Percentage = candle.MVC_Percentage
            
            elif parameters['param']=="Concordance":
                tc.get_concordance(direction=level['direction'], candeltype=candle.Candle_Type)
        
            # Evaluamos la condicion y la almacenamos
            tc.Assumptions.append({hypothesis : cls.apply_object_condition(setting,tc,parameters['param'],parameters['value'],parameters['logic'])})

        
        # Aplicamos la restriccion del tiempo
        tc.Assumptions.append({'Time Constraints': setting.timeconstraints.min_hour <= candle.Relative_Hour <= setting.timeconstraints.max_hour })
            
        # Aplicamos la restriccion de niveles adicionales si los hay
        if len(setting.levels.levels)>0:
            tc.touched_level = []
            for lvl in setting.levels.levels:
                if setting.levels.__dict__[lvl]['included']:                                             # El nivel influye en la entrada
                    if setting.levels.__dict__[lvl]['buy_only_above'] and level['direction']=='buy':     # Solo esta permitida la compra por encima del nivel y la entrada es compra
                        tc.Assumptions.append({f'{lvl} Buy Only Above' : candle.Close > candle.__dict__[lvl]})

                    elif setting.levels.__dict__[lvl]['buy_only_below'] and level['direction']=='buy':   # Solo esta permitida la compra por debajo del nivel y la entrada es compra
                        tc.Assumptions.append({f'{lvl} Buy Only Below' : candle.Close < candle.__dict__[lvl]})

                    elif setting.levels.__dict__[lvl]['sell_only_above'] and level['direction']=='sell': # Solo esta permitida la venta por encima del nivel y la entrada es venta
                        tc.Assumptions.append({f'{lvl} Sell Only Above' : candle.Close > candle.__dict__[lvl]})                        

                    elif setting.levels.__dict__[lvl]['sell_only_below'] and level['direction']=='sell': # Solo esta permitida la venta por debajo del nivel y la entrada es venta
                        tc.Assumptions.append({f'{lvl} Sell Only Below' : candle.Close < candle.__dict__[lvl]})

                # Comprobamos la si el nivel es tocado por la vela
                tc.touched_level.append({lvl: candle.Low <= candle.__dict__[lvl] <= candle.High})

        
        # Aplicamos la restriccion de indicadores si los hay
        if len(setting.indicators.indicators)>0:
            for indicator in setting.indicators.indicators:
                # Primero asignamos el valor del indicador a la TC con el metodo asign_indicator de la clase padre Logic
                cls.asign_indicator_tc(tc=tc, candle=candle, indicator=indicator) 
                if setting.indicators.__dict__[indicator]['included']:                                             
                    tc = cls.evaluate_indicator_tc(tc=tc, candle=candle, indicator=indicator, setting=setting)  #El metodo pertence a la clase padre Logic
        
        # True si se cumplen todas
        tc.Entry = all(value for hypothesis in tc.Assumptions for value in hypothesis.values())


        tc.Direction = level["direction"]
        tc.Market_Day = candle.Market_Day
        tc.Relative_Hour = candle.Relative_Hour
        tc.level_index = level['index']
        tc.tc_list_index = tc_lenght
            
        return tc


    @staticmethod
    def set_best_entry(orders: List[object]) -> object:
        index = 0
        bestprice = orders[0].open_price
        if 'buy' in orders[0].order_type:
            for order in orders:
                if order.open_price < bestprice:
                    index = orders.index(order)
                    bestprice = order.open_price
        else:
            for order in orders:
                if order.open_price > bestprice:
                    index = orders.index(order)
                    bestprice = order.open_price

        return orders[index]

    # Metodo que abre una orden
    @classmethod
    def set_order(cls, setting: Setting, candle: Candle, level: dict) -> object:
        order = Order()
        order.newOrder(order_type= cls.set_order_type(setting=setting, candle=candle, level=level),
                       open_price = cls.set_order_price(setting=setting, candle=candle, level=level),
                       open_time  = candle.Time + dt.timedelta(minutes = setting.instrument.tf),
                       size = setting.trademanagement.size
        )
        if order.order_type == "ExceededRisk":
            return None
        
        tpsl = cls.set_tpsl(setting=setting, candle=candle, order=order)
        order.tp = tpsl['tp']
        order.sl = tpsl['sl']

        return order


    # Método que devuelve el tipo de orden que se ha activado
    @classmethod
    def set_order_type(cls, candle: Candle, setting: Setting, level: dict) -> str:
        if setting.trademanagement.entry_type == "Auto":
            return cls.auto_order_type(direction=level['direction'], 
                                       gap=setting.trademanagement.order_gap, 
                                       ticksize=setting.instrument.ticksize, 
                                       level=level['price'], 
                                       mvc=candle.MVC, 
                                       close=candle.Close, 
                                       slmax=setting.trademanagement.slmax)
        elif setting.trademanagement.entry_type == "Invert":
            return cls.invert_order_type(direction=level['direction'],
                                         gap=setting.trademanagement.order_gap,
                                         ticksize=setting.instrument.ticksize,
                                         level=level['price'],
                                         mvc=candle.MVC,
                                         close=candle.Close,
                                         slmax=setting.trademanagement.slmax)
        

        return level['direction'] + setting.trademanagement.entry_type.replace('Order','')
    

    # Método que devuelve el tipo de entrada que se calcula de forma auto
    @classmethod
    def auto_order_type(cls, direction: str, gap: float, ticksize: float, level: float, mvc: float, close: float, slmax: float) -> str:
        return cls.get_auto_order(direction, gap, ticksize, level, mvc, close, slmax)['auto_entry_type']

    @classmethod
    def invert_order_type(cls, direction: str, gap: float, ticksize: float, level: float, mvc: float, close: float, slmax: float) -> str:
        auto_entry = cls.auto_order_type(direction, gap, ticksize, level, mvc, close, slmax)['auto_entry_type']
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
    @classmethod
    def set_order_price(cls,candle: Candle, setting: Setting, level: dict) -> float:
        if setting.trademanagement.entry_type == "LimitOrder":
            return candle.Close - setting.trademanagement.order_gap * setting.instrument.ticksize if level['direction'] == "buy" else candle.Close + setting.trademanagement.order_gap * setting.instrument.ticksize

        elif setting.trademanagement.entry_type == "MarketOrder":
            return candle.Close

        elif setting.trademanagement.entry_type == "StopOrder":
            return candle.MVC + setting.trademanagement.order_gap * setting.instrument.ticksize if level['direction'] == "buy" else  candle.MVC - setting.trademanagement.order_gap * setting.instrument.ticksize

        elif setting.trademanagement.entry_type in ["Auto","Invert"]:
            return cls.auto_order_type(
                direction=level['direction'],
                gap=setting.trademanagement.order_gap,
                ticksize=setting.instrument.ticksize,
                level=level['price'],
                mvc=candle.MVC,
                close=candle.Close,
                slmax=setting.trademanagement.slmax,
            )['auto_entry_price']
        
    
    # Metodo que selecciona el tipo de entrada
    @classmethod
    def get_auto_order(cls,direction: str, gap: int, ticksize: float, level: float, mvc: float, close: float, slmax: int, tclow: float, tchigh: float) -> dict:
        # sourcery skip: merge-else-if-into-elif, move-assign-in-block
        auto_worstprice = min(level, tclow) if direction == "buy" else max(level, tchigh)
        if abs(level-auto_worstprice)/ticksize > slmax:
            return {'auto_entry_type': "ExceededRisk", 'auto_entry_price': 0} # Hay que asignarlo para que se genere el objeto order pero se elimina justo despues

        auto_classification = cls.get_auto_classification(level,mvc,close)

        if direction == "sell":
            if auto_classification in ["A1","B2" ,"E1"]:

                auto_entry_type = "sellStop"
                auto_entry_price = mvc - ticksize*gap
                if abs(auto_entry_price- auto_worstprice)/ticksize > slmax:
                    adj_dict = cls.adjust_entry(close,ticksize, slmax, direction, auto_worstprice)
                    auto_entry_type = adj_dict['auto_entry_type']
                    auto_entry_price = adj_dict['auto_entry_price']

            elif auto_classification in ["C1","C2","D2","F1","G"]:
                auto_entry_type = "sellStop"
                auto_entry_price = level - ticksize*gap      
                if abs(auto_entry_price-auto_worstprice)/ticksize > slmax:
                    adj_dict = cls.adjust_entry(close,ticksize, slmax, direction, auto_worstprice)
                    auto_entry_type = adj_dict['auto_entry_type']
                    auto_entry_price = adj_dict['auto_entry_price']      
            else:
                if abs(auto_worstprice - close)/ticksize <= slmax:
                    auto_entry_type = "sellMarket"
                    auto_entry_price = close
                else:
                    auto_entry_type = "sellLimit"
                    auto_entry_price = auto_worstprice - slmax*ticksize
        else:
            if  auto_classification in ["A1","A2","D1","E1","F2","G"]:
                auto_entry_type = "buyStop"
                auto_entry_price = level + gap * ticksize
                if abs(auto_entry_price - auto_worstprice)/ticksize > slmax:
                    adj_dict = cls.adjust_entry(close,ticksize, slmax, direction, auto_worstprice)

            elif  auto_classification in ["B1","C2","E2","F1"]:
                auto_entry_type = "buyStop"
                auto_entry_price = mvc + gap * ticksize
                if abs(auto_entry_price-auto_worstprice)/ticksize > slmax:
                    adj_dict  = cls.adjust_entry(close,ticksize, slmax, direction)
            else:
                if abs(auto_worstprice - close)/ticksize <= slmax:
                    auto_entry_type = "buyMarket"
                    auto_entry_price = close
                else:
                    auto_entry_type = "buyLimit"
                    auto_entry_price =  auto_worstprice + slmax*ticksize
        
        return {'auto_entry_type': auto_entry_type, 'auto_entry_price': auto_entry_price}

    
        # Método que clasifica la entrada automatica
    
    @staticmethod
    def get_auto_classification(level: float, mvc: float, close: float):
        if level > close > mvc:
            return "A1"
        elif level > mvc > close:
            return "A2"
        elif mvc > level > close:
            return "B1"
        elif close > level > mvc:
            return "B2"
        elif close > mvc > level:
            return "C1"
        elif mvc > close > level:
            return "C2"
        elif level==mvc and level > close:
            return "D1"
        elif level==mvc and level < close:
            return "D2"
        elif level==close and level > mvc:
            return "E1"
        elif level==close and level < mvc:
            return "E2"
        elif close==mvc and close > level:
            return "F1"
        elif close==mvc and close < level:
            return "F2"
        elif level==close==mvc:
            return "G"
        else:
            return "I"
        
    # Metodo que asigna el worst price de las tpsl automaticos
    def get_auto_worstprice(self, direction: str, level: float, tchigh: float, tclow: float) -> float:
        return min(level, tclow) if direction == "buy" else max(level, tchigh)
    

    @staticmethod
    def adjust_entry(close:float, ticksize: float, slmax: int, direction: str, auto_worstprice: float) -> dict:
        if abs(auto_worstprice - close)/ticksize <= slmax:
            auto_entry_type = f"{direction}Market"
            auto_entry_price = close
        else:
            auto_entry_type = f"{direction}Limit"
            auto_entry_price =  auto_worstprice + slmax*ticksize if direction=="buy" else auto_worstprice - slmax*ticksize
        
        return {'auto_entry_type': auto_entry_type, 'auto_entry_price': auto_entry_price}


    
