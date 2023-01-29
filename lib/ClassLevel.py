from datetime import datetime
import numpy as np
from typing import Optional



class cLevel():
    level_type: str                                 # Tipo de nivel: DP, Imbalance, VPOC, etc. 
    index: int                                      # Indice de la vela donde se produce el nivel
    price: float                                    # Precio del nivel
    start_time: datetime                            # Fecha de la vela donde comienza el nivel
    main: bool                                      # True si es un nivel de la estratgia. False para los niveles añadidos como extras
    active: bool                                    # True si aun no ha sido testeado
    direction: Optional[str]                        # buy para niveles de compra, sell para ventas o None
    end_time: Optional[datetime]                    # Fecha de la vela donde se toca el nivel
    interval: Optional[int]                         # Numero de velas entre la vela de inicio y la vela de toque
    delta: Optional[int]                            # Valor del Delta en la vela donde comienza el nivel
    volume: Optional[int]                           # Valor del Volumen en la vela donde comienza el nivel

    
    
    def __init__(self, level_type: str, index: int, price: float, start_time: datetime, delta: int, volume: int, direction: str, main: bool) -> None:
        """Constructor

        Args:
            price (float): Precio del nivel
            start_time (dt.datetime): Fecha de la vela donde comienza el nivel
            delta (int): Nivel de delta en el precio del nivel
            volume (int): Volumen en el precio del nivel
            ticksize (float): Tamaño del tick
        """
        self.level_type = level_type
        self.price = price
        self.start_time = start_time
        self.delta = delta
        self.volume = volume
        self.direction = direction
        self.main = main
        self.active = True
        self.index = index

    def to_dict(self) -> dict:
        return dict(self.__dict__.items())
               
    def end_time(self, time: np.array, high: np.array, low: np.array) -> np.datetime64:
        """Funcion que devuelve la fecha de la vela en la que se toca el nivel por primera vez

        Args:
            time (np.array): Array con las fechas de las velas 
            high (np.array): Array de float con los high de las velas
            low (np.array):  Array de float con los low de las velas
        Returns:
            np.datetime: Fecha de vela en la que toca o None si es tocado
        """
        return next(
            (tm for tm, hg, lw in zip(time, high, low) if self.touched(hg, lw)),
            None,
        )
    
    def touched(self, high: float, low:float)-> bool:
        """Funcion que devuelve si el nivel ha sido tocado por una vela

        Args:
            high (float): High de la vela
            low (float): Low de la vela

        Returns:
            bool: True si es tocado
        """
        return low <= self.price <= high
    
    def distance(self, level: float, ticksize: float)-> int:
        """Devuelve la distancia en ticks hasta otro nivel dado

        Args:
            level (float): Precio del nivel sobre el que se quiere medir la distancia
            ticksize (float): Tamaño del tick del instrumento

        Returns:
            int: Distnancia en ticks
        """
        return int(abs(level-self.price)/ticksize)
        
    def confluence(self, level: float, tolerance: int)-> bool:
        """Devuelve si hay confluenciencia dentro de un rango de tolerancia, es decir que la distancia entre los niveles sea menor o igual a la tolerancia en ticks

        Args:
            level (float): Precio del otro nivel
            tolerance (int): Ticks de tolerancia del rango

        Returns:
            bool: True si los dos niveles están dentro del rango de tolerancia
        """
        return self.distance(level)<= tolerance 
    