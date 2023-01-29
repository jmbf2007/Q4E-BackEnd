import numpy as np
import sys
sys.path.append("..")



MARKET_SESSIONS_CANDLE_INDEX={
    1:  [480,930,1335],
    5:  [96,186,267],
    15: [32,62,89],
    30: [16,31,44],
    60: [8,15,22]
}

# Funciones para el calculo de parametrso de vela 
def candle_type(open, close)-> int:
    """Funcion que clasifica el tipo de vela en alcista, bajista y doji

    Args:
        open (float): Precio de apertura. Puede ser una serie de float
        close (float): Precio de cierre. Puede ser una serie de float

    Returns:
        int: 1: alcista, -1: bajista, 0: doji
    """
    return 0 if close==open else (1 if close>open else -1)

def candle_range(high, low, ticksize: float)-> int:
    """Funcion que devuelve en rango en ticks de una vela

    Args:
        high (float): Precio High. Puede ser una serie de float
        low (float): Precio Low. Puede ser una serie de float
        ticksize (float): Tamaño del tick del instrumento

    Returns:
        int: Valor en ticks del rango de la vela
    """
    return ((high-low)/ticksize)+1

def candle_body(open, close, ticksize: float) -> int:
    """Funcion que devuelve el valor en ticks del cuerpo de la vela

    Args:
        open (float): Precio de apertura. Puede ser una serie de float
        close (float): Precio de cierre. Puede ser una serie de float
        ticksize (float): Tamaño del tick del instrumento

    Returns:
        int: Valor en ticks del cuerpo de la vela
    """
    return (abs(open-close)/ticksize)+1

def candle_pullback(index,high,low, close,ticksize:float,type:str) -> int:
    """Generator que calcula el pullback de una vela con respecto al cierre de la anterior para un tipo de orden requerido: Buy o Sell. Es decir, el pullback para un Buy 
    se mide con el precio de cierre de la vela anterior menos el low de la vela actual. Para un Sell el pullback es el High de la actual menos el cierre de la anterior

    Args:
        index (Serie de int): Indices de las velas
        high (Serie de float): Serie con los precios high de las velas
        low (Serie de float): Serie con los precios low de las velas
        close (Serie de float): Serie con los precios close de las velas
        ticksize (float): Tamaño del tick del instrumento
        type (str): "Buy" o "Sell"

    Yields:
        Iterator[int]: Valor del pullback en ticks
    """
    pullback = 0
    idmin=int(index[0])
    for id,hg,lw in zip(index, high, low):
        id =int(id)
        if id > idmin :
            prev_close = close.iloc[id-1]
            if type == "Buy":
                pullback = int((prev_close-lw)/ticksize)
            else:
                pullback = int((hg- prev_close)/ticksize)
        else:
            pullback = 0    
        yield pullback

def candle_mvc_percentage(open, high, low, close, mvc) -> int:
    """Funcion que devuelve la posición del MVC de una vela en %

    Args:
        open (float): Precio de apertura. Puede ser una serie de float
        high (float): Precio High. Puede ser una serie de float
        low (float): Precio Low. Puede ser una serie de float
        close (float): Precio de cierre. Puede ser una serie de float
        mvc (float): Precio del mvc. Puede ser una serie de float

    Returns:
        int: Posicion del mvc en % 
    """
    if open==close:
        return 100
    #Vela alcista
    if open<close:
        return int(round(((mvc - low)/(high-low))*100))
    #Vela bajista
    return int(round(((high -mvc)/(high-low))*100))


def candle_mvc_gap(open: float,mvc:float, direction:int ,ticksize: float) -> int:
    """Funcion que devuelve el gap en ticks del MVC de una vela y el cuerpo

    Args:
        open (float): Precio de apertura. Puede ser una serie de float
        mvc (float): Precio del mvc. Puede ser una serie de float
        direction (int): 1: alcista, -1: bajista
        ticksize (float): Tamaño del tick del instrumento

    Returns:
        int: Gap del MVC en ticks
    """
    if direction == 1:
        gap = round((open-mvc)/ticksize-1) if open > mvc else 0
    elif direction == -1:
        gap = round((mvc-open)/ticksize-1) if open < mvc else 0
    elif direction == 0:
        gap = 0
    return gap

def candle_relative_hour(newsession,time) -> int:
    """Generator para calcula la hora relativa de la vela desde la apertura de mercado. 

    Args:
        newsession (pd.series): Columna NewSession.
        time (pd.series):       Columna con el tiempo de apertura de la vela. 

    Yields:
        int: Devuelve la hora relativa desde la apertura de mercado. Es un valor entre 0 y 23
    """
    session_ini_time=0
    rel_hour=0
    for new,tm in zip(newsession,time):
        if new:
            session_ini_time = tm

        yield int((tm-session_ini_time).total_seconds()//3600)  
    
def candle_cummulative_delta(new, delta) -> int:
    """Generator que devuelve el delta acumulado de una vela con respecto al inicio de sessio

    Args:
        new (pd.Serie: bool): Serie de bool con el inicio de la session
        delta (pd.Serie int): Serie de int con el valor del delta de las velas

    Yields:
        Iterator[int]: Valor del delta acumulado
    """
    _cum_delta=0
    for n,d in zip(new,delta):
        if n:
            _cum_delta=0
        _cum_delta +=d
        yield _cum_delta    
        
def candle_shadow_up(type, open, high, close, ticksize: float) -> int:
    """Funcion que devuelve el valor en tick de la mecha superior de una vela

    Args:
        type (int):    1: alcista, -1: bajista, 0: doji
        open (float): Precio de apertura. Puede ser una serie de float
        high (Serie de float): Serie con los precios high de las velas
        close (Serie de float): Serie con los precios close de las velas
        ticksize (float): Tamaño del tick del instrumento

    Returns:
        [int]: Valor en ticks de la mecha superior
    """   
    return ((high-close)/ticksize)  if type==1 else ((high-open)/ticksize)    

def candle_shadow_down(type, open, low, close, ticksize: float) -> int:
    """Funcion que devuelve el valor en tick de la mecha inferior de una vela

    Args:
        type (int):    1: alcista, -1: bajista, 0: doji
        open (float): Precio de apertura. Puede ser una serie de float
        low (Serie de float): Serie con los precios low de las velas
        close (Serie de float): Serie con los precios close de las velas
        ticksize (float): Tamaño del tick del instrumento

    Returns:
        [int]: Valor en ticks de la mecha inferior
    """   
    return ((open-low)/ticksize) if type==1 else ((close-low)/ticksize)     

def candle_head_tail(shadow_up,shadow_down, candle_type) -> int:
    """Funcion que devuelve la relacion entre cabeza y cola de una vela

    Args:
        shadow_up (int): Valor en ticks de la mecha superior
        shadow_down (int): Valor en ticks de la mecha inferior
        candle_type (int): 1: alcista, -1: bajista, 0: doji

    Returns:
        int: Ratio entre cabeza y cola en %
    """    
    if candle_type==0:
        return 100
    elif candle_type==1:
        return abs(int((shadow_up/shadow_down)*100)) if shadow_down!=0 else 100
    else:
        return abs(int((shadow_down/shadow_up)*100)) if shadow_up!=0 else 100

def candle_1h_volume(_time, _volume)->int:
    """Generator que calcula el volume de la vela horaria

    Args:
        _time (pd.Serie): Columna Time
        _volume (pd.Serie): Columna Volume

    Yields:
        [int] : Volume que va acumulando a vela horaria 
    """
    vol1H=0
    for tm,vol in zip(_time, _volume):
        if tm.minute==0:
            vol1H = vol
        else:
            vol1H += vol
        yield vol1H

def count_market_days(newsession, initial_market_day: int) -> int:
    """Generator que cuenta los días de mercado a partir de un día dado

    Args: 
        newsession (pd.series): Columna NewSession.    
        initial_market_day (int): Numeracion del primer día desde el que queremos contar

    Yields:
        Iterator[int]: Numero entero con el numero de días
    """
    day=initial_market_day-1
    for ns in newsession:
        if ns:
            day += 1
        yield day

def candle_session_index(newsession)-> int:
    """Funcion que numera las velas de la session comenzado en 1 en la vela de newsession

    Args:
        newsession (pd.Serie): Columna NewSession  
        index (pd.Serie): Columna index

    Yields:
        Iterator[int]: valor relativo de la vela respecto del inicio de session
    """
    for nw in newsession:
        if nw:
            cont=0
        else:
            cont +=1
            
        yield cont
        
def market_session(candle_session_index, tf: int)-> str:
    """Generator que devuelve la sesion de mercado de la vela.

    Args:
        candle_session_index (pd.Serie): Columna Candle_Session_Index
        tf (int):   Timeframe de las velas

    Yields:
        Iterator[str]: Session de mercado de la vela: Asia, EU o USA
    """
    # Las sessione de mercado se determinan en velas inferiores a 1h, para velas de 4h y diario no tiene sentido hablar de sessiones de mercado
    for id in candle_session_index:
        if 0 < id < MARKET_SESSIONS_CANDLE_INDEX[tf][0]:
            session = 'Asia'
        elif MARKET_SESSIONS_CANDLE_INDEX[tf][0] <= id < MARKET_SESSIONS_CANDLE_INDEX[tf][1]:
            session = 'EU'
        elif MARKET_SESSIONS_CANDLE_INDEX[tf][1] <= id < MARKET_SESSIONS_CANDLE_INDEX[tf][2]:
            session = 'USA'
        else:
            session = 'Overnight'
        
        yield session

# Funciones para el calculo de indicadores        
def true_range(high,low,close,index,ticksize: float)->int:
    """Generator que calcula el true range de una vela. El True Range es el valor máximo de entre 3 opciones:
    1) High - Low
    2) High - Prev. Close
    3) Prev. Close - Low

    Args:
        high (pd.series): Columna High.
        low (pd.series): Columna Low.
        close (pd.series): Columna Close.
        index (pd.series): Columna Index.
        ticksize (float): Tamaño del tick del instrumento

    Yields:
        Iterator[int]: Valor del True Range
    """
    tr=np.nan
    prev_close = 0
    for hg,lw,cl,i in zip(high,low,close,index):
        if i != 0:
            tr = max([hg-lw,abs(hg-prev_close), abs(prev_close-lw)])
        prev_close = cl   
        yield tr/ticksize+1 

def rsi(close, period: int) -> float:
    """Funcion que calcula el indicador RSI 

    Args:
        close (pd.series): Columna Close.
        period (int): Perido del rsi

    Returns:
        float: Valor del RSI
    """
    chg = close.diff(1)
    gain = chg.mask(chg<0,0)
    loss = chg.mask(chg>0,0)
    avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
    rs = abs(avg_gain/avg_loss)
    return  100 - (100/(1+rs))

# Funciones para el calculo de nivels
def vwap(new, close, volume, index, digit: int) -> float:
    """Generator para calcular el VWAP de la columna new que se le pase: Session, Week o Month

    Args:
        new (pd.Serie): Columna NewSession, NewWeek o NewMonth
        close (pd.series): Columna Close.
        volume (pd.series): Columna Volume.
        index ([type]): (pd.series): Columna Index.
        digit (int): Numero de digitos del precio del instrumento

    Yields:
        Iterator[float]: Precio del VWAP
    """
    _sumpv, _sumvol = 0, 0
    for n,cl,vol,i in zip(new,close,volume,index):
        if n or i==0:
            _sumpv=0
            _sumvol=0      
        _sumpv += cl*vol
        _sumvol+= vol
        yield (round(_sumpv/_sumvol,digit) if _sumvol !=0 else 0)
        
def daily_change(_close,_last_day_close) -> float:
    """Generator que devuelve la variacion porcentual del precio de cierre de una vela respecto del cierre del día anterior

    Args:
        _close (pd.Serie):          Columna con los precios de cierre de las velas
        _last_day_close (pd.Serie): Columna con los precios de cierre del día anterior

    Yields:
        Iterator[float]: Variacioón porcentual con dos decimales 
    """
    for cl, ldc in zip(_close,_last_day_close):
        yield 0 if ldc==0 else round(((cl-ldc)/ldc)*100,2)
               
def current_day_level(new,levels,type: str) -> float:
    """Generator que calcula el High o Low del día actual

    Args:
        new (pd.Serie): Columna NewSession
        levels (pd.Serie): Columna High o Low 
        type (str): [description]

    Yields:
        Iterator[float]: Valor de High o Low
    """
    _level=0 if type=='High' else 1000000
    for _n,_l in zip(new,levels):
        if _n:
            _level=0 if type=="High" else 1000000
        if (type == 'High' and _l >= _level) or (type != 'High' and _l <= _level):
            _level=_l
        yield _level        
        
def last_day_level(_new,_level):
    """Generator que devuelve el nivel high o low del día anterior. Necesita que las columnas Current_Day_High, Currrent_Day_Low o Close se hayan calculado previamente

    Args:
        _new (pd.Serie): Columna NewSession
        _level (pd.Serie): Columna Current_Day_ High, Current_Day_Low o Close

    Yields:
        [type]: [float]: Valor del High o Low del día anterior
    """
    _last_day_level=0
    _last_level=0
    for _cont, (_n, _l) in enumerate(zip(_new,_level)):
        if _n and _cont!=0:
            _last_day_level=_last_level
        _last_level=_l
        yield _last_day_level
        
def pivot_points(high, low, close, digit: int,level: str)-> float:
    """Funcion que calcula los Pivot Points

    Args:
        high (pd.Serie): Columna High
        low (pd.Serie): Columna Low
        close (pd.Serie): Columna Close
        digit (int): Digitos del precio del instrumento
        level (str): Nivel: PP,S1,S2,S3,R1,R2,R3

    Returns:
        float: Valor del nivel solicitado
    """
    PP = round((high+low+close)/3,digit)
    if level == 'S1':
        return 2*PP-high
    elif level == 'S2':
        return PP + low - high
    elif level == 'S3':
        return low - 2*(high - PP)
    elif level == 'R1':
        return 2*PP - low
    elif level == 'R2':
        return PP + high - low
    elif level == 'R3':
        return high + 2*(PP - low)
    else: 
        return PP
    
def zce_level(_new, _open, _high, _low, _close, _index, _askedLevel:str):
    """Generator que calcula la Zona Control por Estructura que se le pida: Week o Month. High o Low

    Args:
        _new (pd.Serie): Columna NewWeek o NewMonth
        _open (pd.Serie): Columna Open
        _high (pd.Serie): Columna High
        _low (pd.Serie): Columna Low
        _close (pd.Close): Columna Close
        _index (pd.Serie): Columna Index
        _askedLevel (str): 'High' o 'Low'

    Yields:
        [type]: Valor del nivel
    """
    c_open, c_high, c_low, c_close, zce_high, zce_low = 0,0,0,0,0,0    
    for nw,op,hi,lo,cl,i in zip(_new,_open,_high,_low,_close,_index):
        if i ==  0:
            c_open = op
            c_high= hi
            c_low= lo
            c_close= cl

        if nw and i!=0:
            if c_close>c_open:
                zce_high = c_high
                zce_low = c_close
            else:
                zce_high =c_close
                zce_low = c_low
            c_open = op
            c_high = hi
            c_low = lo

        c_high = hi if hi > c_high else c_high
        c_low  = lo if lo < c_low  else c_low
        c_close = cl       

        yield zce_high if _askedLevel=='High' else zce_low    

def zcc_level(_time, _newSession,  _index, _open, _high, _low, _close, _volume, _day:int, _askedLevel: str)-> float:
    """Generator que calcula la Zona de Control Climatica horaria del día y nivel que se pida

    Args:
        _time (pd.Serie): Columna Time
        _newSession (pd.Serie): Columna NewSession
        _index (pd.Serie): Columna Index
        _open (pd.Serie): Columna Open
        _high (pd.Serie): Columna High
        _low (pd.Serie): Columna Low
        _close (pd.Serie): Columna Close
        _volume (pd.Serie): Columna Volume
        _day (int): Día solicitado:  1: Lunes, 2:Martes, 3: Miércoles, 4: Jueves, 5: Viernes
        _askedLevel (str): High, Low, Hour (devuelve la hora a la que se produce la ZCC), Volume (devuelve el volume de la ZCC)
    Yields:
        Iterator[float]: Valor del nivel
    """

    #Iniciamos las variables
    zcc_high_prov = zcc_low_prov = zcc_high = zcc_low = h1_open = h1_high = h1_low = 0        
    zcc_hour_prov = zcc_hour = zcc_vol_prov = zcc_vol = 0
    market_day=1
    
    for tm,nws,i,op,hi,lo,cl,vol in zip(_time, _newSession, _index, _open, _high, _low, _close, _volume):
        if i == 0: 
            zcc_high = zcc_high_prov = 0
            zcc_low = zcc_low_prov = 0    
            zcc_hour_prov = zcc_hour = tm.hour
            zcc_vol_prov = zcc_vol = vol
            h1_open = op
            h1_high = hi
            h1_low =  lo
            market_day = (tm.weekday()+2) if (tm.weekday()+2 < 7) else 1 
        
        h1_high = hi if hi > h1_high else h1_high
        h1_low = lo if lo < h1_low else h1_low
        
        if tm.minute == 55:
            if vol > zcc_vol_prov:
                zcc_high_prov = h1_high if cl > h1_open else cl
                zcc_low_prov =  cl if cl > h1_open else h1_low
                zcc_hour_prov = tm.hour
                zcc_vol_prov = vol
        
        if tm.minute==0:
            h1_open = op
            h1_high = hi
            h1_low = lo
            
        if nws and i!=0:
            if market_day < _day < 5:
                zcc_high = zcc_low = 0
                zcc_hour = 0
                zcc_vol = 0
            if _day == market_day: 
                zcc_high = zcc_high_prov
                zcc_low =  zcc_low_prov
                zcc_hour = zcc_hour_prov
                zcc_vol = zcc_vol_prov
            
            market_day = (tm.weekday()+2) if (tm.weekday()+2 < 7) else 1 
            zcc_high_prov =0
            zcc_low_prov = 0         
            h1_open = op
            h1_high = hi
            h1_low = lo
            zcc_vol_prov = vol
            zcc_hour_prov = tm.hour
            
        if _askedLevel == "High":
            yield zcc_high
        elif _askedLevel == "Low":
            yield zcc_low
        elif _askedLevel == "Hour":
            yield zcc_hour
        elif _askedLevel == "Volume":
            yield zcc_vol

def dp(_open,_high,_low,_close, _mvc,_range_min,_br_min, _mvc_max,_delta,_delta_check, _ticksize)-> bool:  
    """Funcion que calcula si una vela es un decision point

    Args:
        _open (pd.Serie o float): Columna Open o valor del Open
        _high (pd.Serie o float): Columna High o valor del High
        _low (pd.Serie o float): Columna Low o valor del Low
        _close (pd.Serie o float): Columna Close o valor del Close
        _mvc (pd.Serie o float): Columna MVC o valor del MVC
        _range_min (int): Valor min del rango de la vela para que sea DP
        _br_min (float): Valor min del ratio cuerpo / rango para que sea DP
        _mvc_max (int): Valor de la posicion máxima del MVC en % 
        _delta (int): Columna Delta o valor del Delta
        _delta_check (bool): Comprobacion del delta. Si es True el delta de la vela tiene que tener la misma direccion que la vela
        _ticksize (float): Valor del tick del instrumento

    Returns:
        bool: True si se cumplen todas las condiciones y es un DP. False si no
    """
    _range = ((_high-_low)/_ticksize)+1
    _body = (abs(_open-_close)/_ticksize)+1
    _br = int((_body/_range)*100)
    _mvc_per = candle_mvc_percentage(_open,_high,_low,_close,_mvc)
   
    #Hipotesis 1: Rango Minimo    
    _hip1 = True if _range>_range_min else False

    #Hipotesis 2: Ratio Body/Range Minimo    
    _hip2=True if _br>=_br_min else False

    #Hipotesis 3: MVC mayor que el minimo    
    _hip3=True if _mvc_per<=_mvc_max else False    
       
    #Hipotesis 4: Si esta activa, compatibilidad del delta
    _hip4=True
    if _delta_check:
        #Vela alcista
        if _open<_close:     
            if _delta<0:
                _hip4=False
        #Vela bajista
        else:
            if _delta>0:
                _hip4=False
    #Verificacion
    if _hip1 and _hip2 and _hip3 and _hip4:
        return True
    
    return False   

def market_session_level(_new,_levels,_session,_type,_marketsession)-> float:
    """Generator que devuelve el máximo o minimo de la session de mercado que se pida

    Args:
        _new (pd.Serie): Columna NewSession
        _levels (pd.Serie): Columna High o Low segun se esté calculando el High o Low de cada session de mercado
        _session (pd.Serie): Columna Session
        _type (str): High o Low
        _marketsession (str): Asia, EU o USA

    Yields:
        Iterator[float]: Valor de max o min de la sesion de mercado
    """
    _level=0 if _type=="High" else 1000000
    for _n,_l,_s in zip(_new,_levels,_session):
        if _n:
            _level=0 if _type=="High" else 1000000
        if _s==_marketsession:
            if _type=='High':
                if _l>=_level:
                    _level=_l
            else:
                if _l<=_level:
                    _level=_l
        yield _level