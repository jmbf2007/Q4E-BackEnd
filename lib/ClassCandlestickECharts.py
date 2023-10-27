import datetime as dt
from pandas import DataFrame
import numpy as np


SUBPLOT_PARAMETERS = ['volume','delta','result','balance','rsi','atr','ar','daily_change']

class CandelstickEChart():
    
#---- Constructor
    def __init__(self, data: DataFrame, result: DataFrame, show:dict, tooltip: dict, levels: list, positions: list, orders: list, impulses: list):
        self.data = data
        self.result = result
        self.show = show
        self.levels = levels
        self.positions = positions
        self.orders = orders
        self.impulses = impulses
        self.tooltip = tooltip
        
### ----------- Datos 

    @staticmethod
    def get_tooltip()->dict:
        return {
                "trigger": 'axis',
                "axisPointer": {
                    "type": 'cross'
                },
        }
    
    @staticmethod
    def axisPointer()->dict:
        """Devuelve la configuracion del axisPointer de Options. Este parametro indica la informacion de los ejes que se mostrará en el tooltip

        Returns:
            dict: Diccionario con la configuracion
        """
        return {
            "link": [
                {
                    "xAxisIndex": [0] 
                }
            ]        
        }
    
    def grid(self)-> list:
        """Metodo que devuelve la configuracion del parámetro grid de Option

       Returns:
            list: Lista con los diccionarios de cada elemento del grid
        """
        
        # Cuadro principal para el precio
        _grid = [
            {
                "left": '5%',
                "right": '5%',
                "top": 110,
                "height": 450
            },
        ]

        
        def top(i):
            return 110 if i==0 else (top(i-1)+height(i-1)+20)
        
        def height(i):
            return 450 if i==0 else 50            

        i = 1
        for key,value in self.show.items():
            if key in SUBPLOT_PARAMETERS and value:
                _grid.append({
                    "left": '5%',
                    "right": '5%',
                    "top": top(i),
                    "height": height(i)
                })
                i +=1
        
        return _grid
    
    def yAxis(self) -> list:
        """Metodo que devuelve la configuracion del parámetro yAxis de Option
            
        Returns:
            list: Lista con los diccionarios de cada eje Y 
        """
        #Iniciamos con el eje Y para el Precio
        _yAxis = [
            {        
                "scale": True,
                "gridIndex": 0,
                "splitNumber": 5,
                "splitArea": {"show": self.show['gridlines_y']},
                "axisLabel": {"show": True},
                "axisLine":  {"lineStyle": {"color": '#777'}, "show": False},
                "axisTick":  {"show": True},
                "splitLine": {"show": self.show['gridlines_y']},    
                "name": 'Price',
                "nameLocation": 'center',
                "nameGap": 55,
                "nameTextStyle": {
                    "color": "#777",
                    "fontSize": 12,
                }   
            }           
        ]     
        
        # Añadimos los subplots       
        grid = 1
        for sbplt in SUBPLOT_PARAMETERS:
            if self.show[sbplt]==True:
                _yAxis.append(
                    {        
                        "scale": True,
                        "gridIndex": grid,
                        "splitNumber": 2,
                        "splitArea": {"show": False},
                        "axisLabel": {"show": False},
                        "axisLine":  {"lineStyle": {"color": '#777'}, "show": False},
                        "axisTick":  {"show": False},
                        "splitLine": {"show": self.show['gridlines_y']},    
                        "name": sbplt.capitalize(),
                        "nameLocation": 'center',
                        "nameGap": 55,
                        "nameTextStyle": {
                            "color": "#777",
                            "fontSize": 12,
                        }   
                    })
                grid +=1
        

        return _yAxis
                    
    def xAxis(self) -> list:        
        """Metodo que devuelve la configuracion del parámetro xAxis de Option
            
        Returns:
            list: Lista con los diccionarios de cada eje X
        """        

        _data = self.data.Time.apply(lambda t: t.strftime("%Y-%m-%d %H:%M:%S"))
        _data = _data.tolist()
        # Iniciamos con el eje X para el Precio
        _xAxis = [
           {
                "type": "category",
                "data": _data,
                "boundaryGap": False,
                "scale": True,
                "splitLine": { "show": self.show['gridlines_x'] },
                "axisLine": {"lineStyle": {"color": "#777", "show": True}},
                "axisLabel": { "show": self.show['xaxe_date_label'] },
                "axisTick": { "show": True },
                "axisPointer": {
                    "show": True,
                    "type": "shadow",
                    "label": {"show": True},
                    "triggerTooltip": True,
                    "handle": {
                        "show": False,
                        "margin": 30,
                        "color": '#B80C00'             
                    },                
                }  
           }
        ]
       
        # Añadimos los ejes x de los subplots
        grid = 1
        for key,value in self.show.items():
            if key in SUBPLOT_PARAMETERS and value:
                _xAxis.append(
                    {        
                        "type": "category",
                        "gridIndex": grid,
                        "data": _data,
                        "boundaryGap": False,
                        "scale": True,
                        "splitLine": { "show": self.show['gridlines_x'] },
                        "axisLabel": { "show": False },
                        "axisTick": { "show": True },
                        "axisLine": { "lineStyle": { "color": '#777',"show": True } },
                        "axisPointer": {
                            "type": "shadow",
                            "label": {"show": True},
                            "triggerTooltip": True,
                            "handle": {
                                "show": False,
                                "margin": 30,
                                "color": '#B80C00'
                            } 
                        }
                    }
                )
                grid +=1
        
        return _xAxis

    def dataZoom(self)-> list:
        """Metodo que devuelve la configuracion del dataZoom del Option

        Args:
            chart_show (list): Lista con los valores de las variables de estado chart_show: Volume, Delta, Result, Balance

        Returns:
            list: Lista con las opciones del zoom
        """

        _xAxisIndex = [0]
        i=1
        for key,val in self.show.items():
            if key in SUBPLOT_PARAMETERS and val:
                _xAxisIndex.append(i)
                i +=1
        
        return  [
            {
                "type": 'inside',
                "xAxisIndex": _xAxisIndex,
                "start": 90,
                "end": 100
            },
            {
                "show": True,
                "xAxisIndex": _xAxisIndex,
                "type": 'slider',
                "top": '5%',
                "start": 90,
                "end": 100
            }
        ]
    
    def series(self) -> list:
        """
        Método que devuelve la lista Serie de Options
        """  

        self.initialize_serie()

      # On chart trazas  
       # MVC
        if  self.show['mvc']:
            self.serie.append(self.mvc())

       # DP  
        if self.show['dp']:    
            self.dp()            
                      
       # TC
        if self.show['tc']:
            self.touch_candles()
        
       # Trades
        if self.show['trades']:
            self.trades_lines()                                                     

        # Ordenes
        if self.show['orders']:
            self.orders_lines()           
       
        # NewSession
        if self.show['new_day']:
            self.newsession()

        # New Week
        if self.show['new_week']:
            self.newweek()

        # New Month
        if self.show['new_month']:
            self.newmonth()
            
        # VWAP
        if self.show['session_vwap']:
            self.append_on_chart_serie(column="Session_VWAP", name="Session VWAP", color="magenta")
        
        if self.show['week_vwap']:
            self.append_on_chart_serie(column="Week_VWAP", name="Week VWAP", color="#5B33FF", linetype='dashed')

        if self.show['month_vwap']:
            self.append_on_chart_serie(column="Month_VWAP", name="Month VWAP", color="#33FF8D", linetype='dotted')   

        # Pivot Points
        if self.show['pivot_points']:
            self.pivot_point()

        # Impulsos
        if self.show['impulses']:
            self.get_impulses()

        # TLS
        if self.show['tls']:
            self.tls()        
      
      # Subplots
        next_subplot = 1                    # Contador para indicar en que grid se dibujara el siguiente subplot activo
       # Volume
        if self.show['volume']:
            self.volume(next_subplot)
            next_subplot +=1                # Incrementamos el contador de next_subplot
  
       # Delta
        if self.show['delta']:
            self.delta(next_subplot)
            next_subplot +=1
              
       # Result
        if self.show['result']:
            self.trade_result(next_subplot)
            next_subplot +=1

       # Daily Balance
        if self.show['balance']:
            self.daily_balance(next_subplot)
            next_subplot +=1
               
       # Indicadores
        # RSI
        if self.show['rsi']:
            self.append_subplot_serie('RSI','RSI',next_subplot)
            next_subplot +=1

        # ATR
        if self.show['atr']:
            self.append_subplot_serie('ATR','ATR',next_subplot)
            next_subplot +=1

        # AR
        if self.show['ar']:
            self.append_subplot_serie('AR','AR',next_subplot)
            next_subplot +=1

        if self.show['daily_change']:
            self.append_subplot_serie('Daily_Change','Daily Change',next_subplot)
            next_subplot +=1

       # Return     
        return self.serie 


    # Método que devuelve el diccionario con la configuracion del option
    def getOption(self)-> dict:
        return {
            "progressive": 300,
            "tooltip": self.get_tooltip(),
            "axisPointer": self.axisPointer(),
            "grid": self.grid(),
            "xAxis": self.xAxis(),
            "yAxis": self.yAxis(),
            "dataZoom": self.dataZoom(),
            "series": self.series()            
        }       
        

### ------------ On Chart Plots ----------------------------------------

    # Metodo que inicializa la serie de datos
    def initialize_serie(self) -> None:
        self.serie =[
            {          
                "name": "",
                "type": "candlestick",
                #"data": list(trans_data(self.data.Open, self.data.Close, self.data.Low, self.data.High)),  # El formato de data es una lista de listas [[Open,Close,Low,High]]
                "data": [[op, cl, lw, hg] for op, cl, lw, hg in zip(self.data.Open, self.data.Close, self.data.Low, self.data.High)],
                "itemStyle": {
                    "color": "lime",
                    "color0": "red",
                    "borderColor": "green",
                    "borderColor0": "firebrick"
                },
                "markLine": {"data": [],
                             "symbol": ['none','none'] },                                                       # Diccionario para las lineas del grafico                                            
                "markPoint": { "data": []},                                                     # Diccionario para los puntos del grafico                                            
            },           
        ]

    # Serie de puntos del MVC
    def mvc(self)->dict:
        return {
            "name": "MVC",
            "type": "scatter",
            "symbolSize": 2,
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "data": self.data.MVC.tolist(),
            "itemStyle": {
                "color": "orange",
            },
        }

    # Serie de lineas de los DP
    def dp(self) -> list:      
        for dp in [x for x in self.levels if x['level_type']=='DP' and not x['active']] :
            self.serie[0]["markLine"]["data"].append([ 
                {
                    "coord": [dp['start_time'].strftime("%Y-%m-%d %H:%M:%S"),dp['price']],
                    "symbol": 'none',
                    "symbolsize": 10,    
                    "lineStyle":{                                
                        "normal": {
                            "type": 'dotted',
                            "color": 'rgb(48,177,242)',
                            "width": 1.5
                        }
                    }                        
                },
                {
                    "coord": [dp['end_time'].strftime("%Y-%m-%d %H:%M:%S"),dp['price']],
                    "symbol": 'none',
                    "symbolsize": 10,  
                }])

    # Serie para las Touch Candles
    def touch_candles(self) -> dict:
        return {
            "name": "TC",
            "type": "scatter",
            "symbolSize": 30,
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "data": self.data.Close.tolist(),
            "itemStyle": {
                "color": "pink",
            },
            "tooltip": {                
            },
        }


    # Serie para los lineas de los trades
    def trades_lines(self) -> None:
        for position in self.positions: 
            self.serie[0]['markLine']['data'].append([
                    {
                        "coord": [position['open_time'].strftime("%Y-%m-%d %H:%M:%S"),position['open_price']],                  # Coordenadas del punto de inicio
                        "symbol": "triangle",                                                                                   # Simbolo del punto de incio
                        "symbolsize": 10,                                                                                       # Tamaño del simbolo
                        "symbolRotate": 0 if position['trade_type']=='buy' else 180,                                            # Angulo de rotacion del simbolo: buy triangulo con vertice hacia arriba
                        "itemStyle": {                                                                                          # Propiedades del simbolo. Color verde para buy
                            "color": '#3349FF' if position['trade_type']=='buy' else '#FF33A2',
                        },           
                        "lineStyle":{                                                                                           # Propiedades para la linea
                            "normal": {
                                "type": 'dashed',
                                "color": '#3349FF' if position['trade_type']=='buy' else '#FF33A2',
                                "width": 1.5
                            }
                        }  
                    },
                    {
                        "coord": [position['close_time'].strftime("%Y-%m-%d %H:%M:%S"),position['close_price']],                # Coordenadas del punto final 
                        "symbol": "triangle",                                                                                   # Simbolo del punto final   
                        "symbolSize": 10,                                                                                       # Tamaño del simbolo
                        "symbolRotate": 180 if position['trade_type']=='buy' else 0,                                            # Angulo de rotacion del simbolo: buy triangulo con vertice hacia abajo
                        "itemStyle": {                                                                                          # Propiedades del simbolo. Color verde para buy
                            "color": '#3349FF' if position['trade_type']=='buy' else '#FF33A2',
                        }      
                    }
                ])
 
    # Serie para las ordenes
    def orders_lines(self) -> None:
        for order in self.orders:
            self.serie[0]['markLine']['data'].append([
                    {
                        "coord": [order['open_time'].strftime("%Y-%m-%d %H:%M:%S"),order['open_price']],                      # Coordenadas del punto de inicio
                        "symbol": "circle",                                                                                   # Simbolo del punto de incio
                        "symbolsize": 10,                                                                                       # Tamaño del simbolo
                        "symbolRotate": 0 if 'buy' in order['order_type'] else 180,                                            # Angulo de rotacion del simbolo: buy triangulo con vertice hacia arriba
                        "itemStyle": {                                                                                          # Propiedades del simbolo. Color verde para buy
                            "color": 'blue' if order['action']=='entry' else 'gray',
                        },           
                        "lineStyle":{                                                                                           # Propiedades para la linea
                            "normal": {
                                "type": 'dashed',
                                "color": 'blue' if order['action']=='entry' else 'gray',
                                "width": 1.5
                            }
                        }  
                    },
                    {
                        "coord": [order['close_time'].strftime("%Y-%m-%d %H:%M:%S"),order['open_price']],                # Coordenadas del punto final 
                        "symbol": "triangle" if order['action']=='entry' else 'rect',                                                                                   # Simbolo del punto final   
                        "symbolSize": 
                            
                            10,                                                                                       # Tamaño del simbolo
                        "symbolRotate": 180 if 'buy' in order['order_type'] else 0,                                            # Angulo de rotacion del simbolo: buy triangulo con vertice hacia abajo
                        "itemStyle": {                                                                                          # Propiedades del simbolo. Color verde para buy
                            "color": 'blue' if order['action']=='entry' else 'gray',
                        }      
                    }
                ])
 
    # Lineas para los new Session
    def newsession(self) -> None:
        for time,new in zip(self.data.Time, self.data.NewSession):
            if new:
                self.serie[0]['markLine']['data'].append(
                    {   
                        "name": "",
                        "xAxis": time.strftime("%Y-%m-%d %H:%M:%S"), 
                        "label":  {
                            "show": False
                        }                     
                    })
    
    # Lineas para los new Week
    def newweek(self) -> None:
        for time,new in zip(self.data.Time, self.data.NewWeek):
            if new:
                self.serie[0]['markLine']['data'].append(
                    {   
                        "name": "NewWeek",
                        "xAxis": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "lineStyle":{                                                                                           # Propiedades para la linea
                            "normal": {
                                "type": 'dashed',
                                "color": 'orange',
                                "width": 3
                            }
                        },
                        "label":  {
                            "show": False
                        }
                        
                    })        
    
    # Lineas para los new Month
    def newmonth(self) -> None:
        for time,new in zip(self.data.Time, self.data.NewMonth):
            if new:
                self.serie[0]['markLine']['data'].append(
                    {   
                        "name": "",
                        "xAxis": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "lineStyle":{                                                                                           # Propiedades para la linea
                            "normal": {
                                "type": 'dashed',
                                "color": 'pink',
                                "width": 5
                            }
                        },
                        "label":  {
                            "show": False
                        }
                        
                    }) 
    
    # Método que añade una serie de datos que esté con columnas de data  
    def append_on_chart_serie(self, column: str, name: str, color: str, linetype: str="solid",width: int=1):
        """
        Tipos de linea: solid, dashed, dotted
        """
        for day in range(1,self.data.Market_Day.iat[-1]+1):
            _data = list(map(lambda marketday, value: value if day==marketday else None, 
                                self.data.Market_Day,
                                self.data[column]))
            self.serie.append(
                {
                    "name": f"{name} day {day}",
                    "type": "line",   
                    "data": _data,         
                    "xAxisIndex": 0,
                    "yAxisIndex": 0,
                    "lineStyle": {
                        "color": color,
                        "width": width,
                        "type": linetype,
                    }, 
                    "tooltip": {"show": False},                                          
                }           
            )

    # Setie para los Pivot Points
    def pivot_point(self) -> None:
        for day in list(set(self.data.Market_Day.tolist())):
            _data = self.data[['Time','PP','S1','S2','S3','R1','R2','R3']].loc[self.data.Market_Day==day]    
            # PP 
            self.serie[0]["markLine"]["data"].append([
                {
                    "coord": [_data.Time.iat[0].strftime("%Y-%m-%d %H:%M:%S"),_data.PP.iat[0]],
                    "symbol": 'none',
                    "symbolsize": 10,    
                    "lineStyle":{                                
                        "normal": {
                            "type": 'dashed',
                            "color": 'rgb(48,177,242)',
                            "width": 1
                        }
                    }, 
                    "textStyle":{
                        "text": "PP",
                        "fontSize": 8,                            
                    } 
                                        
                },
                {
                    "coord": [_data.Time.iat[-1].strftime("%Y-%m-%d %H:%M:%S"),_data.PP.iat[-1]],
                    "symbol": 'none',
                    "symbolsize": 10,  
                }
            ])
            # R1 
            self.serie[0]["markLine"]["data"].append([
                {
                    "coord": [_data.Time.iat[0].strftime("%Y-%m-%d %H:%M:%S"),_data.R1.iat[0]],
                    "symbol": "none",
                    "symbolsize": 10,    
                    "lineStyle":{                                
                        "normal": {
                            "type": "dotted",
                            "color": "rgb(68,177,242)",
                            "width": 1
                        }
                    }                        
                },
                {
                    "coord": [_data.Time.iat[-1].strftime("%Y-%m-%d %H:%M:%S"),_data.R1.iat[-1]],
                    "symbol": "none",
                    "symbolsize": 10,  
                }
            ])
            # R2 
            self.serie[0]["markLine"]["data"].append([
                {
                    "coord": [_data.Time.iat[0].strftime("%Y-%m-%d %H:%M:%S"),_data.R2.iat[0]],
                    "symbol": 'none',
                    "symbolsize": 10,    
                    "lineStyle":{                                
                        "normal": {
                            "type": "dotted",
                            "color": 'rgb(88,177,242)',
                            "width": 1
                        }
                    }                        
                },
                {
                    "coord": [_data.Time.iat[-1].strftime("%Y-%m-%d %H:%M:%S"),_data.R2.iat[-1]],
                    "symbol": 'none',
                    "symbolsize": 10,  
                }
            ]) 
            # R3 
            self.serie[0]["markLine"]["data"].append([
                {
                    "coord": [_data.Time.iat[0].strftime("%Y-%m-%d %H:%M:%S"),_data.R3.iat[0]],
                    "symbol": 'none',
                    "symbolsize": 10,    
                    "lineStyle":{                                
                        "normal": {
                            "type": "dotted",
                            "color": 'rgb(108,177,242)',
                            "width": 1
                        }
                    }                        
                },
                {
                    "coord": [_data.Time.iat[-1].strftime("%Y-%m-%d %H:%M:%S"),_data.R3.iat[-1]],
                    "symbol": 'none',
                    "symbolsize": 10,  
                }
            ]) 
            # S1 
            self.serie[0]["markLine"]["data"].append([
                {
                    "coord": [_data.Time.iat[0].strftime("%Y-%m-%d %H:%M:%S"),_data.S1.iat[0]],
                    "symbol": 'none',
                    "symbolsize": 10,    
                    "lineStyle":{                                
                        "normal": {
                            "type": "dotted",
                            "color": 'rgb(48,157,242)',
                            "width": 1
                        }
                    }                        
                },
                {
                    "coord": [_data.Time.iat[-1].strftime("%Y-%m-%d %H:%M:%S"),_data.S1.iat[-1]],
                    "symbol": 'none',
                    "symbolsize": 10,  
                }
            ])
            # S2 
            self.serie[0]["markLine"]["data"].append([
                {
                    "coord": [_data.Time.iat[0].strftime("%Y-%m-%d %H:%M:%S"),_data.S2.iat[0]],
                    "symbol": 'none',
                    "symbolsize": 10,    
                    "lineStyle":{                                
                        "normal": {
                            "type": "dotted",
                            "color": 'rgb(48,137,242)',
                            "width": 1
                        }
                    }                        
                },
                {
                    "coord": [_data.Time.iat[-1].strftime("%Y-%m-%d %H:%M:%S"),_data.S2.iat[-1]],
                    "symbol": 'none',
                    "symbolsize": 10,  
                }
            ]) 
            # S3 
            self.serie[0]["markLine"]["data"].append([
                {
                    "coord": [_data.Time.iat[0].strftime("%Y-%m-%d %H:%M:%S"),_data.S3.iat[0]],
                    "symbol": 'none',
                    "symbolsize": 10,    
                    "lineStyle":{                                
                        "normal": {
                            "type": "dotted",
                            "color": 'rgb(48,117,242)',
                            "width": 1
                        }
                    }                        
                },
                {
                    "coord": [_data.Time.iat[-1].strftime("%Y-%m-%d %H:%M:%S"),_data.S3.iat[-1]],
                    "symbol": 'none',
                    "symbolsize": 10,  
                }
            ])

    # Serie para los impulsos 
    def get_impulses(self) -> None:
        for impulse in self.impulses:
            x0 = impulse['initial'][0].strftime("%Y-%m-%d %H:%M:%S")
            y0 = impulse['initial'][1]
            x1 = impulse['final'][0].strftime("%Y-%m-%d %H:%M:%S")
            y1 = impulse['final'][1]
            direction = impulse['direction']
            self.serie[0]['markLine']['data'].append([
                    {
                        "coord": [x0, y0],                      # Coordenadas del punto de inicio   
                        "lineStyle":{                                                                                           # Propiedades para la linea
                            "normal": {
                                "type": 'dashed',
                                "color": 'blue' if direction==1 else 'purple',
                                "width": 1.0
                            }
                        }  
                    },
                    {
                        "coord": [x1,y1],                # Coordenadas del punto final 
                    }
                ])

    # Serie para los TLS
    def tls(self) -> None:
        # Los TLS estan en la columna TLS_Result del data. Primero extraermos los TLS_Result 1 que indican Largos Atrapados  y los TLS_Result -1 que indican Cortos Atrapados. Nos quedamos con la culumna Time donde aparecen
        _trapped_long_time = self.data.Time[self.data.TLS_Result==1]
        _trapped_long_high = self.data.High[self.data.TLS_Result==1]
        _tls_upper_delta = self.data.TLS_Upper_Delta[self.data.TLS_Result==1]
        _tls_upper_ask_percentage = self.data.TLS_Upper_Ask_Percentage[self.data.TLS_Result==1]
        _tls_upper_asl_levels_percentage = self.data.TLS_Upper_Ask_Levels_Percentage[self.data.TLS_Result==1]
        _tls_upper_tooltip = [f"Upper Delta: {delta} \nAsk%: {ask} \nAsk Levels%: {asl}" for delta,ask,asl in zip(_tls_upper_delta,_tls_upper_ask_percentage,_tls_upper_asl_levels_percentage)]


        # Creamos la serie para los largos atrapados. Seran tipo MarkPoint
        for time,high,tooltip in zip(_trapped_long_time,_trapped_long_high,_tls_upper_tooltip):
            self.serie[0]['markPoint']['data'].append(
                {
                    "name": "Trapped Long",
                    "coord": [time.strftime("%Y-%m-%d %H:%M:%S"),high],
                    'value': tooltip,
                    "itemStyle": {
                        "color": "green",
                    },
                    "symbolSize": 10,
                    "label": {
                        "offset": [0, -10],  # Añade esta línea para desplazar la marca 5 unidades hacia arriba
                    }, 
                    'tooltip': {
                        'formatter': tooltip
                    }
                }
            )
        
        # Creamos la serie para los cortos atrapados. Seran tipo MarkPoint
        _trapped_short_time = self.data.Time[self.data.TLS_Result==-1]
        _trapped_short_low = self.data.Low[self.data.TLS_Result==-1]
        _tls_lower_delta = self.data.TLS_Lower_Delta[self.data.TLS_Result==-1]
        _tls_lower_bid_percentage = self.data.TLS_Lower_Bid_Percentage[self.data.TLS_Result==-1]
        _tls_lower_asl_levels_percentage = self.data.TLS_Lower_Bid_Levels_Percentage[self.data.TLS_Result==-1]
        _tls_lower_tooltip = [f"Lower Delta: {delta} \nBid%: {bid} \nBid Levels%: {asl}" for delta,bid,asl in zip(_tls_lower_delta,_tls_lower_bid_percentage,_tls_lower_asl_levels_percentage)]
        for time,low,tooltip in zip(_trapped_short_time,_trapped_short_low, _tls_lower_tooltip):
            self.serie[0]['markPoint']['data'].append(
                {
                    "name": "Trapped Short",
                    "coord": [time.strftime("%Y-%m-%d %H:%M:%S"),low],
                    "itemStyle": {
                        "color": "red",
                    },
                    "value": "TS",
                    "symbolRotate": 180, 
                    "symbolSize": 10,
                    "label": {
                        "offset": [0, 10],  # Añade esta línea para desplazar la marca 5 unidades hacia arriba
                    },
                    'tooltip': {
                        'formatter': tooltip
                    }
                }
            )


### -------------- Subplots --------------------------------------

    # Serie para el subplot Volume
    def volume(self,next_subplot: int) -> None:
        self.serie.append(
                {
                    "name": "Volume",
                    "type": "bar",   
                    "data": self.data.Volume.tolist(),         
                    "xAxisIndex": next_subplot,
                    "yAxisIndex": next_subplot,
                    "itemStyle": {
                        "color": "blue",
                    },
                    "large": True 
                }    
            )
    
    # Serie para el subplot Delta
    def delta(self, next_subplot: int) -> None:
        _color = ["green" if delta>=0 else "red" for delta in self.data.Delta.tolist()] 
        self.serie.append(
            {
                "name": "Delta",
                "type": "bar",   
                "data": self.data.Delta.tolist(),     
                "xAxisIndex": next_subplot,
                "yAxisIndex": next_subplot,
                "itemStyle": {
                    "color": _color ,
                },
                "large": True, 
                
            }
        )
    
    # Serie para el subplot Result    
    def trade_result(self, next_subplot: int) -> None:      
        position_close_time = [pos['close_time'] for pos in self.positions]
        position_result = [pos['cash_result'] for pos in self.positions]        
        _result = []
        for time in (self.data.Time):
            if time in position_close_time:
                _result.append(position_result[position_close_time.index(time)])
            else:
                _result.append(0)

        self.serie.append(
            {
                "name": "Result",
                "type": "bar",   
                #"data": [ position_result[position_close_time.index(time)] for time in self.data.Time if time in position_close_time else 0 ] ,         
                "data": _result,
                "xAxisIndex": next_subplot,
                "yAxisIndex": next_subplot,
                "colorBy": "data",
                "large": True                                       
            }
        )

    # Serie para el subplot Daily Balance
    def daily_balance(self, next_subplot: int) -> None:
        _balance = []
        _last_balance = 0 
        position_close_time = [pos['close_time'] for pos in self.positions]
        position_result = [pos['cash_result'] for pos in self.positions]
        for _time,_new in zip(self.data.Time,self.data.NewSession):            
            if _new:
                _last_balance = 0

            if _time in position_close_time:
                _last_balance +=  position_result[position_close_time.index(_time)]            
            _balance.append(_last_balance)
        
        self.serie.append(
            {
                "name": "DailyBalance",
                "type": "bar",   
                "data": _balance,         
                "xAxisIndex": next_subplot,
                "yAxisIndex": next_subplot,
                "colorBy": "data",
                "large": True                                       
            }
        )

    
    # Indicadores
    def append_subplot_serie(self, column: str, name: str, next_subplot: int) -> None:
        _data = [0 if np.isnan(x) else x for x in self.data[column]]
        self.serie.append(
            {
                "name": name,
                "type": "line",   
                "data": _data,         
                "xAxisIndex": next_subplot,
                "yAxisIndex": next_subplot,
                "colorBy": "data",
                "large": True                                       
            }
        )




            
        
        
