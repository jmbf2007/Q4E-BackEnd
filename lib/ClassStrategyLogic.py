from typing import List,Optional
from lib.ClassCandle import Candle
from lib.ClassTCCandle import TCCandle
from lib.ClassReversalLogic import ReversalLogic
from lib.ClassTrappedLongShortLogic import TrappedLongShortLogic
from lib.ClassLevelTCLogic import LevelTCLogic
from models.modelsSetting import Setting
from lib.ClassOrder import Order


CANDLE_PATTERN = ['reversal', 'morning_star', 'evening_star', 'shooting_star', 'engulfing', 'harami']
INDICATORS = ['tls', 'inbalance']

class StrategyLogic():
    strategy_type:  str                         # Tipo de strategia
    setting:        Setting                     # Objeto setting
    tc_assumptions: Optional[dict]              # Diccionario con las hipotesis para la vela de toque de la estrategia
    tc:             Optional[List[TCCandle]]    # Lista con las velas de toque encontradas por la estrategia
    tc_entry:       Optional[int]               # Posicion en la lista desde final de la ultima vela de toque que provoca entrada. Normalmente será la ultima (-1) pero si la TC toca varios niveles puede ser que la ultima vela de toque no sea la de la entrada
    orders:         Optional[List[Order]]       # Lista con las ordenes de la estrategia
    
    def __init__(self, setting:dict, tc_assumptions: dict, strategy_type: str) -> None:
        self.setting = Setting(setting)
        self.tc_assumptions = tc_assumptions
        self.strategy_type = strategy_type
        self.tc = []
        self.orders = []
    
    def checkLogic(self, candle: Candle, levels: list=None) -> bool:
        # Si la estrategia es del tipo nivel + vela de toque primero se comprueba que la vela toca un nivel principal
        if self.strategy_type in ["level+tc", "level+atc"]:
            return self.strategy_level_tc(candle, levels)

        elif self.strategy_type in CANDLE_PATTERN:
            return self.strategy_candle_pattern(candle)
        
        elif self.strategy_type in INDICATORS:
            if self.strategy_type == "tls":
                return self.strategy_tls(candle)
            # Comprobamos si se dan las condiciones de la estrategia            

        return False
            
    def strategy_level_tc(self, candle: Candle, levels: list) -> bool:
        result = LevelTCLogic.check_new_entry(candle=candle, tc_assumptions= self.tc_assumptions, setting=self.setting, levels=levels, tc_lenght=len(self.tc))
        if result['tc'] is not None:
            self.tc.append(result['tc'].to_dict())
            if result['tc'].Entry:
                self.orders.append(result['order'].to_dict())
                return True
        return False   

    def strategy_candle_pattern(self, candle: Candle) -> bool:
        if self.strategy_type ==  "reversal":
            result = ReversalLogic.check_new_entry(candle, self.tc_assumptions, self.setting,len(self.tc))
            if result['tc'] is not None and result['tc'].Entry:
                return self.add_tc_and_order(result)
            return False    

    def strategy_tls(self, candle: Candle) -> bool:
        result = TrappedLongShortLogic.check_new_entry(candle=candle, tc_assumptions=self.tc_assumptions, setting=self.setting, tc_lenght=len(self.tc))
        if result['tc'] is not None and result['tc'].Entry:
            return self.add_tc_and_order(result)
        return False

