from typing import List,Optional
import datetime as dt
import pandas as pd
import datetime as dt

class cPorfolio():

    positions: Optional[List[dict]]

    def __init__(self, models_positions: list, account_type: str, initial_balance: float) -> None:
        self.account_type = account_type
        self.initial_balance = initial_balance
        self.models_daily_balance(models_positions)
        self.get_porfolio_days()
        self.get_porfolio_balances()
        self.get_cummulative_net_balances()
        self.get_total_cash_balances()
        del self.balances
        del self.porfolio_balances
        del self.porfolio_days

        self.porfolio_dataframe.to_csv('porfolio.csv', sep=";", index=False)


    def models_daily_balance(self, models_positions: list):        
        data_models_positions = [{'model_name': pos['model_name'], 'positions': pd.DataFrame(pos['positions'])} for pos in models_positions]
        self.models_name = [model['model_name'] for model in data_models_positions] 
        self.balances = [{'model_name': model['model_name'], 'daily_cash_balances': self.group_daily_cash_balances(model['positions'])} for model in data_models_positions]
  
    def group_daily_cash_balances(self, df: pd.DataFrame) -> pd.DataFrame:
        df['date'] = df.close_time.apply(lambda t: t.date())
        return df.groupby(['date']).sum().reset_index()

    def get_porfolio_days(self):
        self.porfolio_days = pd.Series()
        for model in self.balances:
            self.porfolio_days = pd.concat([self.porfolio_days, model['daily_cash_balances']['date']], ignore_index=True)
        
        self.porfolio_days = self.porfolio_days.drop_duplicates()
        self.porfolio_days = self.porfolio_days.sort_values()
        self.porfolio_dataframe = pd.DataFrame({'Days': self.porfolio_days})
    
    def get_total_cash_balances(self):
        # Obtenemos los totales de los modelos
        for model in self.models_name: 
            self.porfolio_dataframe[f'Total_{model}'] = self.porfolio_dataframe[f'Cum_Net_{model}']+self.initial_balance
        
        # El total del porfolio
        if self.account_type == 'Single':
            self.porfolio_dataframe['Total_Porfolio'] = self.porfolio_dataframe['Cum_Net_Porfolio']+self.initial_balance
        else: 
            self.porfolio_dataframe['Total_Porfolio'] = sum(self.porfolio_dataframe[f'Total_{model}'] for model in self.models_name)         

    def get_cummulative_net_balances(self):
        # Lista de columnas de los daily balances
        columns = self.porfolio_dataframe.columns.to_list()
        columns.pop(0)

        # Genarator
        def cummulative(serie: pd.Series):
            cumm_balance = 0
            for daily_balance in serie:
                cumm_balance += daily_balance
                yield cumm_balance
        
        for column in columns:
            self.porfolio_dataframe[f'Cum_{column}'] = list(cummulative(self.porfolio_dataframe[column]))

    def get_porfolio_balances(self) -> None:
        self.porfolio_balances = []
        for i,model in enumerate(self.balances):
            self.porfolio_dataframe[model['model_name']] = self.porfolio_dataframe['Days'].apply(lambda day: self.get_daily_cash(i, day))

        model_columns = [model['model_name'] for model in self.balances]
        self.porfolio_dataframe['Porfolio'] = self.porfolio_dataframe[model_columns].sum(axis=1)
        # Renombramos las columnas añadiendo Net_ para indicar que estos son balances diarios netos
        columns = self.porfolio_dataframe.columns.to_list()
        new_columns = []
        for col in columns:
            if col != 'Days':
                col = f'Net_{col}'
            new_columns.append(col)

        self.porfolio_dataframe.columns = new_columns

    def get_daily_cash(self, index: int, day: dt.date) -> float:
        return next((cash_balance for model_day, cash_balance in zip(self.balances[index]['daily_cash_balances']['date'].tolist(), self.balances[index]['daily_cash_balances']['cash_result'].tolist()) if day == model_day), 0)

    def get_dataframe(self):
        return self.porfolio_dataframe.to_json()

#----- Funciones para el grafico echart

    def series(self, attb: str):  # sourcery skip: for-append-to-extend, inline-immediately-returned-variable, list-comprehension, move-assign-in-block
        series = []
        traces_name = self.get_traces_name(attb)

        # Modelos
        for trace in traces_name: 
            series.append(
                {
                    'name': trace,
                    'type': 'line',
                    'data': self.porfolio_dataframe[trace].to_list(),
                    'smooth': True,
                    'yAxisIndex': 0
                }
            )
        return series

    def get_traces_name(self, attb: str) -> list:
        traces_name = self.porfolio_dataframe.columns.to_list()
        traces_name.pop(0)
        short_traces = []
        for trace in traces_name:
            if attb == "Cummulative Net Balances" and 'Cum_Net_' in trace:
                short_traces.append(trace)
            elif attb == "Daily Net Balances" and 'Net_' in trace[:4]:
                short_traces.append(trace)
            elif attb == "Total Cash Balances" and 'Total_' in trace[:6]:
                short_traces.append(trace)
            else:
                continue
        return short_traces

    def xAxis(self) -> dict:
        return {
            "type": "category",
            "boundaryGap": False,
            "data": self.porfolio_dataframe.Days.to_list(),
            "name": '',
            "nameLocation": "center",
            "nameTextStyle": {
                "fontSize": 14,
                "verticalAlign": "top",
                "padding": [15,15]
            }          
        }

    def yAxis(self, attb: str) -> dict:
        if attb == "Cummulative Net Balances":
            yaxis_data = self.porfolio_dataframe['Cum_Net_Porfolio']
        elif attb == "Daily Net Balances":
            yaxis_data = self.porfolio_dataframe['Net_Porfolio']
        elif attb == "Total Cash Balances":
            yaxis_data = self.porfolio_dataframe['Total_Porfolio']

        return [{
            "type": "value",
            "name": '($)',
            "nameTextStyle": {
                "color": "#777",
                "fontSize": 12,
            },
            #"min": yaxis_data.min(),
            #"max": yaxis_data.max(),
            "axisLine": {
                "show": True,
                "lineStyle": {
                    "color": "black"
                },
            "interval": 500
            }       
        }]

    @staticmethod
    def tooltip()->dict:
        return {
                "trigger": "axis",
        }

    @staticmethod 
    def grid()-> list:       
        return  [
            {
                "left": '5%',
                "right": '5%',
                "top": 110,
                "height": 450,
                "containLabel": True
            },
        ]
    
    def legend(self, attb: str) -> dict:
        return {
            "data": self.get_traces_name(attb),
            "bottom": "90%"}

    def title(self, attb: str) -> dict:
        return {
            'text': attb,
            'left': 'center',
            'textVerticalAlign': 'top'
        }

    def dataZoom(self):
        return [
            {
                'show': True,
                'realtime': True,
                'start': 10,
                'end': 90,
                'xAxisIndex': [0]
            },
            {
                'type': 'inside',
                'realtime': True,
                'start': 10,
                'end': 90,
                'xAxisIndex': [0],
                'top': 'bottom'
            }
        ],

    def get_graph_option(self, attb: str):
        return  {
            'title': self.title(attb),
            'xAxis': self.xAxis(),
            'yAxis': self.yAxis(attb),
            'series': self.series(attb),  
            'tooltip': self.tooltip(),
            'grid': self.grid(),
            'legend': self.legend(attb),
            'dataZoom': self.dataZoom()
        }             
            
#----- Fin Funciones para el grafico echart


