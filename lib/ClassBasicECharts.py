import math

class BasicEChart():
    
#---- Constructor
    def __init__(self, data: dict):
        self.data = data
        self.get_yaxis_maxmin()
        self.color_data()
        self.scatter_data()
        
    def get_yaxis_maxmin(self):
        self.ymax = []
        self.ymin = []
        for _ in range(len(self.data['yaxis_name'])):
            self.ymax.append(-1000000)
            self.ymin.append(1000000)
        
        for axis, data in zip(self.data['yaxis_traces'],self.data['yaxis_data']):
            srmin = min(data)
            srmax = max(data)
            self.ymin[axis] = math.floor(srmin) if srmin<=self.ymin[axis] else self.ymin[axis]
            self.ymax[axis] = math.ceil(srmax) if srmax>=self.ymax[axis] else self.ymax[axis]

    @staticmethod
    def tooltip()->dict:
        return {
                "trigger": "axis",
        }

    def color_data(self)->None:
        _color_data = []
        for listdata in self.data['yaxis_data']:
            data = [{"value": x, "itemStyle": {"color": ("green" if x>=0 else "red")}} for x in listdata]
            _color_data.append(data)
        self.data.update({'color_data': _color_data})
        
    def scatter_data(self)->None:
        self.data['scatter_data']=[]
        for i,scatter in enumerate(self.data['traces_type']):
            if scatter=='scatter':
                self.data['scatter_data'].append([[x,y] for x,y in zip(self.data['xaxis_data'],self.data['yaxis_data'][i])])
            else:
                self.data['scatter_data'].append([None,None])
            
    @staticmethod
    def visualMap() -> dict:
        return  {
            "top": 50,
            "right": 10,
            "pieces": [
            {
                "gt": 0,
                "color": "green"
            },
            {
                "lte": 0,
                "color": "red"
            },
            ],
        }

    @staticmethod 
    def grid()-> list:       
        return  [
            {
                "left": '5%',
                "right": '5%',
                "top": 110,
                "height": 450
            },
        ]

        
    def yAxis(self) -> list:
        _yAxis = []
        for i,yname in enumerate(self.data['yaxis_name']):
            _yAxis.append(
                {        
                    "type": "value",
                    "name": yname,
                    "min": self.ymin[i],
                    "max": self.ymax[i],
                    "axisLine": {
                        "show": True,
                        "lineStyle": {
                            "color": "black"
                        }
                    }       
                }        
            )
            
        return _yAxis
        
    def xAxis(self) -> list:
        return {
            "type": "category",
            "boundaryGap": False,
            "data": self.data['xaxis_data'],
            "name": self.data['xaxis_title'],
            "nameLocation": "center",
            "nameTextStyle": {
                "fontSize": 14,
                "verticalAlign": "top",
                "padding": [15,15]
            }          
        }
    
    def series(self) -> list:
        _serie =[]
        for ydata, tname, yaxis, type, colordata, coloured, scatter  in zip(self.data['yaxis_data'], self.data['traces_name'], self.data['yaxis_traces'], self.data['traces_type'], 
                                                    self.data['color_data'], self.data['coloured_traces'], self.data['scatter_data']) :
            if coloured:
                _data = colordata

            elif type=='scatter':
                _data = scatter
            else:
                _data = ydata
            
            _serie.append(
                {          
                    "name": tname,
                    "type": type,
                    "data": _data,   
                    "smooth": True,
                    "yAxisIndex": yaxis,    
                }           
            )
        return _serie
    
    def legend(self):
        return {
            "data": self.data['traces_name']
        }
    
    def getOption(self)-> dict:
        return {
            "tooltip":  self.tooltip(),
            "legend":   self.legend(),
            "grid":     self.grid(),
            "xAxis":    self.xAxis(),
            "yAxis":    self.yAxis(),
            "series":   self.series(),
            #"visualMap": self.visualMap()       
        }    