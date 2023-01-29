from typing import List,Optional


class TCCandle():
    
    Index:                      int                         # Indice de la vela 
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
    tc_list_index:              Optional[int]               # Posicion que ocupa la TC en la lista de TC
    level_index:                Optional[int]               # Indice de la vela que genera el nivel tocado
    Concordance:                Optional[bool]              # Indica si hay concordancia entre la vela de toque y el tipo de entrada
    auto_worstprice:            Optional[float]             # Para las entradas auto, indica el peor de los precios para una posible entrada: min {Low)level, Low)tc} o max { High)level, High(tc)}
    auto_classification:        Optional[str]               # Para las entradas auto indica la clasificacion de la entrada
    auto_entry_type:            Optional[str]               # Para las entradas auto indica el tipo de entrada
    auto_entry_price:           Optional[str]               # Para las entradas auto indica el precio de entrada
    auto_sl:                    Optional[int]               # Para las entradas auto indica el stop loss en ticks
    


    def __init__(self, index: int) -> None:
        self.Index = index    
        self.Assumptions = []    
        
    def to_dict(self) -> dict:
        return dict(self.__dict__.items())
    
    def from_dict(self, data: dict) -> None:
        self.__dict__.update(data)       
        
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


    # Metodo que asigna el worst price de las tpsl automaticos
    def get_auto_worstprice(self, direction: str, level: float, tchigh: float, tclow: float):
        self.auto_worstprice = min(level, tclow) if direction == "buy" else max(level, tchigh)

    # Método que clasifica la entrada automatica
    def get_auto_classification(self, level: float, mvc: float, close: float):
        if  level > close > mvc:
            self.auto_classification = "A1"     
        elif level > mvc > close:
            self.auto_classification = "A2"
        elif  mvc > level > close:
            self.auto_classification = "B1"
        elif close > level > mvc:
            self.auto_classification = "B2"
        elif close > mvc > level:
            self.auto_classification = "C1"
        elif mvc > close > level:
            self.auto_classification = "C2"
        elif level==mvc and level > close:
            self.auto_classification = "D1"
        elif level==mvc and level < close:
            self.auto_classification = "D2"
        elif level==close and level > mvc:
            self.auto_classification = "E1"
        elif level==close and level < mvc:
            self.auto_classification = "E2"
        elif close==mvc and close > level:
            self.auto_classification = "F1"
        elif close==mvc and close < level:
            self.auto_classification = "F2"
        elif level==close==mvc:
            self.auto_classification = "G"
        else:
            self.auto_classification = "I"
        
    # Metodo que selecciona el tipo de entrada
    def get_auto_entry_type(self, direction: str, gap: int, ticksize: float, level: float, mvc: float, close: float, slmax: int):
        if abs(level-self.auto_worstprice)/ticksize > slmax:
            self.auto_entry_type ="ExceededRisk"
            self.auto_entry_price = 0       # Hay que asignarlo para que se genere el objeto order pero se elimina justo despues
            return

        if direction == "sell":
            if self.auto_classification in ["A1","B2" ,"E1"]:

                self.auto_entry_type = "sellStop"
                self.auto_entry_price = mvc - ticksize*gap
                if abs(self.auto_entry_price-self.auto_worstprice)/ticksize > slmax:
                    self.adjust_entry(close,ticksize, slmax, direction)

            elif self.auto_classification in ["C1","C2","D2","F1","G"]:
                self.auto_entry_type = "sellStop"
                self.auto_entry_price = level - ticksize*gap      
                if abs(self.auto_entry_price-self.auto_worstprice)/ticksize > slmax:
                    self.adjust_entry(close,ticksize, slmax, direction)      
            else:
                if abs(self.auto_worstprice - close)/ticksize <= slmax:
                    self.auto_entry_type = "sellMarket"
                    self.auto_entry_price = close
                else:
                    self.auto_entry_type = "sellLimit"
                    self.auto_entry_price = self.auto_worstprice - slmax*ticksize
        else:
            if  self.auto_classification in ["A1","A2","D1","E1","F2","G"]:
                self.auto_entry_type = "buyStop"
                self.auto_entry_price = level + gap * ticksize
                if abs(self.auto_entry_price-self.auto_worstprice)/ticksize > slmax:
                    self.adjust_entry(close,ticksize, slmax, direction)
            elif  self.auto_classification in ["B1","C2","E2","F1"]:
                self.auto_entry_type = "buyStop"
                self.auto_entry_price = mvc + gap * ticksize
                if abs(self.auto_entry_price-self.auto_worstprice)/ticksize > slmax:
                    self.adjust_entry(close,ticksize, slmax, direction)
            else:
                if abs(self.auto_worstprice - close)/ticksize <= slmax:
                    self.auto_entry_type = "buyMarket"
                    self.auto_entry_price = close
                else:
                    self.auto_entry_type = "buyLimit"
                    self.auto_entry_price =  self.auto_worstprice + slmax*ticksize


    def adjust_entry(self, close:float, ticksize: float, slmax: int, direction: str):
        if abs(self.auto_worstprice - close)/ticksize <= slmax:
            self.auto_entry_type = f"{direction}Market"
            self.auto_entry_price = close
        else:
            self.auto_entry_type = f"{direction}Limit"
            self.auto_entry_price =  self.auto_worstprice + slmax*ticksize if direction=="buy" else self.auto_worstprice - slmax*ticksize
        
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

    def get_rc_entry(self, close: float, extreme: float, ticksize: float, direction: int, slmax: int, slmin: int, slippage: int) -> None:
        theorical_sl = abs(round((close-extreme)/ticksize))+slippage
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

    
