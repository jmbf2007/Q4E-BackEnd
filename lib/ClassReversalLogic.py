from lib.ClassCandle import Candle
from lib.ClassTCCandle import TCCandle
from models.modelsSetting import Setting
from lib.ClassLogic import Logic
from lib.ClassOrder import Order
import math
import datetime as dt

class ReversalLogic(Logic):

    @classmethod
    def check_new_entry(cls, candle: Candle, tc_assumptions: dict, setting: Setting, tc_lenght: int) -> object:

        tc = TCCandle(index=candle.Index)
        for hypothesis,parameters in zip(list(tc_assumptions.keys()), list(tc_assumptions.values())):
            if parameters['param']=="Body":
                tc.get_body(candle.Body)
            elif parameters['param']=="BR":
                tc.get_br(candle.BR)
            elif parameters['param']=="HT":
                tc.get_ht(candle.HT)
            elif parameters['param']=="MVC_Gap":
                tc.get_mvc_gap(candle.MVC_Gap)
            elif parameters['param']=="Volume":
                tc.get_volume(candle.Volume)
            elif parameters['param']=="InvertDelta":
                tc.get_invertdelta(direction=candle.Candle_Type, delta=candle.Delta)
            elif parameters['param']=="Range":
                tc.get_range(candle.Range)
        
            # Evaluamos la condicion y la almacenamos
            tc.Assumptions.append({hypothesis : cls.apply_object_condition(setting,tc,parameters['param'],parameters['value'],parameters['logic'])})
        


        # True si se cumplen todas
        tc.Entry = bool(math.prod([list(hypotesis.values())[0] for hypotesis in tc.Assumptions]))

        # Aplicamos la restriccion del tiempo
        if not setting.timeconstraints.min_hour <= candle.Relative_Hour <= setting.timeconstraints.max_hour:
            tc.Entry = False

        tc.Direction = candle.Candle_Type
        tc.Market_Day = candle.Market_Day
        tc.Relative_Hour = candle.Relative_Hour
        tc.tc_list_index = tc_lenght


        # Si hay entrada almacenamos el resto de parametros y calulamos el nivel de entrada
        if tc.Entry:
            tc.Market_Day = candle.Market_Day
            tc.Relative_Hour = candle.Relative_Hour
            tc.get_rc_entry(close=candle.Close, 
                            extreme=candle.High if candle.Candle_Type == -1 else candle.Low,
                            ticksize=setting.instrument.ticksize, 
                            direction= candle.Candle_Type,
                            slmax = setting.trademanagement.slmax,
                            slmin = setting.trademanagement.slmin,
                            slippage=setting.trademanagement.slippage
            )
            tc.level_index = candle.Index       # Asignamos el level_index como la TC para funcionen los filtros de nivel
            tc.Interval = 0                     # Asignamos el intervalo a 0 para que no se apliquen los filtros de intervalo

        if tc.Entry:
            order = cls.set_order(candle, setting)
        return {'tc': tc, 'order': order if tc.Entry else None}


    @classmethod
    def set_order(cls, candle: Candle, setting: Setting) -> object:
        order = Order()
        order.newOrder(order_type=cls.set_order_type(setting, candle),
                       open_price= cls.set_order_price(setting, candle),
                       open_time = candle.Time + dt.timedelta(minutes = setting.instrument.tf),
                       size= setting.trademanagement.size,                       
        )

        tpsl = cls.set_tpsl(setting, candle, order.open_price)
        order.tp = tpsl['tp']
        order.sl = tpsl['sl']

        return order
    

    @staticmethod
    def set_order_type(setting: Setting, candle: Candle) -> str:
        if candle.Candle_Type == 1: 
            theorical_sl = int((candle.Close - candle.Low)/setting.instrument.ticksize) +1 + setting.trademanagement.slippage if hasattr(setting.trademanagement, "slippage") else 0
        else:
            theorical_sl = int((candle.High - candle.Close)/setting.instrument.ticksize)+1 + setting.trademanagement.slippage if hasattr(setting.trademanagement, "slippage") else 0
        
        if theorical_sl < setting.trademanagement.slmax:
            return "buyMarket" if candle.Candle_Type == 1 else "sellMarket"
        else:
            return "buyLimit" if candle.Candle_Type == 1 else "sellLimit"
        
    @staticmethod
    def set_order_price(setting: Setting, candle: Candle) -> float:
        if candle.Candle_Type == 1: 
            theorical_sl = int((candle.Close - candle.Low)/setting.instrument.ticksize) +1 + setting.trademanagement.slippage if hasattr(setting.trademanagement, "slippage") else 0
        else:
            theorical_sl = int((candle.High - candle.Close)/setting.instrument.ticksize)+1 + setting.trademanagement.slippage if hasattr(setting.trademanagement, "slippage") else 0

        if theorical_sl < setting.trademanagement.slmax:
            return candle.Close
        
        if candle.Candle_Type == 1:
            return candle.Low + (setting.trademanagement.slmax -(setting.trademanagement.slippage+1)) * setting.instrument.ticksize
        return candle.High + ((setting.trademanagement.slippage+1)-setting.trademanagement.slmax) * setting.instrument.ticksize
    
    @staticmethod
    def set_tpsl(setting: Setting, candle: Candle, order_price: float) -> dict:
        if candle.Candle_Type == 1: 
            theorical_sl = int((order_price - candle.Low)/setting.instrument.ticksize) +1 + setting.trademanagement.slippage if hasattr(setting.trademanagement, "slippage") else 0
        else:
            theorical_sl = int((candle.High - order_price)/setting.instrument.ticksize)+1 + setting.trademanagement.slippage if hasattr(setting.trademanagement, "slippage") else 0

        sl = min(theorical_sl, setting.trademanagement.slmax)

        return {'sl': sl,'tp': int(setting.trademanagement.ratio_tpsl * sl)}
    
