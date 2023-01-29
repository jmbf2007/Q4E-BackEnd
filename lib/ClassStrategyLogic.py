from this import d
from typing import List,Optional
from lib.ClassCandle import Candle
from lib.ClassTCCandle import TCCandle
from lib.ClassReversal import Reversal
from models.modelsSetting import Setting
import math

CANDLE_PATTERN = ['reversal', 'morning_star', 'evening_star', 'shooting_star', 'engulfing', 'harami']

class StrategyLogic():
    strategy_type:  str                         # Tipo de strategia
    setting:        Setting                     # Objeto setting
    tc_assumptions: Optional[dict]              # Diccionario con las hipotesis para la vela de toque de la estrategia
    tc:             Optional[List[TCCandle]]    # Lista con las velas de toque encontradas por la estrategia
    tc_entry:       Optional[int]               # Posicion en la lista desde final de la ultima vela de toque que provoca entrada. Normalmente será la ultima (-1) pero si la TC toca varios niveles 
                                                # puede ser que la ultima vela de toque no sea la de la entrada
    
    def __init__(self, setting:dict, tc_assumptions: dict, strategy_type: str) -> None:
        self.setting = Setting(setting)
        self.tc_assumptions = tc_assumptions
        self.strategy_type = strategy_type
        self.tc = []
    
    def checkLogic(self, candle: Candle, levels: list=None) -> bool:
        # Si la estrategia es del tipo nivel + vela de toque primero se comprueba que la vela toca un nivel principal
        if self.strategy_type in ["level+tc", "level+atc"]:
            # Comprobamos si es una vela de toque 
            entries = 0
            for level in levels:
                if candle.Index>level['index'] and candle.Low <= level['price'] <= candle.High:
                    # Evaluamos la vela toque
                    entries +=1 if self.strategy_level_tc(candle, level) else entries

            # Comprobamos si hay tocado mas de una nivel dejando entrada en mas de 1
            if entries >1:                 
                self.tc_entry = self.set_best_entry(entries)
                return True
            elif entries ==1:
                self.tc_entry = -1
                return True
            elif hasattr(self,"tc_entry"):
                del self.tc_entry
        elif self.strategy_type in CANDLE_PATTERN:
            # Comprobamos si es una vela de patron
            return self.strategy_candle_pattern(candle)

        
        elif self.strategy_type == "indicators":
            pass

        return False
            
    # Metodo (por implementar) que selecciona la mejor entrada si la vela toca varios niveles y da mas de una entrad
    def set_best_entry(self, entries: int) ->int:
        for i in range(entries):
            if self.tc[-1-i]['Entry']:
                return -1-i

                  
    def apply_object_condition(self,ob:object,param:str, value: str, logic: str) -> bool:
        # sourcery skip: remove-redundant-if 
        if logic == ">=":
            return ob.__dict__[param] >= self.setting.strategyparameters.__dict__[value]
        elif logic == "<=":
            return ob.__dict__[param] <= self.setting.strategyparameters.__dict__[value]
        elif logic == ">":
            return ob.__dict__[param] > self.setting.strategyparameters.__dict__[value]
        elif logic == "<":
            return ob.__dict__[param] < self.setting.strategyparameters.__dict__[value]
        elif logic == "=":
            return ob.__dict__[param] == self.setting.strategyparameters.__dict__[value]
        elif logic == "True" or True:
            return ob.__dict__[param] if self.setting.strategyparameters.__dict__[value] else True

        
    def strategy_level_tc(self, candle: Candle, level: dict) -> bool:
        tc = TCCandle(index=candle.Index)
        # Calculamos los parámetros de la vela de toque y evaluamos su condicion
        for hypotesys,parameters in zip(list(self.tc_assumptions.keys()), list(self.tc_assumptions.values())):
            if parameters['param']=="Bounce" and not hasattr(tc,"Bounce"):
                tc.get_bounce(tc_close=candle.Close,level=level,ticksize=self.setting.instrument.ticksize)
                
            elif parameters['param']=="Interval":
                tc.get_interval(index = level['index'])
                
            elif parameters['param']=="Delta_Convergence":
                tc.get_delta_convergence(direction=level['direction'], delta=candle.Delta)
                
            elif parameters['param']=="CumDelta_Convergence":
                tc.get_cumdelta_convergence(direction=level['direction'], cumdelta=candle.CumDelta)
                
            elif parameters['param']=="MVC_Percentage":
                tc.MVC_Percentage = candle.MVC_Percentage
            
            elif parameters['param']=="Concordance":
                tc.get_concordance(direction=level['direction'], candeltype=candle.Candle_Type)
        

            # Evaluamos la condicion y la almacenamos
            tc.Assumptions.append({hypotesys : self.apply_object_condition(tc,parameters['param'],parameters['value'],parameters['logic'])})

        
        # True si se cumplen todas
        tc.Entry = math.prod([list(hypotesis.values())[0] for hypotesis in tc.Assumptions])

        # Aplicamos la restriccion del tiempo
        if not self.setting.timeconstraints.min_hour <= candle.Relative_Hour <= self.setting.timeconstraints.max_hour:
            tc.Entry = False
            
        tc.Direction = level["direction"]
        tc.Market_Day = candle.Market_Day
        tc.Relative_Hour = candle.Relative_Hour
        tc.get_level_index()
        tc.tc_list_index = len(self.tc)
        # Parametros para las entradas automáticas
        if self.setting.trademanagement.entry_type in ["Auto","Invert"] and tc.Entry:
            tc.get_auto_worstprice(level["direction"], level["price"], candle.High, candle.Low)
            tc.get_auto_classification(level['price'], candle.MVC, candle.Close)
            tc.get_auto_entry_type(
                direction=tc.Direction, 
                gap=self.setting.trademanagement.order_gap if hasattr(self.setting.trademanagement,"order_gap") else 0,
                ticksize = self.setting.instrument.ticksize, 
                level = level['price'],
                mvc = candle.MVC, 
                close = candle.Close, 
                slmax = self.setting.trademanagement.slmax
            )
            

        # Almacenamos el TC
        self.tc.append(tc.to_dict())
        return tc.Entry

    def strategy_candle_pattern(self, candle: Candle) -> bool:
        if self.strategy_type ==  "reversal":
            return self.reversal_candle_pattern(candle)
        return False

    def reversal_candle_pattern(self, candle: Candle) -> bool:
        tc = TCCandle(index=candle.Index)
        for hypotesys,parameters in zip(list(self.tc_assumptions.keys()), list(self.tc_assumptions.values())):
            if parameters['param']=="Body":
                tc.get_body(candle.Body)
            elif parameters['param']=="BR":
                tc.get_br(candle.BR)
            elif parameters['param']=="HT":
                tc.get_ht(candle.HT)
            elif parameters['param']=="MVC_Gap":
                tc.get_mvc_gap(candle.MVC_Gap)
            elif parameters['param']=="Volume":
                tc.get_volume(candle.Volume)
            elif parameters['param']=="InvertDelta":
                tc.get_invertdelta(direction=candle.Candle_Type, delta=candle.Delta)
        
            # Evaluamos la condicion y la almacenamos
            tc.Assumptions.append({hypotesys : self.apply_object_condition(tc,parameters['param'],parameters['value'],parameters['logic'])})
        


        # True si se cumplen todas
        tc.Entry = bool(math.prod([list(hypotesis.values())[0] for hypotesis in tc.Assumptions]))

        # Aplicamos la restriccion del tiempo
        if not self.setting.timeconstraints.min_hour <= candle.Relative_Hour <= self.setting.timeconstraints.max_hour:
            tc.Entry = False

        tc.Direction = candle.Candle_Type
        tc.Market_Day = candle.Market_Day
        tc.Relative_Hour = candle.Relative_Hour
        tc.tc_list_index = len(self.tc)


        # Si hay entrada almacenamos el resto de parametros y calulamos el nivel de entrada
        if tc.Entry:
            tc.Market_Day = candle.Market_Day
            tc.Relative_Hour = candle.Relative_Hour
            tc.get_rc_entry(close=candle.Close, 
                            extreme=candle.High if candle.Candle_Type == -1 else candle.Low,
                            ticksize=self.setting.instrument.ticksize, 
                            direction= candle.Candle_Type,
                            slmax = self.setting.trademanagement.slmax,
                            slmin = self.setting.trademanagement.slmin,
                            slippage=self.setting.trademanagement.slippage
            )
            tc.level_index = candle.Index       # Asignamos el level_index como la TC para funcionen los filtros de nivel
            tc.Interval = 0                     # Asignamos el intervalo a 0 para que no se apliquen los filtros de intervalo
            self.tc.append(tc.to_dict())
        if tc.Entry:
            self.tc_entry=-1                    # Ultimo elemento de la lista TC
        return tc.Entry


 