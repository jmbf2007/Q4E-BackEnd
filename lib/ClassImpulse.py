from typing import List,Optional
import datetime as dt
import math


class Impulse:

    initial: list
    final: list
    direction: int
    last: bool
    fault: Optional[int]
    method: str
    pullback_max: list
    pullback_percent_max: Optional[float]

    def __init__(self, initial: list, final: list, direction: int, method: str) -> None:
        self.initial = initial
        self.final = final
        self.direction = direction
        self.last = False
        self.fault = 0
        self.method = method

    def check_new_candle(self, high: float, low: float, time: str, max_fault: int=None, ha_open: float=None, ha_close: float=None) -> None:
        if self.method == "Fault New Extreme":
            self.fault_new_extreme(high, low, time, max_fault)
        elif self.method == "Pullback Percentage":
            self.pullback_percent(high, low, time, max_fault)
        elif self.method == "Heiken Ashi":
            self.heiken_ashi(high, low, time, ha_close, ha_open)
    
    def heiken_ashi(self, high: float, low: float, time: str, ha_close: float, ha_open: float) -> None:
        # sourcery skip: merge-duplicate-blocks, merge-else-if-into-elif, remove-redundant-if
        if self.direction == 1:
            if ha_close>=ha_open:                       # continua el impulso
                if high > self.final[1]:                # Nuevo High
                    self.final = [time,high]            # Actualizamos el final
            else:                                       # Impulso terminado
                self.last = True                        # Marcamos el impulso como terminado
        else:
            if ha_close<=ha_open:                       # continua el impulso
                if low < self.final[1]:                 # Nuevo Low
                    self.final = [time,low]             # Actualizamos el final
            else:                                       # Impulso terminado
                self.last = True                        # Marcamos el impulso como terminado

    def pullback_percent(self, high: float, low: float, time: str, max_pullback_percent: float) -> None:
        # sourcery skip: merge-else-if-into-elif
        if self.direction == 1:            
            if high > self.final[1]:                                                                        # Nuevo High
                self.final = [time,high]                                                                    # Actualizamos el final
                return
            else: 
                pullback_percent = (self.final[1] - low) / (self.final[1] - self.initial[1]) * 100          # Calculamos el pullback
        else:
            if low < self.final[1]:                                                                         # Nuevo Low                                                                                      
                self.final = [time,low]                                                                     # Actualizamos el final             
                return   
            else:
                pullback_percent = (high - self.final[1]) / (self.initial[1] - self.final[1]) * 100         # Calculamos el pullback

        if pullback_percent > max_pullback_percent:                                                         # Impulso terminado     
            self.last = True                                                                                # Marcamos el impulso como terminado

    def fault_new_extreme(self, high: float, low: float, time: str, max_fault: int) -> None:
        # sourcery skip: extract-duplicate-method, merge-else-if-into-elif
        if self.direction == 1:
            if high > self.final[1]:                # Nuevo High                
                self.final = [time ,high]           # Actualizamos el final
                self.pullback_max = []
                self.fault = 0
            else: 
                self.fault += 1
                self.pullback_max = [time, low] if (len(self.pullback_max)==0) or (len(self.pullback_max)>0 and low < self.pullback_max[1]) else self.pullback_max
                if self.fault >= max_fault:
                    self.last = True
        else:
            if low < self.final[1]:
                self.final = [time, low]
                self.pullback_max = []
                self.fault = 0
            else: 
                self.fault += 1
                self.pullback_max = [time, high] if (len(self.pullback_max)==0) or (len(self.pullback_max)>0 and high > self.pullback_max[1]) else self.pullback_max
                if self.fault > max_fault:
                    self.last = True

    def to_dict(self) -> dict:
        return {
            "initial": self.initial,
            "final": self.final,
            "direction": self.direction,
            "duration": self.duration_candles(),
            "slope": self.slope(),

        }

    def duration_candles(self, tf:int=5) -> float:
        if isinstance(self.initial[0], str):
            time_ini = dt.datetime.strptime(self.initial[0], "%Y-%m-%d %H:%M:%S")
            time_fin = dt.datetime.strptime(self.final[0], "%Y-%m-%d %H:%M:%S")
        else:
            # convertimos de timestamp a datetime
            time_ini = self.initial[0]
            time_fin = self.final[0]
        return int((time_fin - time_ini).total_seconds() / (tf*60))

    def slope(self, ticksize: float=0.25) -> float:
        inc=abs(self.final[1] - self.initial[1]) / ticksize
        # Calulamos la hipotenusa como un triangulo rectangulo entre el incremento y la duracion
        hip = math.sqrt(inc**2 + self.duration_candles()**2)
        # Calculamos el seno del angulo
        sen = inc / hip
        # Devolvemos el arcseno del angulo en grados
        return round(math.degrees(math.asin(sen)),1)