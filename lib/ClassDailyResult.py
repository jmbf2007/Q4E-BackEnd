#------------------------------
# Importamos librerias externas
#------------------------------
import numpy as np
import pandas as pd 
import datetime as dt

from zmq import has 

#------------------------------
# Importamos Clases Propias
#-----------------------------
from lib.ClassBasicECharts import BasicEChart
from lib.ClassHistogramECharts import HistogramEChart
#------------------------------
# Clase
#------------------------------
class cDailyResult():

#---- Constructor. Recibe los datos en forma de dataframe con las columnas: MarketDay, Trades, Balance, TickPnL
    def __init__(self,marketdays,trades,balance,tickpnl,maxbalance,minbalance, initial_balance, load = False, empty=False):

        # Si se solicita un objeto vacío se devuelve aquí
        if empty:
            return

        if load == False:
            self.data = pd.DataFrame(columns=('MarketDay','Trades','Balance','TickPnL','MaxBalance','MinBalance','CumBalance','Balance_Percentage','CumBalance_Percentage'))
            self.data.MarketDay =marketdays
            self.data.Trades =trades
            self.data.Balance = balance
            self.data.TickPnL = tickpnl
            self.data.MaxBalance = maxbalance
            self.data.MinBalance = minbalance
            self.initial_balance = initial_balance
            self.Get_Attributes()
            self.get_balance_attributes()
 

#---- Bloque Métodos de la Clase
    # Método que calcula los atributos max, min y average
    def Get_Attributes(self):
        self.windays = len(self.data.Balance[self.data.Balance>0])
        self.lossdays = len(self.data.Balance[self.data.Balance<0])
        self.bevendays = len(self.data.Balance[self.data.Balance==0])
        
        self.maxbalance = self.data.Balance.max()
        self.maxtickpnl = self.data.TickPnL.max()
        self.maxtrades = self.data.Trades.max()
        self.bestbalance = self.data.MaxBalance.max()
        
        self.minbalance = self.data.Balance.min()
        self.mintickpnl = self.data.TickPnL.min()
        self.mintrades = self.data.Trades.min()
        self.worstbalance = self.data.MinBalance.min()

        if len(self.data)>0:
            self.windays_percentage = (self.windays/len(self.data))*100
            self.lossdays_percentage = (self.lossdays/len(self.data))*100
            self.bevendays_percentage = (self.bevendays/len(self.data))*100
            
            self.averagebalance = round(self.data.Balance.sum()/len(self.data),2)
            self.averagetickpnl = round(self.data.TickPnL.sum()/len(self.data),0)
            self.averagetrades = round(self.data.Trades.sum()/len(self.data),0)
            self.averagemaxbalance = round(self.data.MaxBalance.sum()/len(self.data),2)
            self.averageminbalance = round(self.data.MinBalance.sum()/len(self.data),2)
        
    def get_balance_attributes(self):
        # Daily Balance Acumulado
        def cumBalance(balance):
            cumbalance=0
            for dbl in balance:
                cumbalance += dbl
                yield cumbalance
            
        self.data.CumBalance = list(cumBalance(self.data.Balance))
        
        # Variacion porcentual del daily balance respecto del balance inicial

        if self.initial_balance>0:
            self.data.Balance_Percentage = self.data.Balance.apply(lambda bal: round((bal/self.initial_balance)*100,2))
            self.data.CumBalance_Percentage = self.data.CumBalance.apply(lambda cumbal: round((cumbal/self.initial_balance)*100,2))
        else:
            self.data.Balance_Percentage = None
            self.data.CumBalance_Percentage =None
                  
    # Método que devuelve el histograma de una distribución normal de los días 
    @staticmethod
    def get_dailyresulthistogram_option(data: np.array, _min: float, _max: float, param: dict) -> object:
        
        _step = param['step']
        _type = param['type']        

        # Para los datos
        _x1_data = [float(round(_min + _step * x, 2)) for x in range(int((_max - _min) / _step) + 1)]



        # Para las lineas de la media y std
        _x2_extremes = [min(_x1_data), max(_x1_data)]
        _mean = float(np.mean(data))
        _std1 = float(np.mean(data)-np.std(data))
        _std2 = float(np.mean(data)+np.std(data))  

        if _type=='Total days':
            _histogram = [((data >= _min + _step * x) & (data < (_min + _step * (x + 1)))).sum() for x in range(int((_max - _min) / _step) + 1)]
            _histogram = [int(h) for h in _histogram]
            _cumhistogram = [(data>=_min+_step*x).sum() for x in range(int((_max-_min)/_step)+1)]
            _histogram_name = 'Num of days(num)'
            _cumhistogram_name = 'Cumulative days(days>=)'
            _mean_name = 'Mean&Std(num)'
            _histogram_units = 'num'
            _cumhistogram_units = 'days>='
        else:
            _histogram = [round(((((data >= _min + _step * x) & (data < (_min + _step * (x + 1)))).sum()) / len(data)) * 100, 2) for x in range(int((_max - _min) / _step) + 1)]

            _histogram = [float(h) for h in _histogram]
            _cumhistogram = [round((((data>=_min+_step*x).sum())/len(data))*100,2) for x in range(int((_max-_min)/_step)+1)]
            _histogram_name = 'Num of days(%)'
            _cumhistogram_name = 'Cumulative Days(%>=)'
            _mean_name = 'Mean&Std(%)'
            _histogram_units = '%'
            _cumhistogram_units = '%>='       

        _cumhistogram =[float(c) for c in  _cumhistogram]
        data = {
            'histogram_xdata': _x1_data,
            'mean_xaxis_extremes': _x2_extremes,
            'histogram_ydata': _histogram,
            'histogram_units': _histogram_units,
            'histogram_trace_name': _histogram_name,
            'cumhistogram_ydata': _cumhistogram,
            'cumhistogram_units': _cumhistogram_units,
            'cumhistogram_trace_name': _cumhistogram_name,
            'mean_trace_name': _mean_name,
            'mean': _mean,      
            'std1': _std1,
            'std2': _std2            
        }

        echart = HistogramEChart(data)

        return echart.getOption()

    # Método que devuelve el histograma temporal de la propiedad que se le pida
    def get_dailybalances_option(self, param: dict):
        _attb = param['selected_attb_group']
        _xaxis_data=self.data.MarketDay.to_list()
        if _attb == "trades":
            _yaxis_data = [self.data.Trades.to_list()]
            _traces_name = ['Trades(num)']
            _traces_type = ['bar']
            _yaxis_name = ["Num"]            
            _yaxis_traces = [0] 
            _coloured_traces = [True]
        elif _attb == "balance":
            _yaxis_data = [self.data.Balance.to_list(), self.data.CumBalance.to_list()]
            _traces_name = ['Balance($)',"Net Cumulative Daily Balance(net$)"]
            _traces_type = ['bar','line']
            _yaxis_name= ["$","net$"]            
            _yaxis_traces = [0,1]     
            _coloured_traces = [True, False]        
        elif _attb=="tickpnl":
            _yaxis_data = [self.data.TickPnL.to_list()]
            _traces_name = ['TickPnL(ticks)']
            _traces_type = ['bar']
            _yaxis_name= ["ticks"]
            _yaxis_traces = [0] 
            _coloured_traces = [True]
        elif _attb=="maxbalance":
            _yaxis_data = [self.data.MaxBalance.to_list()]
            _traces_name = ['MaxBalance($)']
            _traces_type = ['bar']
            _yaxis_name = ["$"]
            _yaxis_traces = [0] 
            _coloured_traces = [False]
        elif _attb== ["minbalance"]:
            _yaxis_data = [self.data.MinBalance]
            _traces_name = ['MinBalance($)']
            _traces_type = ['bar']
            _yaxis_name=["$"]
            _yaxis_traces = [0]  
            _coloured_traces = [False]
        elif _attb=="dailybalancerange":            
            _yaxis_data = [self.data.Balance.to_list(),self.data.MaxBalance.to_list(), self.data.MinBalance.to_list()]
            _traces_name = ['Balance($)','MaxBalance($)','MinBalance($)']
            _traces_type = ['bar','scatter','scatter']
            _yaxis_name = ["$"]
            _yaxis_traces = [0,0,0]    
            _coloured_traces = [True, True, True]
            
        _data = {
            'xaxis_data': _xaxis_data,
            'xaxis_title': "Market Day",
            'yaxis_data': _yaxis_data,
            'yaxis_name': _yaxis_name,
            'yaxis_traces': _yaxis_traces,
            'traces_name': _traces_name,
            'traces_type': _traces_type,
            'coloured_traces': _coloured_traces       
        }
            
        echart = BasicEChart(_data)
    
        return echart.getOption()
        
    # Metodo que devuelve un dataframe resumen de los attributos 
    def get_summaryDataFrame(self,_attb):
        if _attb == "dailyresults":
      
            df = pd.DataFrame(columns=('Total','%'))
            row1=[self.windays,self.windays_percentage]
            row2=[self.lossdays,self.lossdays_percentage]
            row3=[self.bevendays,self.bevendays_percentage]
            df = df.append(row1)
            df = df.append(row2)
            df = df.append(row3)
            
            return df

        else:       
            if not hasattr(self,'averagetrades'):
                self.Get_Attributes()
            _columns=['Trades','TickPnL','Balance','MaxBalance','MinBalance']
            _index = ['Max','Min','Avrg']
            df = pd.DataFrame(index = _index, columns = _columns)
            _trades = [self.maxtrades, self.mintrades, self.averagetrades]
            _tickpnl = [self.maxtickpnl, self.mintickpnl, self.averagetickpnl]
            _balance = [self.maxbalance, self.minbalance, self.averagebalance]
            _maxbalance = [self.bestbalance, 0, self.averagemaxbalance]
            _minbalance = [0, self.worstbalance, self.averageminbalance]

            df.Trades =_trades
            df.TickPnL = _tickpnl
            df.Balance = _balance
            df.MaxBalance = _maxbalance
            df.MinBalance = _minbalance
            
            return df.to_json()
    
    # Método que devuelve el grafico de tarta del resumen
    def get_pie_echart(self)-> dict:
        if not hasattr(self,'windays'):
            self.Get_Attributes()
            
        _values=[self.windays,self.lossdays,self.bevendays]
        _labels=['Win days','Loss days','Break Even days']
        _colors=['green','red','blue']
        
        return {
            "tooltip": {"trigger": "item"},
            "title": {
                "text": f"Days: {self.windays+self.lossdays+self.bevendays}"    
            },
            "color": _colors,
            "lengend": {'show': True,'top': '5%', 'left': 'center'},
            "series": {
                "name": "Summary",
                "type": "pie",
                "radius": ['40%', '80%'],
                "avoidLabelOverlap": False,
                "itemStyle": {
                    "borderRadius": 10,
                    "borderColor": '#fff',
                    "borderWidth": 2
                },
                "label": {
                    "show": True,
                    "position": 'center',
                    "alignTo": 'laneline',
                    "bleedMargin": 5
                },
                "emphasis": {
                    "label": {
                        "show": True,
                        "fontSize": '40',
                        "fontWeight": 'bold'
                    }
                },
                "labelLine": {
                    "show": False
                },
                "data": [
                    {"value": _values[0], "name": _labels[0]},
                    {"value": _values[1], "name": _labels[1]},
                    {"value": _values[2], "name": _labels[2]},
                ]                
            }
        }
        
    # Método que devuelve el option para el heatmap del calendario
    def get_calendar_heatmap_option(self):
        pass
        

