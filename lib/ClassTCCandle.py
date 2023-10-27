from typing import List,Optional


class TCCandle():
    
    Index:                      int                         # Indice de la vela
    Range:                      Optional[int]               # Rango de la vela 
    Body:                       Optional[int]               # Cuerpo de la vela
    Bounce:                     Optional[int]               # Numero de ticks de rebote del nivel
    BR:                         Optional[int]               # Relacion cuerpo/rango en %
    HT:                         Optional[int]               # Relacion Head/Tail en %
    MVC_Gap:                    Optional[int]               # Gap entre el MVC y el cuerpo de la vela
    Delta:                      Optional[int]               # Delta entre el MVC y el cuerpo de la vela
    Volume:                     Optional[int]               # Volumen de la vela
    Interval:                   Optional[int]               # Numero de velas desde el nivel a la de toque
    Delta_Convergence:          Optional[bool]              # True si hay convergencia entre el delta de la vela de toque y la direccion del nivel que toca
    Invert_Delta_Convergence:   Optional[bool]              # True si hay convergencia inversa entre el delta de la vela de toque y la direccion del nivel que toca
    CumDelta_Convergence:       Optional[bool]              # True si hay convergencia entre el delta acumulado de la vela de toque y la direccion del nivel que toca
    MVC_Percentage:             Optional[int]               # Posicion del MVC de la TC en %
    Assumptions:                Optional[List[dict]]        # Lista con el resultado de la evaluacion de cada una de las hipotesis de la estrategia
    Entry:                      Optional[bool]              # True si produce una orden de entrada
    Direction:                  Optional[str]               # Direccion de la entrada que provacaría la TC
    Market_Day:                 Optional[int]               # Dia de mercado de la TC
    Relative_Hour:              Optional[int]               # Hora relativa de la TC
    Session_VWAP:               Optional[float]             # VWAP de la sesion de la TC
    tc_list_index:              Optional[int]               # Posicion que ocupa la TC en la lista de TC
    level_index:                Optional[int]               # Indice de la vela que genera el nivel tocado
    touched_level:              Optional[List[dict]]        # Lista de diccionarios que contienen el nombre del nivel y un bool que indica si la tc toca cada nivel de las lista de niveles. Hay un elemento por cada nivel que se haya seleccionado
    Concordance:                Optional[bool]              # Indica si hay concordancia entre la vela de toque y el tipo de entrada
    auto_worstprice:            Optional[float]             # Para las entradas auto, indica el peor de los precios para una posible entrada: min {Low)level, Low)tc} o max { High)level, High(tc)}
    auto_classification:        Optional[str]               # Para las entradas auto indica la clasificacion de la entrada
    auto_entry_type:            Optional[str]               # Para las entradas auto indica el tipo de entrada
    auto_entry_price:           Optional[str]               # Para las entradas auto indica el precio de entrada
    auto_sl:                    Optional[int]               # Para las entradas auto indica el stop loss en ticks
    tc_entry:                   Optional[int]               # Posicion de la vela de toque en la lista de TC
    ATR:                        Optional[float]             # ATR de la vela de toque
    AR:                         Optional[float]             # AR de la vela de toque
    RSI:                        Optional[float]             # RSI de la vela de toque
    TLS_Upper_Delta:            Optional[int]               # Delta de la mecha superior de la vela de toque
    TLS_Upper_Ask_Percentage:   Optional[int]               # % de delta Ask en la mecha superior de la vela de toque
    TLS_Upper_Ask_Levels_Percentage: Optional[int]          # % de niveles con delta Ask en la mecha superior de la vela de toque respecto a los niveles
    TLS_Lower_Delta:            Optional[int]               # Delta de la mecha inferior de la vela de toque
    TLS_Lower_Bid_Percentage:   Optional[int]               # % de delta Bid en la mecha inferior de la vela de toque
    TLS_Lower_Bid_Levels_Percentage: Optional[int]          # % de niveles con delta Bid en la mecha inferior de la vela de toque respecto a los niveles
    TLS_Result:                Optional[int]                # Resultado de la evaluacion de la hipotesis de la TLS: 1 largos atrapados, -1 cortos atrapados, 0 no atrapados


    def __init__(self, index: int) -> None:
        self.Index = index    
        self.Assumptions = []    
        
    def to_dict(self) -> dict:
        return dict(self.__dict__.items())
    
    def from_dict(self, data: dict) -> None:
        self.__dict__.update(data)       
        
    # --- Métodos para la     
    # Método que calcula el rebote
    def get_bounce(self, tc_close: float, level:dict, ticksize: float) -> None:
        self.Bounce =  int((tc_close - level['price'])/ticksize if level['direction']=="buy" else (level['price']-tc_close)/ticksize)
    
    # Método que calcula el intervalo
    def get_interval(self, index) -> None:
        self.Interval = self.Index - index
            
    # Método que calcula si convergen el delta de la vela de toque y la direccion del nivel.
    def get_delta_convergence(self,direction: str, delta: int) -> None:    
        self.Delta_Convergence = (direction=="buy" and delta > 0) or (direction=="sell" and delta <0)

    # Método que calcula si convergen el delta acumulado de la vela de toque y la direccion del nivel.
    def get_cumdelta_convergence(self,direction: str, cumdelta: int) -> None:    
        self.CumDelta_Convergence = (direction=="buy" and cumdelta > 0) or (direction=="sell" and cumdelta <0)
        
    # Método que calcula el indice de la vela del nivel
    def get_level_index(self) -> None:
        self.level_index = self.Index - self.Interval

    # Metodo que asigna la concordancia
    def get_concordance(self, direction: str, candeltype: int) -> None:
        # True si la direccion del trade es compra y la tc es bajista o si la direccion es venta y la tc es alcista
        self.Concordance = (direction=="buy" and candeltype==-1) or (direction=="sell" and candeltype==1)


    # Metodos para tc tipo reversal
    def get_body(self, body: int) -> None:
        self.Body = body

    def get_br(self, br: int) -> None:
        self.BR = br

    def get_ht(self, ht: int) -> None:
        self.HT = ht
    
    def get_delta(self, delta: int) -> None:
        self.Delta = delta

    def get_mvc_gap(self, mvc_gap: int) -> None:
        self.MVC_Gap = mvc_gap

    def get_invertdelta(self, direction: str, delta: int) -> None:
        self.InvertDelta = (direction==1 and delta < 0) or (direction==-1 and delta >0)

    def get_volume(self, volume: int) -> None:
        self.Volume = volume

    def get_range(self, range: int) -> None:
        self.Range = range

    def set_session_vwap(self, vwap: float) -> None:
        self.Session_VWAP = vwap

    def set_ATR(self, atr: float) -> None:
        self.ATR = atr
    
    def set_AR(self, ar: float) -> None:
        self.AR = ar
    
    def set_RSI(self, rsi: float) -> None:
        self.RSI = rsi

    def set_TLS(self, upper_delta: int, upper_ask_percentage: int, upper_ask_levels_percentage: int, lower_delta: int, lower_bid_percentage: int, lower_bid_levels_percentage: int, result: int) -> None:
        self.TLS_Upper_Delta = upper_delta
        self.TLS_Upper_Ask_Percentage = upper_ask_percentage
        self.TLS_Upper_Ask_Levels_Percentage = upper_ask_levels_percentage
        self.TLS_Lower_Delta = lower_delta
        self.TLS_Lower_Bid_Percentage = lower_bid_percentage
        self.TLS_Lower_Bid_Levels_Percentage = lower_bid_levels_percentage
        self.TLS_Result = result



    def get_rc_entry(self, close: float, extreme: float, ticksize: float, direction: int, slmax: int, slmin: int, slippage: int) -> None:
        theorical_sl = abs(round((close-extreme)/ticksize))+slippage+1
        if theorical_sl > slmax:
            if direction == -1:
                self.auto_entry_price = extreme + slippage*ticksize -slmax*ticksize
                self.auto_entry_type = "sellLimit"
                self.auto_sl = slmax
            elif direction == 1:
                self.auto_entry_price = extreme - slippage*ticksize +slmax*ticksize
                self.auto_entry_type = "buyLimit"
                self.auto_sl = slmax
        else:
            self.auto_entry_price = close
            self.auto_entry_type = "buyMarket" if direction == 1 else "sellMarket"
            self.auto_sl = max(theorical_sl, slmin)

    
