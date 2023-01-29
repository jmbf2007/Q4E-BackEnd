import math

class HistogramEChart():
    
#---- Constructor
    def __init__(self, data: dict):
        self.data = data        
        self.y0max = max(self.data['histogram_ydata'])
        self.y1max = max(self.data['cumhistogram_ydata'])
                
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
                "height": 450
            },
        ]

        
    def yAxis(self) -> list:
        return [
            {        
                "type": "value",
                "name": self.data['histogram_units'],
                "min": 0,
                "max": self.y0max,
                "position": 'left',
                "axisLine": {
                    "show": True,
                    "onZero": False,
                    "lineStyle": {
                        "color": "black"
                    }
                }       
            },
            {        
                "type": "value",
                "name": self.data['cumhistogram_units'],
                "min": 0,
                "max": self.y1max,
                "position": 'right',
                "axisLine": {
                    "show": True,
                    "onZero": False,
                    "lineStyle": {
                        "color": "black"
                    }
                }       
            },                    
        ]

        
    def xAxis(self) -> list:
        return [
            {
                "type": "category",
                "boundaryGap": False,
                "data": self.data['histogram_xdata'],
                "name": "Daily Return %",
                "nameLocation": "center",
                "nameTextStyle": {
                    "fontSize": 14,
                    "verticalAlign": "top",
                    "padding": [15,15]
                }          
            },
            {
                "type": "value",
                "show": False,
                "min": self.data['mean_xaxis_extremes'][0],
                "max": self.data['mean_xaxis_extremes'][1], 
            }
        ]
    
    def series(self) -> list:
        return [
            {          
                "name": self.data['histogram_trace_name'],
                "type": 'bar',
                "data": self.data['histogram_ydata'],   
                "yAxisIndex": 0,    
                "xAxisIndex": 0,                
            },
            {
                "name": self.data['cumhistogram_trace_name'],
                "type": 'line',
                "data": self.data['cumhistogram_ydata'],   
                "smooth": True,
                "yAxisIndex": 1,    
                "xAxisIndex": 0,                 
            },
            {
                "name": self.data['mean_trace_name'],
                "type": 'line',
                "data": [[self.data['mean'],0],[self.data['mean'],self.y0max]],   
                "smooth": True,
                "yAxisIndex": 0,    
                "xAxisIndex": 1,   
                "markArea": {
                    "itemStyle": {
                        "opacity": 0.3   
                    },
                    "data": [
                        [
                            {"xAxis": self.data['std1']},
                            {"xAxis": self.data['std2']}
                        ]
                    ]
                },
                "markPoint": {
                    "data": [
                        {
                            "name": 'mean', 
                            "value": round(self.data['mean'],2),
                            "xAxis": self.data['mean'],
                            "yAxis": self.y0max
                        }
                    ]
                    
                }                              
            }            
        ]

    
    def legend(self):
        return {
            "data": [
                self.data['histogram_trace_name'],
                self.data['cumhistogram_trace_name'],
                self.data['mean_trace_name']
            ]
        }
    
    def getOption(self)-> dict:
        return {
            "tooltip":  self.tooltip(),
            "legend":   self.legend(),
            "grid":     self.grid(),
            "xAxis":    self.xAxis(),
            "yAxis":    self.yAxis(),
            "series":   self.series()     
        }    