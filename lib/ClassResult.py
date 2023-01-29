'''
'''

#------------------------------
# Importamos librerias externas
#------------------------------
import pandas as pd 
import math

import sys
sys.path.append("..")

#------------------------------
# Importamos Clases Propias
#-----------------------------

from lib.ClassDailyResult import cDailyResult
from lib.ClassBasicECharts import BasicEChart
from models.modelsSetting import Setting

RESULT_ATTRIBUTES = {'Total Trades':'total',
            'Total Win Trades':'win',
            'Total Loss Trades':'loss',
            'Total Doubt Trades':'doubt',
            'Total Breakeven Trades':'beven',
            'Partial Win Trades':'pwin',
            'Partial Loss Trades':'ploss',
            'Balance PnL Ticks':'tick_balance',
            'Average PnL Ticks':'avrg_ticks',
            'Cash Balance PnL':'cash_balance',
            'Average Cash Balance':'avrg_cash',
            'Cash Drawdown %':'cash_drawdown',
            'Max Cash Drawdown %':'cash_drawdown_max',
            'Total Win Ticks':'win_ticks',
            'Total Loss Ticks':'loss_ticks',
            'Average Win Ticks':'avrg_win_ticks',
            'Average Loss Ticks':'avrg_loss_ticks',
            'Best Trade Ticks':'best',
            'Worst Trade Ticks':'worst',
            'Ratio Win':'rwin',
            'Profit Factor':'profit_factor',
            'Recovery Factor':'recovery_factor',
            'Return of Investement(ROI)':'roi',
}


#------------------------------
# Clase
#------------------------------
class cResult():


#---- Constructor

  def __init__(self, setting: dict=None, data: list=None, empty: bool=False, wfa: bool=None) -> None:    
    # Si se solicita un objeto result vacío se devuelve aquí
    if empty:
      return

    self.setting = Setting(setting)
    if wfa: 
      self.data = None
      return

    self.data = pd.DataFrame(data)  
    self.get_all_result_attributes()  
    self.get_dailyresults()
    self.get_dailystatictis()

    

#---- Bloque para calcular las series de cada atributo

  #Metodo Tick_Balance
  def get_tick_balance(self):
    def Sum_Ticks(_data):
      _cont=0
      for r in _data:
        _cont += r
        yield _cont

    self.data['tick_balance']=list(Sum_Ticks(self.data.tick_result))
    # Los generator son mas rapidos que las list comprenhention
    #self.data['tick_balance'] = [sum(self.data.tick_result[:i+1]) for i in range(len(self.data.tick_result))]

  def get_cash_balance(self):
    self.get_cash_data()

  def get_cash_drawdown(self):
    self.get_cash_data()
  
  def get_cash_drawdown_max(self):
    self.get_cash_data()
    
  def get_roi(self):
    self.get_cash_data()
    
  def get_avrg_cash(self):
    self.get_cash_data()

  #Metodo para los atributos con cash
  def get_cash_data(self):
    #Generator para el cash Balance
    def sum_cash_balance(_data):
      _cont=0
      for r in _data:
        _cont += r
        yield _cont
            
    #Generator para el Cash_Balance_High
    def balance_high(_balance):
      _balance_high=self.setting.account.initial_balance
      for _bal in _balance:
          if _bal>_balance_high:
              _balance_high=_bal
          yield _balance_high  

    #Generator para el DD_Max
    def dd_max(_dd):
      _dd_max=0
      for d in _dd:
          if d>_dd_max:
             _dd_max=d
          yield _dd_max

    #Generator para el Average Cash
    def average_cash(_data):
      for _trades, balance in enumerate(_data, start=1):
        yield round(balance/_trades,2)

    self.data['cash_net_balance']=list(sum_cash_balance(self.data.cash_result))                                                
    #self.data['cash_net_balance'] = [sum(self.data.cash_result[:i+1]) for i in range(len(self.data.cash_result))]
    self.data['cash_balance'] =  self.data['cash_net_balance'] + self.setting.account.initial_balance
    self.data['cash_balance_high']=list(balance_high(self.data.cash_balance))
    #self.data['cash_balance_high'] = [max(self.data.cash_balance[:i+1]) for i in range(len(self.data.cash_balance))]
    self.data['cash_drawdown']=round(((self.data['cash_balance_high']-self.data['cash_balance'])/self.data['cash_balance_high'])*100,2) 
    self.data['trailing_drawdown']=self.data['cash_balance_high']-self.setting.account.trailing_dd
    self.data['cash_drawdown_max']=list(dd_max(self.data.cash_drawdown))
    #self.data['cash_drawdown_max'] = [max(self.data.cash_drawdown[:i+1]) for i in range(len(self.data.cash_drawdown))]
    self.data['avrg_cash']=list(average_cash(self.data.cash_balance))
    self.data['roi']=self.data['cash_net_balance']/self.setting.account.initial_balance

  #Metodo para Total Trades
  def get_total(self):
    self.data['total']=len(self.data.tick_result)

  #Metodo para contar Total: win, loss, doubt y beven
  def count_result(self, result: str):
    def count(trade_result, result):
      count=0
      for trade in trade_result:
        if (result == 'win' and trade in ['win','pwin']) or (result == 'loss' and trade in ['loss','ploss']) or (result == 'doubt' and trade == 'doubt') or (result == 'beven' and trade == 'beven'):
          count +=1 
        yield count
    
    if result not in ['win','loss','doubt','beven','pwin','ploss']:
      return
    
    self.data[result] = list(count(self.data.trade_result, result))
  
  #Método para rwin: Ratio Win 
  def get_rwin(self):
    for result in ['win','loss','doubt','beven','pwin','ploss']:
        self.count_result(result)

    self.data['rwin']=list(map(lambda win,loss,doubt,beven:
                           round(((win)/(win+loss+doubt+beven))*100,2) if (win+loss+doubt+beven)!=0 else 0, 
                           self.data.win, self.data.loss, self.data.doubt, self.data.beven))
  
  #Método que calcula el ratio win de un numero de trades
  def get_mean_rwin(self,period):
    def rwin_mean(rs):
      return round(sum(1 if x>0 else 0 for x in rs)/len(rs)*100,2)

    self.data['rwin_mean']= self.data.rwin[0:period].values.tolist() + [rwin_mean(self.data.tick_result[i:i+period].tolist()) for i in range(len(self.data.rwin)-period)]

  #Metodo win ticks: Profitable PnL Ticks
  def get_win_ticks(self):
    #Generator
    def count_win_ticks(_result):
        _count=0
        for r in _result:
            if r>0:
              _count += r
            yield _count
    self.data['win_ticks']=list(count_win_ticks(self.data.tick_result))

  #Metodo Lost Ticks: Lossing PnL Ticks
  def get_loss_ticks(self): 
    #Generator
    def count_loss_ticks(_result):
        _count=0
        for r in _result:
            if r<0:
              _count += r
            yield _count
    self.data['loss_ticks']=list(count_loss_ticks(self.data.tick_result))
  
  #Metodo para Average Win ticks
  def get_avrg_win_ticks(self):
    self.get_win_ticks()
    self.count_result(result='win')
    self.data['avrg_win_ticks']=list(map(lambda win_ticks,win: (round(win_ticks/win,0) if win!=0 else 0), self.data.win_ticks, self.data.win))

  #Metodo para Average Loss ticks
  def get_avrg_loss_ticks(self):
    self.get_loss_ticks()
    self.count_result(result='loss')
    self.data['avrg_loss_ticks']=list(map(lambda loss_ticks,loss: (round(loss_ticks/loss,0) if loss!=0 else 0), self.data.loss_ticks, self.data.loss))

  #Metodo para profit factor
  def get_profit_factor(self):
    self.get_win_ticks()
    self.get_loss_ticks()    
    self.data['profit_factor']=list(map(lambda win,lost: round(abs(win/lost) if lost!=0 else 0,2), self.data.win_ticks, self.data.loss_ticks))

  #Metodo para Worst Trade 
  def get_worst(self):
    #Generator
    def worst(_data):
      _worst=0
      for r in _data:
          if r<_worst:
             _worst=r
          yield _worst
    self.data['worst']=list(worst(self.data.tick_result))

  #Metodo para Best Trade
  def get_best(self):
    #Generator
    def best(_data):
        _best=0
        for r in _data:
            if r>_best:
               _best=r
            yield _best
    self.data['best']=list(best(self.data.tick_result))

  #Metodo para recoveryfactor
  def get_recovery_factor(self):
    self.get_cash_data()
    self.data['recovery_factor']=list(map(lambda cash_balance,cash_dd_max: round((cash_balance/cash_dd_max) if cash_dd_max !=0 else 0,2), 
                                      self.data.cash_balance, self.data.cash_drawdown_max))

  #Metodo para Average Ticks:
  def get_avrg_ticks(self):
    #Generator
    def average_ticks(_data):
      _balance = 0
      for _trades, r in enumerate(_data, start=1):
        _balance +=r
        yield round(_balance/_trades,2)
        
    self.data['avrg_ticks']=list(average_ticks(self.data.tick_result))

#---- Bloque de Métodos para las estadísticas diarias

  #Método para calcular las ganancias, numero de trades y balance diarios
  def get_dailyresults(self):
    #Generators
    def dailytickPnL(_result, _marketdays):
      _dailytickpnl=0
      _day=0
      for _res, _md in zip(_result,_marketdays):
        if _md!=_day:
          _day = _md
          _dailytickpnl = 0

        _dailytickpnl += _res
        yield _dailytickpnl

    def dailybalance(_result, _marketdays, _tickvalue, _size, _fee):
      _dailybalance=0
      _day=0
      for _res, _md in zip(_result,_marketdays):
        if _md!=_day:
          _day = _md
          _dailybalance = 0
        _dailybalance += _res*_size*_tickvalue -_fee*_size
        yield _dailybalance
    
    def dailytrades(_result, _marketdays):
      _day=0
      _numtrades=0
      for _res, _md in zip(_result,_marketdays):
        if _md!=_day:
          _day = _md
          _numtrades = 0
        _numtrades += 1
        yield _numtrades
    
    def dailymaxbalance(_marketdays, _balance):
      _dailymaxbalance=0
      _day=0
      for _bal, _md in zip(_balance,_marketdays):
        if _md!=_day:
          _day = _md
          _dailymaxbalance = 0
  
        _dailymaxbalance = _bal if _bal>_dailymaxbalance else _dailymaxbalance
        yield _dailymaxbalance

    def dailyminbalance(_marketdays, _balance):
      _dailyminbalance=0
      _day=0
      for _bal, _md in zip(_balance,_marketdays):
        if _md!=_day:
          _day = _md
          _dailyminbalance = 0
  
        _dailyminbalance = _bal if _bal<_dailyminbalance else _dailyminbalance
        yield _dailyminbalance

    #Datos
    self.data['daily_tickpnl']=list(dailytickPnL(self.data.tick_result,self.data.market_day))
    self.data['daily_balance']=list(dailybalance(self.data.tick_result,self.data.market_day,self.setting.instrument.tickvalue,self.setting.trademanagement.size,self.setting.account.fee))
    self.data['daily_numtrades']=list(dailytrades(self.data.tick_result,self.data.market_day))
    self.data['daily_maxbalance']=list(dailymaxbalance(self.data.market_day,self.data.daily_balance))
    self.data['daily_minbalance']=list(dailyminbalance(self.data.market_day,self.data.daily_balance))
    
  #Método para las estadísticas diarias
  def get_dailystatictis(self):
    #Lista con los días de mercados ordenados
    _marketdays=sorted(set(self.data.market_day))
    _trades=[]
    _balance=[]
    _tickpnl=[]
    _maxbalance=[]
    _minbalance=[]
    #Recorremos los resultados y extraemos el ultimo dato del día y lo almacenamos en listas
    for _day in _marketdays:
      _trades.append(self.data['daily_numtrades'].loc[self.data.market_day==_day].iat[-1])
      _balance.append(self.data['daily_balance'].loc[self.data.market_day==_day].iat[-1])
      _tickpnl.append(self.data['daily_tickpnl'].loc[self.data.market_day==_day].iat[-1])
      _maxbalance.append(self.data['daily_maxbalance'].loc[self.data.market_day==_day].iat[-1])
      _minbalance.append(self.data['daily_minbalance'].loc[self.data.market_day==_day].iat[-1])
      
    #Creamos un objeto de la clase dailyresult
    
    self.dailyresult=cDailyResult(_marketdays,_trades,_balance,_tickpnl,_maxbalance,_minbalance,self.setting.account.initial_balance)
  

  #Metodo que calcula todos los atributos 
  def get_all_result_attributes(self):
      self.get_total()
      for result in ['win','loss','doubt','beven']:
        self.count_result(result)

      self.get_cash_data()
      self.get_avrg_win_ticks()
      self.get_avrg_loss_ticks()
      self.get_tick_balance()      
      self.get_avrg_ticks()
      self.get_worst()
      self.get_best()
      self.get_rwin()
      self.get_profit_factor()
      self.get_recovery_factor()
      self.get_dailyresults()
      self.get_dailystatictis()

#---- Bloque para recuperar las series de los atributos
  #Metodo que devuelve la serie completa del atributo que se solicita
  def Get_Attribute_Serie(self,_attb):
    if _attb not in RESULT_ATTRIBUTES.values():
      return []

    if _attb=="total":
        self.get_total()
        return self.data.total
    elif _attb in ["win","loss","doubt","beven","pwin","ploss"]:
        self.count_result(_attb)
        return self.data[_attb]
    elif _attb=="tick_balance":
        self.get_tick_balance()
        return self.data.tick_balance
    elif _attb=="avrg_ticks":
        self.get_avrg_ticks()
        return self.data.avrg_ticks
    elif _attb=="cash_balance":
        self.get_cash_balance()
        return self.data.cash_balance
    elif _attb=="avrg_cash":
        self.get_avrg_cash()
        return self.data.avrg_cash
    elif _attb=="cash_drawdown":
        self.get_cash_drawdown()
        return self.data.cash_drawdown
    elif _attb=="cash_drawdown_max":
        self.get_cash_drawdown_max()
        return self.data.cash_drawdown_max
    elif _attb=="win_ticks":
        self.get_win_ticks()
        return self.data.win_ticks
    elif _attb=="loss_ticks":
        self.get_loss_ticks()
        return self.data.loss_ticks
    elif _attb=="avrg_win_ticks":
        self.get_avrg_win_ticks()
        return self.data.avrg_win_ticks
    elif _attb=="avrg_loss_ticks":
        self.get_avrg_loss_ticks()
        return self.data.avrg_loss_ticks
    elif _attb=="best":
        self.get_best()
        return self.data.best
    elif _attb=="worst":
        self.get_worst()
        return self.data.worst    
    elif _attb=="rwin":
        self.get_rwin()  
        return self.data.rwin
    elif _attb=="profit_factor":
        self.get_profit_factor()
        return self.data.profit_factor
    elif _attb=="recovery_factor":
        self.get_recovery_factor()
        return self.data.recovery_factor
    elif _attb=="roi":
        self.get_roi()
        return self.data.roi
    
    #Método que devuelve el titulo del eje Y para el graficos de atributos simple
  def Get_Axis_Name_Single(self,_at):
          if _at=="win":
              return 'Num of Win Trades'
          elif _at=="loss":
              return 'Num of Loss Trades'
          elif _at=="doubt":
              return 'Num of Doubt Trades'
          elif _at=="beven":
              return 'Num of Breakeven Trades'
          elif _at=="pwin":
              return 'Num of Partial Win Trades'
          elif _at=="ploss":
              return 'Num of Partial Loss Trades'
          elif _at=="rwin":
              return 'Ratio of Win Trades %'
          elif _at=="win_ticks":
              return 'Num of Total Win Ticks'
          elif _at=="lost_ticks":
              return 'Num of Total LostTicks'
          elif _at=="pandl":
              return 'Ticks P&L (num)'
          elif _at=="pf":
              return 'Profit Factor'
          elif _at=="worst":
              return 'Worst trade in ticks'
          elif _at=="cash_dd_max":
              return 'Drawdown max (%)'
          elif _at=="cash_pandl":
              return 'Cash P&L ($)'
          elif _at=="recoveryfactor":
              return 'Recovery Factor'
          else:
              return 'This would never be shown'


#----- Bloque de métodos para obtener las graficas ECharts
  def get_hourly_option(self) -> dict:
    # Lista para los valores  
    _hours = []
    _win = []
    _loss = []
    for hour in range(24):
      _filter = self.data[(self.data['Relative_Hour']>=hour) & (self.data['Relative_Hour']<(hour+1))]           # Filtrado de trades en la hora hour
      _hours.append(hour)                                                                                       # Añadimos la hora
      _win.append(len(_filter[_filter.Result>=0]))                                                              # Añadimos los trades ganadores
      _loss.append(len(_filter[_filter.Result<0]))                                                              # Añadimos los trades perdedores

    data = {
      'xaxis_data': _hours,
      'xaxis_title': 'Market Hour',
      'yaxis_data': [_win,_loss],
      'yaxis_name': ['Trades'],
      'yaxis_traces': [0,0],
      'traces_name': ['Win','Loss'],
      'traces_type': ['bar','bar'],
      'coloured_traces': [False,False]
    }
    
    echart = BasicEChart(data)    
    return echart.getOption()
    
  def get_hourlyinformation_option(self, param: dict) -> dict:  
    # Lista para los valores  
    _hours, _win, _loss, _rwin, _rloss = [], [], [], [], []

    for hour in range(24):
      _filter = self.data[(self.data['relative_hour']>=hour) & (self.data['relative_hour']<(hour+1))]           # Filtrado de trades en la hora hour
      total_win = len(_filter[_filter.tick_result>=0])
      total_loss = len(_filter[_filter.tick_result<0])
      ratio_win = round((total_win)/(total_win+total_loss)*100,1) if (total_win+total_loss)>0 else 0
      ratio_loss = round((total_loss)/(total_win+total_loss)*100,1) if (total_win+total_loss)>0 else 0
      _hours.append(hour)                                                                                       # Añadimos la hora
      _win.append(total_win)                                                                                    # Añadimos los trades ganadores
      _loss.append(total_loss)                                                                                  # Añadimos los trades perdedores
      _rwin.append(ratio_win)                                                                                   # Añadimos el porcentaje de ganadores
      _rloss.append(ratio_loss)                                                                                 # Añadimos el porcentahe de perdedores
      
    
    ywin = _win if param['selected']=='Total Trades' else _rwin
    yloss = _loss if param['selected']=='Total Trades' else _rloss
    yaxis_unit = "trades" if param['selected']=='Total Trades' else "%" 

    data = {
      'xaxis_data': _hours,
      'xaxis_title': 'Market Hour',
      'yaxis_data': [ywin,yloss],
      'yaxis_name': [yaxis_unit],
      'yaxis_traces': [0,0],
      'traces_name': ['Win','Loss'],
      'traces_type': ['bar','bar'],
      'coloured_traces': [False,False]
    }
    
    echart = BasicEChart(data)    
    option = echart.getOption()
  
    # Apilamos las barras 
    option['series'][0].update({'stack': 'total'})
    option['series'][1].update({'stack': 'total'})
    
    # Para el total trades al poner las barras en stack hay que redimensionar el eje y
    option['yAxis'][0]['max'] = max(_win)+max(_loss) if param['selected']=='Total Trades' else 100
    
    #Cambiamos los colores
    option.update({'color': ['green','red']})   
    
    return option
  
  def get_attributegroup_option(self, param: dict)-> dict:
    _data = {
      'xaxis_data': self.data.index.to_list(),
      'xaxis_title': 'Number of trades',
      'yaxis_data': self.get_attribute_multiple(param['selected_attributegroup'], param['rwin_mean_period']),
      'yaxis_name': self.get_yaxis_name_group(param['selected_attributegroup']),
      'yaxis_traces': self.get_yaxis_traces(param['selected_attributegroup']),
      'traces_name': self.get_traces_name(param['selected_attributegroup'], param['rwin_mean_period']),
      'traces_type': self.get_traces_type(param['selected_attributegroup']),
      'coloured_traces': self.get_coloured_traces(param['selected_attributegroup'])
    }
    if len(_data['xaxis_data'])==0:
      return {}
    echart = BasicEChart(_data)
    
    return echart.getOption()
    
  #Metodo que devuelve multiples series
  def get_attribute_multiple(self,_group,_period=100):
      if _group=="trades":
            for result in ['win','loss','doubt','beven']:
              self.count_result(result)
            return [self.data.win.to_list(),self.data.loss.to_list(),self.data.doubt.to_list(),self.data.beven.to_list()]
      elif _group=="ticks":
            self.get_win_ticks()
            self.get_loss_ticks()
            self.get_tick_balance()
            return [self.data.win_ticks.to_list(), self.data.loss_ticks.to_list(), self.data.tick_balance.to_list()]
      elif _group=="cash":
            self.get_cash_data()
            self.get_rwin()
            self.get_mean_rwin(_period)
            return [self.data.cash_balance.to_list(),self.data.trailing_drawdown.to_list(),self.data.rwin.to_list(),self.data.cash_drawdown.to_list(),self.data.rwin_mean.to_list()]
      else:
            return ['This should never be shown']

  #Metodo que devuelve de nombre de las trazas
  def get_traces_name(self,_group,_period=100):
      if _group=="trades":
          return ['Winning Trades','Lossing Trades','Doubt Trades','Breakeven Trades']
      elif _group=="ticks":
          return ['Win Ticks','Lost Ticks','Balance Ticks']
      elif _group=="cash":
          return ['Cash Balance($)','Trailing Drawdown($)','Ratio Win(%)','Drawdown(%)',f'RWin Mean({_period})(%)']
      else:
          return 'This should never be shown'
  
  #Metodo que devuelve de el eje en el que se muestra cada traza en los atributos por grupo
  def get_yaxis_traces(self,_group):
      if _group=="trades":
          return [0,0,0,0]
      elif _group=="ticks":
          return [0,0,1]
      elif _group=="cash":
          return [0,0,1,1,1]
      else:
          return 'This should never be shown'
  
  #Metodo que devuelve de el eje en el que se muestra cada traza en los atributos por grupo
  def get_coloured_traces(self,_group):
    if _group == "cash":
      return [False,False,False,False,False]
    elif _group in ["trades", "ticks"]:
      return [False,False,False,False]
    else:
      return 'This should never be shown'
  
  def get_traces_type(self,_group):
      if _group=="trades":
          return ['line','line','line','line']
      elif _group=="ticks":
          return ['line','line','line']
      elif _group=="cash":
          return ['line','line','line','line','line']
      else:
          return 'This should never be shown'
  
  #Metodo que devuelve de nombre de los ejes Y para los atributos por grupo
  def get_yaxis_name_group(self,_group):
      if _group=="trades":
          return ['Num Trades','']
      elif _group=="ticks":
          return ['Ticks','Ticks Balance']
      elif _group=="cash":
          return ['$','%']
      else:
          return 'This should never be shown'


#---- Métodos que calculan el 
  # Metodo que calcula los resutlados en funcion del internval simple
  def get_interval_single_data(self) -> list:
    # Calculamos el numero de interval distintos que hay en las posiciones
    set_interval = set(self.data['interval'].toList())
    # Pasamos los datos a listas
    interval = self.data['interval'].to_list()
    tick_result = self.data['tick_result'].to_list()
    
    # Calculamos los win, loss y rwin para cada intervalo
    single_interval_win = [sum(1 if x==i and y>=0 else 0 for x,y in zip(interval,tick_result)) for i in set_interval]
    single_interval_loss = [sum(1 if x==i and y<0 else 0 for x,y in zip(interval,tick_result)) for i in set_interval]
    single_interval_rwin = [int(w/(w+l)*100) for w,l in zip(single_interval_win,single_interval_loss)]
    
    return [{'interval': i, 'single_interval_win': w, 'single_interval_loss': l, 'single_interval_rwin': rw} for i,w,l,rw in zip(set_interval, single_interval_win, single_interval_loss, single_interval_rwin)]
    
  # Método qye calcula los resultado en funcion de los dias de mercado que hay entre level y tc  
  def get_interval_daily_data(self) -> list:  
    set_interval_days = set(self.data['interval_days'].to_list())
    interval_days = self.data['interval_days'].to_list()
    tick_result = self.data['tick_result'].to_list()
    daily_interval_win = [sum(1 if x==d and y>=0 else 0 for x,y in zip(interval_days, tick_result)) for d in set_interval_days ]
    daily_interval_loss = [sum(1 if x==d and y<0 else 0 for x,y in zip(interval_days, tick_result)) for d in set_interval_days ]
    daily_interval_rwin = [int(w/(w+l)*100) for w,l in zip(daily_interval_win, daily_interval_loss)]
    
    return [{'interval_day': d, 'daily_interval_win': w, 'daily_interval_loss': l, 'daily_inteval_rwin': rw} for d,w,l,rw in zip(set_interval_days, daily_interval_win, daily_interval_loss, daily_interval_rwin)]
    
  # Método que calucla los resultados en funcion del intervalo simple para un interval_day dado
  def get_interval_single_day_data(self, interval_day:int) -> list:
    interval = [i for i,id in zip(self.data['interval'],self.data['interval_days']) if id==interval_day] 
    tick_result = [tr for id,tr in zip(self.data['interval_days'],self.data['tick_result']) if id==interval_day] 
    set_interval = set(interval)
    single_interval_win = [sum(1 if x==i and y>=0 else 0 for x,y in zip(interval,tick_result)) for i in set_interval]
    single_interval_loss = [sum(1 if x==i and y<0 else 0 for x,y in zip(interval,tick_result)) for i in set_interval]
    single_interval_rwin = [int(w/(w+l)*100) for w,l in zip(single_interval_win,single_interval_loss)]  
  
    return [{'interval': i, 'single_interval_win': w, 'single_interval_loss': l, 'single_interval_rwin': rw} for i,w,l,rw in zip(set_interval, single_interval_win, single_interval_loss, single_interval_rwin)]
  
  # Metodo que devuelve el option de la grafica del interval en distintas sesiones de merercado
  def get_interval_daily_option(self, num_days: int) -> dict:  
    win, loss = [] , []
    daily_interval = sorted(self.get_interval_daily_data(),key=lambda i: i['interval_day'])
    short_daily_interval = daily_interval[:num_days]
    set_interval_day = [ x['interval_day'] for x in short_daily_interval]
    set_daily_interval_win = [ x['daily_interval_win'] for x in short_daily_interval]
    set_daily_interval_loss = [ x['daily_interval_loss'] for x in short_daily_interval]
    for day in range(num_days):
        if day in set_interval_day:
            win.append(set_daily_interval_win[set_interval_day.index(day)])
            loss.append(set_daily_interval_loss[set_interval_day.index(day)])
        else:
            win.append(0)
            loss.append(0)

    reswin = sum(x['daily_interval_win'] for x in daily_interval if x['interval_day'] >= num_days)
    resloss = sum(x['daily_interval_win'] for x in daily_interval if x['interval_day'] >= num_days)
    win.append(reswin)
    loss.append(resloss) 


    data = {
        'xaxis_data': list(range(num_days + 1)),
        'xaxis_title': 'Market Relative Days',
        'yaxis_data': [win, loss],
        'yaxis_name': ['trades'],
        'yaxis_traces': [0, 0],
        'traces_name': ['Win', 'Loss'],
        'traces_type': ['bar', 'bar'],
        'coloured_traces': [False, False]
    }

    echart = BasicEChart(data)
    option = echart.getOption()

    # Apilamos las barras 
    option['series'][0].update({'stack': 'total', 'barWidth': '30%'})
    option['series'][1].update({'stack': 'total', 'barWidth': '30%'})

    # Para el total trades al poner las barras en stack hay que redimensionar el eje y
    option['yAxis'][0]['max'] = max(win)+max(loss) 
    option['yAxis'][0]['axisLine']['onZero'] = False
    option['yAxis'][0]['offset'] = 30


    #Cambiamos los colores
    option.update({'color': ['green','red']})   


    return option
  
  # Método que devuelve el option de la grafia del interval simple en la primera sesion de mercado
  def get_interval_single_day_option(self) -> dict:  
    win, loss = [] , []
    session_interval = sorted(self.get_interval_single_day_data(interval_day=0), key=lambda i: i['interval'])

    set_session_interval = [ x['interval'] for x in session_interval]
    set_session_interval_win = [ x['single_interval_win'] for x in session_interval]
    set_session_interval_loss = [ x['single_interval_loss'] for x in session_interval]
    #max_interval_in_session = int(23*60/self.setting.instrument.tf)
    max_interval_in_session = 50
    for interval in range(1,max_interval_in_session):
        if interval in set_session_interval:
            win.append(set_session_interval_win[set_session_interval.index(interval)])
            loss.append(set_session_interval_loss[set_session_interval.index(interval)])
        else:
            win.append(0)
            loss.append(0)



    data = {
        'xaxis_data': list(range(1,max_interval_in_session)),
        'xaxis_title': 'Interval in the same Session',
        'yaxis_data': [win, loss],
        'yaxis_name': ['trades'],
        'yaxis_traces': [0, 0],
        'traces_name': ['Win', 'Loss'],
        'traces_type': ['bar', 'bar'],
        'coloured_traces': [False, False]
    }

    echart = BasicEChart(data)
    option = echart.getOption()

    # Apilamos las barras 
    option['series'][0].update({'stack': 'total', 'barWidth': '80%'})
    option['series'][1].update({'stack': 'total', 'barWidth': '80%'})

    # Para el total trades al poner las barras en stack hay que redimensionar el eje y
    option['yAxis'][0]['max'] = max(win)+max(loss) 
    option['yAxis'][0]['axisLine']['onZero'] = False
    option['yAxis'][0]['offset'] = 20


    #Cambiamos los colores
    option.update({'color': ['green','red']})   


    return option
  
  # Método que devuelve el option de la grafica del parametetro que se le pida
  def get_parameter_option(self, parameter:str, data: list, initial_range: int, final_range:int, step: int,title: str) -> dict:
    win, loss = [] , []
    sorted_data = sorted(data, key=lambda i: i[parameter])
    initial_range = int(initial_range)
    final_range = int(final_range)

    parameter_data= [ x[parameter] for x in sorted_data]
    parameter_tick_result = [ x['tick_result'] for x in sorted_data]  
    set_parameter_data = list(set(parameter_data))
    parameter_win = [sum(1 if x==i and y>=0 else 0 for x,y in zip(parameter_data,parameter_tick_result)) for i in set_parameter_data]
    parameter_loss = [sum(1 if x==i and y<0 else 0 for x,y in zip(parameter_data,parameter_tick_result)) for i in set_parameter_data]

    
    if step>1:      # Agruapamos los win y loss
      win = [sum(w for w, l in zip(parameter_win, set_parameter_data) if i <= l < i + step ) for i in range(initial_range, final_range, step)] 
      loss = [sum(w for w, l in zip(parameter_loss, set_parameter_data) if i <= l < i + step ) for i in range(initial_range, final_range, step)]
    
    #parameter_data_rwin = [int(w/(w+l)*100) for w,l in zip(parameter_win,parameter_loss)]  
    else:
      for param in range(int(initial_range),int(final_range)):
          if param in set_parameter_data:
              win.append(parameter_win[set_parameter_data.index(param)])
              loss.append(parameter_loss[set_parameter_data.index(param)])
          else:
              win.append(0)
              loss.append(0) 
    
    data = {
        'xaxis_data': list(range(int(initial_range),int(final_range),step)),
        'xaxis_title': title,
        'yaxis_data': [win, loss],
        'yaxis_name': ['trades'],
        'yaxis_traces': [0, 0],
        'traces_name': ['Win', 'Loss'],
        'traces_type': ['bar', 'bar'],
        'coloured_traces': [False, False]
    }
    
    echart = BasicEChart(data)
    option = echart.getOption()

    # Apilamos las barras 
    option['series'][0].update({'stack': 'total', 'barWidth': '40%'})
    option['series'][1].update({'stack': 'total', 'barWidth': '40%'})

    # Para el total trades al poner las barras en stack hay que redimensionar el eje y
    option['yAxis'][0]['max'] = max(win)+max(loss) 
    option['yAxis'][0]['axisLine']['onZero'] = False
    option['yAxis'][0]['offset'] = 40


    #Cambiamos los colores
    option.update({'color': ['green','red']})   
    option.update({'media': {'query': { 'minAspectRation' : 1}}})
                                    


    return option