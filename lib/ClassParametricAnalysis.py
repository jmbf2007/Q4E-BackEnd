#------------------------------
# Importamos librerias externas
#------------------------------
import pandas as pd 



import sys
sys.path.append("..")


ATTRIBUTES={'Total Trades':'total',
        'Total Win Trades':'win',
        'Total Loss Trades':'loss',
        'Total Doubt Trades':'doubt',
        'Total Breakeven Trades':'beven',
        'Partial Win Trades':'pwin',
        'Partial Loss Trades':'ploss',
        'Balance PnL Ticks':'tick_balance',
        'Average PnL Ticks':'avrg_ticks',
        'Cash Balance':'cash_balance',
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
# Importamos Clases Propias
#-----------------------------
#from lib.ClassParametricInfo import cParametricInfo
from models.models import ParametricInfo

#------------------------------
# Clase
#------------------------------




class cParametric():
#---- Constructor
    def __init__(self,parameters: dict=None, load=False):

      
        if not load:                 
            self.parameters=ParametricInfo()
            self.parameters.name = parameters['name']
            self.parameters.description = parameters['description']
            self.parameters.param1_name = parameters['param1_name']
            self.parameters.param1_values = parameters['param1_values']
            self.parameters.param2_name = parameters['param2_name']
            self.parameters.param2_values = parameters['param2_values']
        else:
            return



#---- Bloque Metodos de la Clase
    
    #Metodo para iniciar los dataframe de salida
    def initialize_dataframes(self):
        if len(self.parameters.param2_values)!=0:
            self.index_name=list(map(lambda x: (str(x)), self.parameters.param2_values))
            #Definimos los dataframes de salida vacios 
            for attb in list(ATTRIBUTES.values()):
                self.__dict__['df_'+attb]= pd.DataFrame(index=self.index_name)

    #Método que devuelve el dataframe del atributo que se solicita  
    def get_attribute(self,_attb):
        if _attb in ATTRIBUTES.values():
            return self.__dict__[f'df_{str(_attb)}']
        else:
            return None


