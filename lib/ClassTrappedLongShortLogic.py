from lib.ClassCandle import Candle
from lib.ClassTCCandle import TCCandle
from models.modelsSetting import Setting
from lib.ClassLogic import Logic
from lib.ClassOrder import Order
from datetime import timedelta


class TrappedLongShortLogic(Logic):

    @classmethod
    def check_new_entry(cls, candle: Candle, tc_assumptions: dict, setting: Setting, tc_lenght: int) -> object:
        tc= TCCandle(index=candle.Index)



        # Aplicasmos las condiciones de la estrategia. No hay que calcular mas valores ya que han sido calculados en el DataCandle
        for hypothesis, parameters in zip(list(tc_assumptions.keys()),list(tc_assumptions.values())):
            
            # Hay que añadir los valores de los parametros de la hipotesis a la clase TCCandle para poder usar los filtros posteriormente
            
            setattr(tc, parameters['param'], candle.__dict__[parameters['param']])

            tc.Assumptions.append({hypothesis : cls.apply_object_condition(
                setting=setting,
                ob=candle,
                param=parameters['param'],
                value=parameters['value'],
                logic=parameters['logic'])}
            )

        # La entrada en venta se da cuando hay largos atrapados y en compra cuando hay cortos atrapados
        # Las hipótesis para los largos atrapados son las que tienen "Upper" en el key de la hipótesis y para los cortos atrapados las que tienen "Lower" en el key de la hipótesis
        trapped_long = 1
        trapped_short = 1

        for hypothesis, assumption_value in zip(list(tc_assumptions.keys()),tc.Assumptions):
            if "Upper" in hypothesis:
                trapped_long = trapped_long * list(assumption_value.values())[0]
            if "Lower" in hypothesis:
                trapped_short = trapped_short * list(assumption_value.values())[0]

        # Probamos si hay largos atrapados
        if trapped_long==1:
            # Comprobamos si se exije concordancia de vela
            if hasattr(setting.strategyparameters, "concordance") and setting.strategyparameters.concordance:
                if candle.Candle_Type==1:
                    trapped_long = 1
                else:
                    trapped_long = 0
        if trapped_short==1:
            # Comprobamos si se exije concordancia de vela
            if hasattr(setting.strategyparameters, "concordance") and setting.strategyparameters.concordance:
                if candle.Candle_Type==-1:
                    trapped_short = 1
                else:
                    trapped_short = 0
        
        # Si hay largos atrapados y cortos apratados, no hay nada que hacer
        if trapped_long==1 and trapped_short==1:
            tc.Entry=False        

        # Si no hay largos atrapados ni cortos atrapados, no hay nada que hacer
        if trapped_long==0 and trapped_short==0:
            tc.Entry=False
        
        # Aplicamos la restriccion del tiempo
        if not setting.timeconstraints.min_hour <= candle.Relative_Hour <= setting.timeconstraints.max_hour:
            tc.Entry = False

        # Si hay largos atrapados y no cortos atrapados, se entra en venta
        if trapped_long==1 and trapped_short==0:
            tc.Entry=True
            tc.Direction="sell"
        
        # Si hay cortos atrapados y no largos atrapados, se entra en compra
        if trapped_long==0 and trapped_short==1:
            tc.Entry=True
            tc.Direction="buy"

        # Si hay entrada se calcula el resto de parametros
        if tc.Entry:
            tc.Market_Day = candle.Market_Day
            tc.Relative_Hour = candle.Relative_Hour
            tc.level_index = candle.Index       # Asignamos el level_index como la TC para funcionen los filtros de nivel
            tc.Interval = 0                     # Asignamos el intervalo a 0 para que no se apliquen los filtros de intervalo
            tc.tc_list_index = tc_lenght        # Asignamos la posicion que ocupa la TC en la lista de TCs

            # Calculamos el nivel de entrada
            extreme = candle.High if candle.Candle_Type == 1 else candle.Low
            slippage = setting.trademanagement.slippage if hasattr(setting.trademanagement, "slippage") else 0
            theorical_sl = abs(round((candle.Close-extreme)/setting.instrument.ticksize))+slippage
            # 1) Si la entrada es a mercado
            if setting.trademanagement.entry_type == "MarketOrder":
                #Si la entrada es a mercado, hay limite de sl y este supera el SL maximo, no hay entrada
                if hasattr(setting.trademanagement, "slmax") and theorical_sl > setting.trademanagement.slmax:                
                    tc.Entry = False                    
                else:
                    tc.auto_entry_price = candle.Close                                                                                              # Precio de entrada a mercado
                    tc.auto_entry_type = 'sellMarket' if candle.Candle_Type == 1 else 'buyMarket'                                                   # Tipo de entrada a mercado
                    tc.auto_sl = theorical_sl if not hasattr(setting.trademanagement, "slmin") or theorical_sl > setting.trademanagement.slmin else setting.trademanagement.slmin  # SL de la entrada a mercado

            # 2) Si la entrada es Automatica
            elif setting.trademanagement.entry_type == "Auto":
                if hasattr(setting.trademanagement, "slmax") and theorical_sl > setting.trademanagement.slmax:                                        #Si la entrada es automatica, hay limite de sl y este supera el SL maximo, hacemos entrada limite al precio que cumpla el slmax
                    tc.auto_entry_price = candle.Close - setting.instrument.ticksize*(theorical_sl - setting.trademanagement.slmax) * tc.Direction
                    tc.auto_entry_type = 'sellLimit' if tc.Direction == -1 else 'buyLimit'
                    tc.auto_sl = setting.trademanagement.slmax
                else:
                    tc.auto_entry_price = candle.Close                                                                                                          # Precio de entrada automatica
                    tc.auto_entry_type = 'sellMarket' if tc.Direction == -1 else 'buyMarket'                                                                    # Tipo de entrada automatica
                    tc.auto_sl = theorical_sl if not hasattr(setting.trademanagement, "slmin") or theorical_sl > setting.trademanagement.slmin else setting.trademanagement.slmin

        if tc.Entry:
            order = cls.set_order(setting, candle)
        return {'tc': tc, 'order': order if tc.Entry else None}


    @classmethod
    def set_order(cls,setting: Setting, candle: Candle) -> Order:
        # Calculamos el nivel de entrada
        if setting.trademanagement.entry_type == "MarketOrder":
            open_price = candle.Close                                                                                              # Precio de entrada a mercado
            order_type = 'sellMarket' if candle.Candle_Type == 1 else 'buyMarket'                                                  # Tipo de entrada a mercado


        elif setting.trademanagement.entry_type == "LimitOrder":        
            order_type = 'sellLimit' if candle.Candle_Type == 1 else 'buyLimit'                                                   # Tipo de entrada a limite
            open_price = candle.Close + setting.trademanagement.order_gap * setting.instrument.ticksize * candle.Candle_Type      # Precio de entrada a limite


        elif setting.trademanagement.entry_type == "StopOrder":
            order_type = 'sellStop' if candle.Candle_Type == 1 else 'buyStop'                                                      # Tipo de entrada a stop
            open_price = candle.Close - setting.trademanagement.order_gap * setting.instrument.ticksize * candle.Candle_Type
            open_time = candle.Time + timedelta(minutes=setting.instrument.tf)                                                     # Tiempo de entrada a stop

        else:                                                                                            
            order_type = None
            open_price = None


        open_time = candle.Time + timedelta(minutes=setting.instrument.tf)                                                     # Tiempo de entrada a mercado

        order = Order()
        order.newOrder(order_type=order_type, 
                       open_time=open_time, 
                       open_price=open_price, 
                       size=setting.trademanagement.size
        )

        tpsl = cls.set_tpsl(setting, candle, order)

        order.tp = tpsl['tp']
        order.sl = tpsl['sl']

        return order

    
    