from typing import List,Optional
from pydantic import BaseModel
from bson import ObjectId



class LoginUser(BaseModel):
    username: str
    password: Optional[str]

class UserId(BaseModel):
    id: str
    
    @property
    def objectID(self):
        return ObjectId(self.id)

class Strategy(BaseModel):
    id: Optional[str]
    name: Optional[str]
    
    @property
    def objectID(self):
        return ObjectId(self.id)
     
class Model(BaseModel):
    id: Optional[str]
    name: Optional[str]
    summary: Optional[str]
    version: Optional[int]
    strategy_type: Optional[str]
    
    @property
    def objectID(self):
        return ObjectId(self.id)

class DataObjectType(BaseModel):
    dataobject: Optional[str]
    super:      Optional[str]
 
class AttributeGraph(BaseModel):
    selected_attb_group: Optional[str]
    rwin_mean_period: Optional[int]
    step: Optional[float]   
    type: Optional[str]

class EChartType(BaseModel):
    type: Optional[List]
    
class ParametricInfo(BaseModel):
    name: Optional[str]
    description: Optional[str]
    param1_name: Optional[str]
    param1_values: Optional[List]
    param2_name: Optional[str]
    param2_values: Optional[List]

class Porfolio(BaseModel):
    username: Optional[str]
    id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    strategies_name: Optional[List]
    strategies_id: Optional[List]
    models_name: Optional[List]
    models_id: Optional[List]
    required_object: Optional[str]
    account: Optional[str]
    required_attb: Optional[str]
    initial_balance: Optional[float]

    @property
    def objectID(self):
        return ObjectId(self.id)


class StrategyBuilder(BaseModel):
    name: Optional[str]
    description: Optional[str]
    owner_name: Optional[str]
    strategy_type: Optional[str]
    date_creation: Optional[int]
    last_update: Optional[int]
    owner_name: Optional[str]
    public: Optional[bool]
    version: Optional[int]
    settings: Optional[dict]
    tc_assumptions: Optional[dict]
    assumptions: Optional[dict]
    id: Optional[str]
    
    @property
    def objectID(self):
        return ObjectId(self.id)





