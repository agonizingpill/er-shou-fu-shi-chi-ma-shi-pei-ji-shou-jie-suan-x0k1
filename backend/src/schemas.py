from pydantic import BaseModel,ConfigDict,Field
from typing import Literal
class Input(BaseModel):model_config=ConfigDict(extra='forbid',str_strip_whitespace=True,allow_inf_nan=False)
class Login(Input):
 email:str;password:str
class ConsignorIn(Input):
 name:str=Field(min_length=2,max_length=80);contact:str=Field(min_length=3,max_length=100)
class AgreementIn(Input):
 code:str=Field(min_length=2,max_length=40);consignor_id:int;floor_cents:int=Field(gt=0,le=10000000);commission_bp:int=Field(ge=0,le=5000);ends:str
class AmendmentIn(Input):
 commission_bp:int=Field(ge=0,le=5000);reason:str=Field(min_length=8,max_length=500)
class GarmentIn(Input):
 agreement_id:int;code:str=Field(min_length=2,max_length=40);title:str=Field(min_length=3,max_length=100);condition:str=Field(min_length=8,max_length=300);price_cents:int=Field(gt=0,le=10000000)
class MeasurementIn(Input):
 garment_id:int;chest:float=Field(ge=40,le=180);shoulder:float=Field(ge=20,le=80);length:float=Field(ge=20,le=180);elasticity:float=Field(ge=0,le=1);cut:int=Field(ge=0,le=2)
class ProfileIn(Input):
 code:str=Field(min_length=2,max_length=40);chest:float=Field(ge=40,le=180);shoulder:float=Field(ge=20,le=80)
class AssessmentIn(Input):
 garment_id:int;profile_id:int
class FittingIn(Input):
 garment_id:int;profile_id:int;slot:int=Field(ge=1,le=2);starts:str;ends:str
class SaleIn(Input):
 fitting_id:int;price_cents:int=Field(gt=0,le=10000000)
class ReturnIn(Input):
 sale_id:int;reason:str=Field(min_length=8,max_length=500)
class InspectionIn(Input):
 outcome:Literal['relist','retire'];inspection:str=Field(min_length=8,max_length=500)
class PayoutIn(Input):
 sale_id:int;reference:str=Field(min_length=3,max_length=60)
class ReasonIn(Input):reason:str=Field(min_length=8,max_length=500)
class ClockIn(ReasonIn):now:str
