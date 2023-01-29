#------------------------------
# Importamos librerias externas
#------------------------------
import pandas as pd


#------------------------------
# Importamos Clases Propias
#-----------------------------
from lib.ClassCase import cCase
from lib.ClassData import cDataCandle
from lib.ClassResult import cResult





#------------------------------
# Clase
#------------------------------
class cWalkForward():

#---- Constantes
    OBJECTIVE_FUNCTIONS=[None,'Max Balance','Max Ratio Win','Max Profit Factor','Min Drawdown','Max Winning Days %']

#---- Constructor
    def __init__(self, data: pd.DataFrame, data_wfa: dict, setting: dict, m1_data: pd.DataFrame, tc_assumptions:dict, strategy_settings: dict, strategy_type:str):
     
        #Dataframe de los datos originales
        self.data = data
        self.m1_data = m1_data
        
        #Setting del caso original en formato diccionario
        self.setting = setting

        #Hipotesis de la estrategia
        self.tc_assumptions = tc_assumptions
        self.strategy_settings = strategy_settings
        self.strategy_type = strategy_type

        self.strategy_parameters_values = [x['value'] for x in self.strategy_settings['strategyparameters']]
        self.trademanagement_values = [x['value'] for x in self.strategy_settings['trademanagement']]
        self.indicators_values = {}
        for indicator in self.setting['indicators']['indicators']:
            self.indicators_values[indicator]= list(self.setting['indicators'][indicator].keys()) 
        


        # Atributos para la definicion de los períodos In-Sample, Out-of-Sample 
        self.is_days = data_wfa['is_days']      # Días para el In-Sample
        self.oos_days = data_wfa['oos_days']    # Días para el Out-Of-Sample
        self.periods = data_wfa['periods']      # Numero de pasos del WFA 

        # Atributos para los parámetros a optimizar
        self.param1_name = data_wfa['parameters']['param1_name']
        self.param1_values = data_wfa['parameters']['param1_values']
        self.param2_name = data_wfa['parameters']['param2_name']
        self.param2_values = data_wfa['parameters']['param2_values']
        self.param3_name = data_wfa['parameters']['param3_name']
        self.param3_values = data_wfa['parameters']['param3_values']


        # Funcion objetivo y ajuste del riesgo
        self.objective_function = data_wfa['objective_function']



        # En una lista almacenaremos los casos de los resultados de aplicar las optimizaciones
        self.cases=[]
        self.oos_results = pd.DataFrame()                   # Dataframe con los resultados de los periodos
        self.oos_results_periods = []
        self.oos_data  = pd.DataFrame()                     # Dataframe con la concatenacion de dataframes de los oos
        self.is_data = pd.DataFrame()                       # Dataframe para los datos de los dias del IS


#---- Bloque de métodos


    #Funcion que optimiza el periodo que  se le pase y almacena los resultados en el dataframe de los valores optimizados
    def optimize_period(self,_step) -> None:
        
        #Calulamos los dias de mercado inicial y final de cada periodo
        _is_ini=1+self.oos_days*(_step-1)
        _is_end=_is_ini+self.is_days


        #Filtramos los días y nos quedamos sólo con el IS
        self.filter_is_days(_is_ini,_is_end)                                               

        # Setting incial antes de realizar el loop de por los parameteros
        self.is_setting = self.setting
        
        # Matriz en la que almacenarán los resultados de la optimizacion del periodo
        self.optimization_matrix = pd.DataFrame(columns=('P1','P2','P3','OF'))                              

        # Iniciamos en dataframe que recoge los resultados de optimos de los OOS en el primer paso
        if _step==0:
            self.oos_settings = pd.DataFrame(columns=('P1','P2','P3'))                                      # Dataframe en el que se almacenarán los optimos de cada periodo y que son los setting del OOS


        #Hay que ir recorriendo los parametros a optimizar
        if self.param1_name is None:
            return

        self.get_optimization_matrix()

        #Buscamos el caso optimo 
        if self.objective_function == self.OBJECTIVE_FUNCTIONS[4]:
            id_op=self.optimization_matrix.OF.tolist().index(min(self.optimization_matrix.OF.tolist()))
        else:
            id_op=self.optimization_matrix.OF.tolist().index(max(self.optimization_matrix.OF.tolist()))

        p1_op = self.optimization_matrix.P1.iat[id_op]
        p2_op = self.optimization_matrix.P2.iat[id_op]
        p3_op = self.optimization_matrix.P3.iat[id_op]  
        self.oos_settings = self.oos_settings.append({'P1':p1_op,'P2':p2_op,'P3':p3_op}, ignore_index=True)


    # Funcion que filtra los días del IS
    def filter_is_days(self, is_ini: int, is_end: int) -> None:
        self.is_data = self.data[(self.data['Market_Day']>=is_ini) & (self.data['Market_Day']<is_end)].copy()
        self.is_data = self.is_data.reset_index()     


    @staticmethod
    def filter_df_days(df: pd.DataFrame, ini: int, end: int) -> pd.DataFrame:
        filter_df = df[(df['Market_Day']>=ini) & (df['Market_Day']<end)].copy()
        return filter_df.reset_index()


    # Funcion que itera los parámetros y rellena la matrix de optimizacion para un IS dado
    def get_optimization_matrix(self) -> None:
        for p1 in self.param1_values:
            #Asignamos el parametro
            self.is_setting = self.update_setting(self.is_setting,self.param1_name,p1)
            #Comprobamos si hay un segundo parametro
            if self.param2_name!=None:
                for p2 in self.param2_values:
                    #Asignamos el parametro
                    self.is_setting = self.update_setting(self.is_setting,self.param2_name,p2)
                    #Comprobamos si hay un tercer parametro
                    if self.param3_name is not None:
                        for p3 in self.param3_values:
                            #Asignamos el parametro
                            self.is_setting = self.update_setting(self.is_setting,self.param3_name,p3)
                            objective = self.get_objetive_function_value()
                            #Almacenamos el caso
                            self.optimization_matrix=self.optimization_matrix.append({'P1':p1,'P2':p2,'P3':p3,'OF':objective},ignore_index=True)

                    else:
                        #Ejecutamos el caso p2
                        objective = self.Execute_Optimization()
                        #Almacenamos el caso
                        self.optimization_matrix=self.optimization_matrix.append({'P1':p1,'P2':p2,'P3':None,'OF':objective},ignore_index=True)

            else: 
                #Ejecutamos el caso p1
                objective = self.Execute_Optimization()
                #Almacenamos el caso
                self.optimization_matrix=self.optimization_matrix.append({'P1':p1,'P2':None,'P3':None,'OF':objective},ignore_index=True)  


    #Funcion que ejecuta el caso selecionado para su optimización
    def get_objetive_function_value(self)-> object:
        """Funcion que ejecuta el caso que esté seleccionado y devuelve el valor de la función objetivo

        Returns:
            object: Devuelve el valor numérico de la OF que puede ser int o float
        """
        # Objeto datacandle
        datacandle = cDataCandle(data=self.is_data, setting= self.is_setting, super='wfa')
        datacandle.Calculate_Model()

        #Objeto case
        self.case = cCase(data=datacandle.data,
                          setting=self.is_setting, 
                          m1data = self.m1_data,
                          tc_assumptions= self.tc_assumptions,
                          strategy_settings = self.strategy_settings,
                          strategy_type = self.strategy_type
                    ) 
        
        # Resolvemos
        for day in set(self.case.data.Market_Day):
            self.case.check_session(day)

        # Creamos el objeto result y filter      
        self.case.get_result()

        #Calculamos el valor de la funcion objetivo
        _objective=0
        if self.objective_function == self.OBJECTIVE_FUNCTIONS[1]:
            _objective=self.case.filter.result.Get_Attribute_Serie('cash_balance').tail(1).iat[0]
        elif self.objective_function == self.OBJECTIVE_FUNCTIONS[2]:
            _objective=self.case.filter.result.Get_Attribute_Serie('rwin').tail(1).iat[0]
        elif self.objective_function == self.OBJECTIVE_FUNCTIONS[3]:
            _objective=self.case.filter.result.Get_Attribute_Serie('profit_factor').tail(1).iat[0]
        elif self.objective_function == self.OBJECTIVE_FUNCTIONS[4]:
            _objective=self.case.filter.result.Get_Attribute_Serie('cash_drawdown_max').tail(1).iat[0]
        elif self.objective_function == self.OBJECTIVE_FUNCTIONS[5]:
            _objective=self.case.filter.result.dailyresult.windays_percentage
        
        return _objective

    #Funcion que asigna el valor al parametro seleccionado
    def update_setting(self,setting: dict,_param: str,_value) -> dict:        
        if _param in self.strategy_parameters_values:
            setting['strategyparameters'][_param] = _value
        elif _param in self.trademanagement_values: 
            setting['trademanagement'][_param] = _value           
        elif len(setting['indicators']['indicators'])>0:            
            for indi in setting['indicators']['indicators']:   
                if _param.split('_')[0] in self.indicators_values[indi]:
                    setting['indicators'][indi][_param.split('_')[1]] = _value
        return setting
            
    #Función que ejecuta un periodo con los parametros obtenidos en la optimización
    def run_optimized_period(self, _case: int, strategy_settings: dict, strategy_type: str):

        #Determinamos los inicios y fin de cada periodo, incluyendo IS y OOS
        _is_ini = 1 + self.oos_days*_case
        _oos_ini = _is_ini + self.is_days
        _oos_end = _oos_ini + self.oos_days

        #Filtramos la matriz de datos y nos quedamos solo con los OOS
        oos_data = self.filter_df_days(self.data, _oos_ini,_oos_end)
                  
        #Asignamos los parámetros optimizados al caso
        oos_setting = self.set_optimal_oos_setting(_case)

        # Objeto datacandle
        datacandle = cDataCandle(data=oos_data, setting= oos_setting, super='wfa')
        datacandle.Calculate_Model()
        # Al calcular el modelo en cada periodo el Market_Day se reinicia. Para que no se confunda tenemos actualizar sumando los OOS anteriores
        datacandle.data.Market_Day = datacandle.data.Market_Day.apply(lambda x: x+self.oos_days*_case)

        #Objeto case
        self.cases.append(cCase(data=datacandle.data, setting=oos_setting, m1data = self.m1_data, tc_assumptions= self.tc_assumptions, strategy_settings=strategy_settings, strategy_type=strategy_type))
        
        # Resolvemos
        for day in set(self.cases[_case].data.Market_Day):
            self.cases[_case].check_session(day)

        # Creamos el objeto result y filter      
        self.cases[_case].get_result()
        self.cases[_case].filter.result.get_all_result_attributes()

            
            
        #TODO: Duda . Quizás sea mejor cambiar el parametro initial balance de cada OOS con el balance final que se obtenga del OOS anterior



        # Ahora hay que seleccionar sólo los trades dentro del OOS y los añadimos al dataframe de los oos 
        if _case == 0:
            self.oos_results = pd.DataFrame()
            # Lista para saber donde estan los ultimos trades de cada periodo
            self.oos_results_periods = []      
            # Lista para las posiciones y ordenes de cada periodo
            self.oos_positions = []
            self.oos_orders = []     

       
        # Concatenamos el oos_data
        self.oos_data = pd.concat([self.oos_data, self.cases[_case].data.copy()], axis = 0)
        self.oos_data = self.oos_data.reset_index(drop=True)

        # Concatenamos las posiciones y ordenes
        self.oos_positions.append(self.cases[_case].positions)
        self.oos_orders.append(self.cases[_case].orders)

        
        # Concatenamos los dataframe de result
        self.oos_results = pd.concat([self.oos_results, self.cases[_case].filter.result.data.copy()], axis = 0)
        self.oos_results = self.oos_results.reset_index(drop=True)
        
        #Almacenamos la longitud en trades de cada periodo OOS
        self.oos_results_periods.append(len(self.oos_results))

    # Funcion que cambia los parametros optimizados del diccionario setting dado
    def set_optimal_oos_setting(self,_case:int) -> dict:
        #Asignamos los parámetros optimizados al caso
        _p1 = self.oos_settings.P1.iat[_case]
        _p2 = self.oos_settings.P2.iat[_case]
        _p3 = self.oos_settings.P3.iat[_case]


        oos_setting = self.setting
        if _p1 is not None:
            oos_setting = self.update_setting(oos_setting,self.param1_name,_p1)
            
        if _p2 is not None:
            oos_setting = self.update_setting(oos_setting,self.param2_name,_p2)

        if _p3 is not None:
            oos_setting = self.update_setting(oos_setting,self.param3_name,_p3)
        
        return oos_setting



    #Función que asigna los parametros optimizados al caso seleccionado
    def set_optimal_parameter(self, _case, _param, _value):       
        if _param in self.strategy_parameters_values:
            self.cases[_case].data.setting.strategyparameters.__dict__[_param] = _value
        elif _param in self.trademanagement_values: 
            self.cases[_case].data.setting.trademanagement.__dict__[_param] = _value           
        elif len(self.case.data.setting.indicators.indicators)>0:            
            for indi in self.case.data.setting.indicators.indicators:   
                if _param.split('_')[0] in self.indicators_values[indi]:
                    self.cases[_case].data.setting.indicators.__dict__[indi][_param.split('_')[1]] = _value

    #Función que crea un objeto de la clase result con los datos unificados de los OOS optimizados
    def unify_oos_result(self):
        # Para unificar los result de los OOS :
       
        # 1) Instanciamos un objeto result como wfa. Solo pasamos el setting
        self.unified_oos = cResult(setting = self.setting, wfa=True)

        # 2) Asignamos el dataframe de los result de los oos
        self.unified_oos.data = self.oos_results

        # 3) Creamos el objeto dailyresult
        self.unified_oos.get_dailystatictis()
        

        