from typing import List,Optional
from lib.ClassLogic import Logic
from lib.ClassOrder import Order
from lib.ClassCandle import Candle
from lib.ClassTCCandle import TCCandle

class Reversal(Logic):

    Index:          int                     # Indice de la vela
    Body:           Optional[int]           # Cuerpo de la vela
    Range:          Optional[int]           # Rango de la vela
    BR:             Optional[int]           # Relacion cuerpo/rango en %
    HT:             Optional[int]           # Relacion Head/Tail en %
    Gap:            Optional[int]           # Gap entre el MVC y el cuerpo de la vela
    Volume:         Optional[int]           # Volumen de la vela
    Direction:      Optional[str]           # Direccion de la vela
    Market_Day:     Optional[int]           # Dia de mercado de la vela
    Relative_Hour:  Optional[int]           # Hora relativa de la vela
    Entry:          Optional[bool]          # True si produce una orden de entrada
    Assumptions:    Optional[List[dict]]    # Lista con el resultado de la evaluacion de cada una de las hipotesis de la estrategia
    entry_price:    Optional[float]         # Precio de entrada
    order_type:     Optional[str]           # Tipo de orden

    def __init__(self, index: int) -> None:
        self.Index = index    
        self.Assumptions = []
    
    def to_dict(self) -> dict:
        return dict(self.__dict__.items())
    
    def get_Range(self, range: int) -> None:
        self.Range = range
    
    def get_Body(self, body: int) -> None:
        self.Body = body

    def get_BR(self, br: int) -> None:
        self.BR = br

    def get_HT(self, lower_shadow: int, upper_shadow, direction: int) -> None:
        if direction == 1:
            self.HT = (upper_shadow/lower_shadow)*100
        elif direction == -1:
            self.HT = (lower_shadow/upper_shadow)*100
        elif direction == 0:
            self.HT = 0

    def get_Gap(self, open: float, mvc: float, ticksize:float, direction: int) -> None:
        if direction == 1:
            self.Gap = round((open-mvc)/ticksize-1)
        elif direction == -1:
            self.Gap = round((mvc-open)/ticksize-1)
        elif direction == 0:
            self.Gap = 0

    def get_Volume(self, volume: int) -> None:
        self.Volume = volume

    def get_Direction(self, direction: int) -> None:
        if direction == 1:
            self.Direction = "buy"
        elif direction == -1:
            self.Direction = "sell"
        elif direction == 0:
            self.Direction = "flat"
    
    def get_Market_Day(self, market_day: int) -> None:
        self.Market_Day = market_day
    
    def get_Relative_Hour(self, relative_hour: int) -> None:
        self.Relative_Hour = relative_hour

    
    def get_rc_entry_price(self, close: float, extreme: float, ticksize: float, direction: int, slmax: int, slippage: int) -> None:
        theorical_sl = abs(round((close-extreme)/ticksize))+slippage
        if theorical_sl > slmax:
            if direction == 1:
                self.entry_price = extreme - slippage*ticksize +slmax*ticksize
                self.order_type = "LimitOrder"
            elif direction == -1:
                self.entry_price = extreme + slippage*ticksize -slmax*ticksize
                self.order_type = "LimitOrder"
        else:
            self.entry_price = close
            self.order_type = "MarketOrder"

    

        




    


        
