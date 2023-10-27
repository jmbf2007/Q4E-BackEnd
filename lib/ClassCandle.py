
from typing import List,Optional
from pydantic import BaseModel
from datetime import datetime



class Candle(BaseModel):
    # Datos básicos 
    Index:                      int                 # Indice de la vela
    Time:                       datetime            # Tiempo de apertura de la vela
    Open:                       float               # Precio de apertura de la vela 
    High:                       float               # Precio máximo de la vela
    Low:                        float               # Precio minimo de la vela
    Close:                      float               # Precio de cierre de la vela
    Delta:                      int                 # Delta de la vela
    Volume:                     int                 # Volumen de la vela
    MVC:                        int                 # Poscion en precio del Cluster de Volumen Maximo
    NewSession:                 bool                # True si la vela es la primera de la session
    NewWeek:                    bool                # True si la vela es la primera de la semana
    MewMonth:                   bool                # True si la vela es la primera del mes
    Ask:                        Optional[List[int]] # Lista con los valores de Ask de la vela desde el High al Low
    Bid:                        Optional[List[int]] # Lista con los valores de Bid de la vela desde el High al Low

    
    # Parámetros geometricos y tiempo de la vela
    Candle_Ask:                 Optional[int]       # Ask de vela
    Candle_Bid:                 Optional[int]       # Bid de la vela
    Candle_Type:                Optional[int]       # 1 alcista -1 bajista 0 doji
    Range:                      Optional[int]       # Rango en ticks de vela 
    Body:                       Optional[int]       # Cuerpo en ticks de la vela
    BR:                         Optional[int]       # Ratio body/range en %
    Candle_Sesssion_Index:      Optional[int]       # Numero de la vela dentro de la sesion de mercado
    Pullback_Buy:               Optional[int]       # Pullback para compra: Close(anterior)-Low(actual)
    Pullback_Sell:              Optional[int]       # Pullback para venta: High(actual)- Close(anterior)
    MVC_Percentage:             Optional[int]       # Posicion en % del CVM
    MVC_Gap:                    Optional[int]       # Gap en ticks del CVM respecto al cuerpo de la vela
    Relative_Hour:              Optional[int]       # Hora de mercado de la vela respecto a la apertura de la sesion 
    Shadow_Upper:               Optional[int]       # Mecha superior de la vela en ticks
    Shadow_Lower:               Optional[int]       # Mecha inferio de la vela en ticks
    HT:                         Optional[int]       # Ratio Head/Tail en %
    Market_Day:                 Optional[int]       # Dia de mercado de la vela
    Vol_H1:                     Optional[int]       # Volumen acumulado que lleva la vela de 1H en esta vela
    Session:                    Optional[str]       # Sesion de mercado a la que pertenece la vela
    Tradeable:                  Optional[bool]      # Indica si la vela es operable
    
    # Indicadores out_chart
    CumDelta:                   Optional[int]       # Delta acumulado de la session de la vela
    RSI:                        Optional[int]       # Valor del indicador RSI de la vela
    ATR:                        Optional[int]       # Valor del indicador ATR de la vela
    AR:                         Optional[int]       # Valor del indicador AR de la vela
    TLS_Upper_Delta:            Optional[int]       # Delta de la mecha superior
    TLS_Upper_Volume:           Optional[int]       # Volumen de la mecha superior
    TLS_Upper_Ask_Percentage:   Optional[int]       # Delta de la mecha superior en %
    TLS_Upper_Ask_Levels_Percentage: Optional[int]  # Delta de la mecha superior en niveles de %
    TLS_Lower_Delta:            Optional[int]       # Delta de la mecha inferior
    TLS_Lower_Volume:           Optional[int]       # Volumen de la mecha inferior
    TLS_Lower_Bid_Percentage:   Optional[int]       # Delta de la mecha inferior en %
    TLS_Lower_Bid_Levels_Percentage: Optional[int]  # Delta de la mecha inferior en niveles de %
    TLS_Max_Ask_In_Upper_Shadow: Optional[bool]     # True si el Ask maximo de la vela esta en la mecha superior
    TLS_Max_Bid_In_Lower_Shadow: Optional[bool]     # True si el Bid maximo de la vela esta en la mecha inferior
    TLS_Result:                 Optional[int]       # Resultado de la evaluacion de la hipotesis de la TLS: 1 largos atrapados, -1 cortos atrapados, 0 no atrapados

    

    # Indicadores on_chart
    Session_VWAP:               Optional[float]     # Valor del VWAP de la session
    Week_VWAP:                  Optional[float]     # Valor del VWAP semanal
    Month_VWAP:                 Optional[float]     # Valor del VWAP mensual
    CD_High:                    Optional[float]     # Valor maxímo del Día Actual
    CD_Low:                     Optional[float]     # Valor mínimo del Dia Actual
    LD_High:                    Optional[float]     # Valor máximo del Ultimo Día
    LD_Low:                     Optional[float]     # Valor mínimo  del Ultimo Día
    LD_Close:                   Optional[float]     # Valor de cierre del Ultimo Día
    Daily_Change:               Optional[int]       # Variacion en % del precio de cierre del vela con respecto al cierre del Ultimo Día
    Asia_High:                  Optional[int]       # Valor del máximo de la sesion Asiática
    Asia_Low:                   Optional[int]       # Valor del mínimo de la sesion Asiática
    EU_High:                    Optional[int]       # Valor del máximo de la sesion Europea
    EU_low:                     Optional[int]       # Valor del mínimo de la sesion Europea
    USA_High:                   Optional[int]       # Valor del máximo de la sesion Americana
    USA_Low:                    Optional[int]       # Valor del mínimo de la sesion Americana
    PP:                         Optional[int]       # Valor del Pivot Point
    S1:                         Optional[int]       # Valor del S1 de los Pivot Points
    S2:                         Optional[int]       # Valor del S2 de los Pivot Points
    S3:                         Optional[int]       # Valor del S3 de los Pivot Points
    R1:                         Optional[int]       # Valor del R1 de los Pivot Points
    R2:                         Optional[int]       # Valor del R2 de los Pivot Points
    R3:                         Optional[int]       # Valor del R3 de los Pivot Points
    ZCE_W_High:                 Optional[float]     # Valor del máximo de la Zona de Control por Esructura Semanal
    ZCE_W_Low:                  Optional[float]     # Valor del mínimo de la Zona de Control por Esructura Semanal
    ZCE_M_High:                 Optional[float]     # Valor del máximo de la Zona de Control por Esructura Mensual
    ZCE_M_Low:                  Optional[float]     # Valor del mínimo de la Zona de Control por Esructura Mensual
    ZCC_1_High:                 Optional[float]     # Valor del máximo de la Zona de Control Climática del Lunes
    ZCC_1_Low:                  Optional[float]     # Valor del mínimo de la Zona de Control Climática del Lunes
    ZCC_2_High:                 Optional[float]     # Valor del máximo de la Zona de Control Climática del Martes
    ZCC_2_Low:                  Optional[float]     # Valor del mínimo de la Zona de Control Climática del Martes
    ZCC_3_High:                 Optional[float]     # Valor del máximo de la Zona de Control Climática del Miercoles
    ZCC_3_Low:                  Optional[float]     # Valor del mínimo de la Zona de Control Climática del Miercoles
    ZCC_4_High:                 Optional[float]     # Valor del máximo de la Zona de Control Climática del Jueves
    ZCC_4_Low:                  Optional[float]     # Valor del mínimo de la Zona de Control Climática del Jueves
    ZCC_5_High:                 Optional[float]     # Valor del máximo de la Zona de Control Climática del Viernes
    ZCC_5_Low:                  Optional[float]     # Valor del mínimo de la Zona de Control Climática del Viernes 

         
    def __init__(self, data:dict, columns:list) -> None:
        for c,x in zip(columns,data):            
            self.__dict__.update({c:x})


    def to_dict(self) -> dict:
        return dict(self.__dict__.items())
    
    def from_dict(self, data: dict) -> None:
        self.__dict__.update(data)
    
    @property    
    def TimeMinutes(self):      
        return self.Time.to_pydatetime().minute
            