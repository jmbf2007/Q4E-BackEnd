#------------------------------
# Importamos librerias externas
#------------------------------
from dataclasses import dataclass
from typing import List, Optional
from pydantic import BaseModel

import sys

from lib.functions import daily_change
sys.path.append("..")


#------------------------------
# Clases
#------------------------------      
@dataclass     
class Instrument(BaseModel):
    
    ticker: Optional[str]
    tf: Optional[int]
    start_date: Optional[int]               # Se almacenará como timestamp
    end_date: Optional[int]                 # Se almacenará como timestamp
    ticksize: Optional[float]
    tickvalue: Optional[float]
    digit: Optional[int]
    data_source: Optional[str]
    
    def __init__(self, data: dict)-> None:
        self.__dict__.update(data)
   

@dataclass 
class Account(BaseModel):        
    initial_balance: Optional[float]
    trailing_dd: Optional[float]
    fee: Optional[float]    

    def __init__(self, data: dict)-> None:
        self.__dict__.update(data)

@dataclass        
class Indicators(BaseModel):
    
    indicators: Optional[List[str]]
    rsi: Optional[dict]
    atr: Optional[dict]
    ar: Optional[dict]
    daily_change: Optional[dict]
    zigzag: Optional[dict]
    
    
    def __init__(self, data: dict)-> None:
        self.__dict__.update(data)

                
@dataclass 
class TradeManagement(BaseModel):
    
    size: Optional[int]
    entry_type: Optional[str]
    slippage: Optional[int]
    order_gap: Optional[int]
    wait_candles: Optional[int]
    tp: Optional[int]
    sl: Optional[int]  
    consecutive_trades: Optional[bool]
    slmax: Optional[int]
    slmin: Optional[int]
    ratio_tpsl: Optional[float]
            
    def __init__(self, data: dict)-> None:
        self.__dict__.update(data)
        
@dataclass 
class TimeConstraints(BaseModel):
    duration: Optional[int]
    overnight: Optional[bool]
    multitrade: Optional[bool]
    min_hour: Optional[int]
    max_hour: Optional[int]
    avoid_opening_asia: Optional[int]
    avoid_opening_eu: Optional[int]
    avoid_opening_usa: Optional[int]

    def __init__(self, data: dict)-> None:
        self.__dict__.update(data)

@dataclass            
class Levels(BaseModel):       
    
    main:   Optional[str]                  # Nivel principal de la estrategia si la tiene. Este se chequea siempre. Ej. DP 
    levels: Optional[List[str]]            # Los niveles extras añadidos
    
    def __init__(self, data: dict)-> None:
        self.__dict__.update(data)
        

@dataclass     
class StrategyParameters(BaseModel):
    
    range_min: Optional[int]
    br_min: Optional[int]
    mvc_max: Optional[int]
    tolerance: Optional[int]
    bounce_min: Optional[int]               # Valores negativos implican que la tc cierra mas alla del nivel. 0 es cierre coincidente con el nivel
    bounce_max: Optional[int]               
    mvc_tc_min: Optional[int]
    interval_min: Optional[int]
    interval_max: Optional[int]
    tc_concordance: Optional[bool]
    mvc_gap: Optional[int]
    invertdelta: Optional[bool]
    
    def __init__(self, data: dict)-> None:
        self.__dict__.update(data)
                

class Setting():
    
    instrument = Optional[Instrument]
    account = Optional[Account]
    indicators = Optional[Indicators]
    trademanagement = Optional[TradeManagement]
    timeconstraints = Optional[TimeConstraints]
    levels = Optional[Levels]
    strategyparameters = Optional[StrategyParameters]
    
    def __init__(self, data: dict) -> None:      
        self.instrument =  Instrument(data['instrument'])
        self.account = Account(data['account'])
        self.indicators = Indicators(data['indicators'])
        self.trademanagement = TradeManagement(data['trademanagement'])
        self.timeconstraints = TimeConstraints(data['timeconstraints'])
        self.levels = Levels(data['levels'])
        self.strategyparameters = StrategyParameters(data['strategyparameters'])

    def to_dict(self):
        dicc1 = {}
        for attb1, val1 in self.__dict__.items():
            dicc2 = dict(val1.__dict__.items())
            dicc1[attb1] = dicc2
        return dicc1
    
    

    