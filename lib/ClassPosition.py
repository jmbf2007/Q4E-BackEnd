from typing import Optional, List
from datetime import datetime

class Position():
    
    trade_type:     Optional[str]               # buy o sell
    open_time:      Optional[datetime]          # Tiempo de apertura de la posicion
    open_price:     Optional[float]             # Precio de entrada de la posicion
    size:           Optional[int]               # Tamaño en lotes de la posicion. Lo ponemos aquí por si en un futuro se quieren hacer cierres parciales. Sería el tamaño de la posicion que aun esta activa
    tp:             Optional[int]               # Take Profit en ticks. Se pone aquí por si en futuro se quiere hacer algun tipo de gestion del trade tipo trailing stop
    sl:             Optional[int]               # Stop Loss en ticks. Se pone aquí por si en futuro se quiere hacer algun tipo de gestion del trade tipo trailing stop
    tc:             Optional[int]               # Indice de la vela de toque
    tc_list_index:  Optional[int]               # Posicion que ocupa la tc en la lista de tc
    level_index:    Optional[int]               # Indice de la vela del nivel que produce la entrada
    levels:         Optional[dict]              # Diccionario con el valor de niveles (si los hay) en el momento de la entrada
    maxProfit:      Optional[int]               # Mayor beneficio posible alcanzado por la posicion
    maxLoss:        Optional[int]               # Mayor peridida posible alcanzada por la posicion
    active:         Optional[bool]              # Indica si está activa aun
    close_time:     Optional[datetime]          # Lista con los tiempos de los cierres parciales
    close_price:    Optional[float]             # Lista con los precios de cierre parciales
    tick_result:    Optional[int]               # Balance en ticks de la posicion
    cash_result:    Optional[float]             # Balance en $ de la posicion
    trade_result:   Optional[str]               # Win, loss, partial win, partial loss o doubt
    duration:       Optional[int]               # Duracion en minutos del trade
    relative_hour:  Optional[int]               # Hora relativa de entrada de la posicion
    market_day:     Optional[int]               # Día de mercado de la posicion
    interval:       Optional[int]               # Intervalo de velas desde la vela que origina el nivel y la vela de toque dela posicion
    interval_days:  Optional[int]               # Intervalo de días de mercado entra la vela que orginal el nivel y la vela de toque de la posicion

   
    # Método  que crea una nueva posicion. No se usa el constructor __init__()      
    def newPosition(self, 
                    trade_type:str,
                    open_time: datetime, 
                    open_price: float, 
                    size: float, 
                    tp: int, 
                    sl: int, 
                    tc: int, 
                    tc_list_index: int, 
                    level_index: int,
                    levels: dict,
                    relative_hour: int,
                    market_day: int,
                    interval: int,
                    interval_days: int) -> None:
        self.trade_type = trade_type
        self.open_price = open_price
        self.open_time = open_time
        self.size = size
        self.tp = tp
        self.sl = sl
        self.tc = tc
        self.tc_list_index = tc_list_index
        self.level_index = level_index
        self.levels = levels
        self.maxProfit = 0
        self.maxLoss = 0
        self.active = True
        self.trade_result = ""
        self.relative_hour = relative_hour
        self.market_day = market_day
        self.interval = interval
        self.interval_days = interval_days

    # Método que devuelve el contenido del objeto position en forma de diccionario
    def to_dict(self) -> dict:
        return dict(self.__dict__.items())
    
    # Método que actualiza los datos del objeto desde un diccionario
    def from_dict(self, data: dict) -> None:
        self.__dict__.update(data)
      
    # Método que devuelve la informacion necesaria para el objeto result    
    def data_to_result(self):
        return {
            'trade_type': self.trade_type,
            'open_price': self.open_price,
            'open_time': self.open_time,
            'close_price': self.close_price,
            'close_time': self.close_time,
            'trade_result': self.trade_result,
            'tick_result': self.tick_result,
            'cash_result': self.cash_result,
            'tc_index': self.tc,
            'relative_hour': self.relative_hour,
            'market_day': self.market_day,
            'interval': self.interval,
            'interval_days': self.interval_days
        }
    
