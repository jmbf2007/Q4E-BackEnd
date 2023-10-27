from typing import Optional
from datetime import datetime


class Order():
    order_type:         Optional[str]               # "buy limit", "sell limit", "buy stop", "sell stop", "buy market", "sell market"
    open_time:          Optional[datetime]          # Tienmpo en el que se colaca la orden. Normalmente a la apertura de la siguiente vela desde pues de la cerrada
    open_price:         Optional[float]             # Precio en el que se coloca la orden para las ordenes limit y stop y el precio de cierre de la vela para las ordenes a mercado
    size:               Optional[int]               # Tamaño de la orden
    active:             Optional[bool]              # Estara a True siempre que la orden este sin tocar
    action:             Optional[str]               # La orden puede acabar en "entry" or "canceled"
    close_time:         Optional[datetime]          # Tiempo en el que cierra la orden
    tp:                 Optional[float]             # Precio de take profit
    sl:                 Optional[float]             # Precio de stop loss
    
    
    def newOrder(self, order_type: str, open_time: datetime, open_price: float, size: int, tp: float=None, sl: float=None) -> None:
        self.order_type = order_type
        self.open_time = open_time
        self.open_price = open_price
        self.size = size
        self.active = True
        if tp is not None:
            self.tp = tp
        if sl is not None:
            self.sl = sl
        

    def to_dict(self) -> dict:
        return dict(self.__dict__.items())
        