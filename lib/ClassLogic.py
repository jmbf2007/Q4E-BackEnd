from models.modelsSetting import Setting
from lib.ClassOrder import Order
from lib.ClassCandle import Candle
from lib.ClassTCCandle import TCCandle
from abc import ABC, abstractmethod


class Logic(ABC):

    @staticmethod
    def apply_object_condition(setting: Setting, ob: object, param:str, value: str, logic: str) -> bool:
        # sourcery skip: remove-redundant-if 
        if logic == ">=":
            return ob.__dict__[param] >= setting.strategyparameters.__dict__[value]
        elif logic == "<=":
            return ob.__dict__[param] <= setting.strategyparameters.__dict__[value]
        elif logic == ">":
            return ob.__dict__[param] > setting.strategyparameters.__dict__[value]
        elif logic == "<":
            return ob.__dict__[param] < setting.strategyparameters.__dict__[value]
        elif logic == "=":
            return ob.__dict__[param] == setting.strategyparameters.__dict__[value]
        elif logic == "True" or True:        
            return ob.__dict__[param] if setting.strategyparameters.__dict__[value] else True

    
    @staticmethod
    def evaluate_indicator_tc(tc: TCCandle, indicator: str, setting: Setting) -> TCCandle:
        if indicator == "atr":
            tc.Assumptions.append({'ATR min': tc.ATR >= setting.indicators['atr']['min']})
            tc.Assumptions.append({'ATR max': tc.ATR <= setting.indicators['atr']['max']})
        elif indicator == "ar":
            tc.Assumptions.append({'AR min': tc.AR >= setting.indicators['ar']['min']})
            tc.Assumptions.append({'AR max': tc.AR <= setting.indicators['ar']['max']})
        elif indicator == "rsi":
            tc.Assumptions.append({'RSI min': tc.RSI >= setting.indicators['rsi']['min']})
            tc.Assumptions.append({'RSI max': tc.RSI <= setting.indicators['rsi']['max']})

        return tc
    
    @staticmethod
    def asign_indicator_tc(tc: TCCandle, candle: Candle, indicator: str) -> TCCandle:
        if indicator == "atr":
            tc.set_ATR(candle.ATR)
        elif indicator == "ar":
            tc.set_AR(candle.AR)
        elif indicator == "rsi":
            tc.set_RSI(candle.RSI)
        elif indicator == "tls":
            tc.set_TLS(candle.TLS_Upper_Delta, candle.TLS_Upper_Ask_Percentage, candle.TLS_Upper_Ask_Levels_Percentage, candle.TLS_Lower_Delta, candle.TLS_Lower_Bid_Percentage, candle.TLS_Lower_Bid_Levels_Percentage, candle.TLS_Result)

        return tc
    
    @abstractmethod    
    def set_order():
        pass

    @abstractmethod
    def check_new_entry():
        pass

    @classmethod
    def set_tpsl(cls, setting: Setting, candle: Candle, order: Order) -> dict:
        if hasattr(setting.trademanagement, "tp") and hasattr(setting.trademanagement, "sl"):
            tp = setting.trademanagement.tp 
            sl = setting.trademanagement.sl 
           
        elif hasattr(setting.trademanagement, "tp") and hasattr(setting.trademanagement, "ratio_tpsl"):
            tp = setting.trademanagement.tp
            sl = int(setting.trademanagement.tp / setting.trademanagement.ratio_tpsl) 

        elif hasattr(setting.trademanagement, "sl") and hasattr(setting.trademanagement, "ratio_tpsl"):
            tp = int(setting.trademanagement.sl * setting.trademanagement.ratio_tpsl) 
            sl = setting.trademanagement.sl 
        
        elif hasattr(setting.trademanagement, "ratio_tpsl") and hasattr(setting.trademanagement, "slmax") and hasattr(setting.trademanagement, "slmin"):
            if 'buy' in order.order_type: 
                theorical_sl = int((order.open_price - candle.Low)/setting.instrument.ticksize) +1 + setting.trademanagement.slippage if hasattr(setting.trademanagement, "slippage") else 0
            else:
                theorical_sl = int((candle.High - order.open_price)/setting.instrument.ticksize)+1 + setting.trademanagement.slippage if hasattr(setting.trademanagement, "slippage") else 0
            
            if theorical_sl < setting.trademanagement.slmin:
                tp = int(setting.trademanagement.slmin * setting.trademanagement.ratio_tpsl) 
                sl = setting.trademanagement.slmin
            
            elif theorical_sl > setting.trademanagement.slmax:
                tp = int(setting.trademanagement.slmax * setting.trademanagement.ratio_tpsl)
                sl = setting.trademanagement.slmax
            
            else:
                tp = int(theorical_sl * setting.trademanagement.ratio_tpsl)
                sl = theorical_sl
        
        return {'tp': tp, 'sl': sl}
