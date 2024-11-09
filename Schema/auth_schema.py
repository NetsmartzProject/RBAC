from pydantic import BaseModel, EmailStr, Field, model_validator,field_validator
from uuid import UUID
from typing import List, Optional,Union
import re
from typing import Literal
from database.model import Role

class UserBase(BaseModel):
    username:str
    email:EmailStr
    password:str
    allocated_hits:int
    
class SubOrganisationBase(BaseModel):
    sub_org_name:str
    sub_org_email:EmailStr
    sub_org_password:str
    allocated_hits:int
    remaining_hits:int
    used_hits:int
    

class SuborganisationResponse(BaseModel):
    sub_org_name:str
    sub_org_email:EmailStr
    allocated_hits:int
    created_by_org_id:int


    
class OrganisationBase(BaseModel):
    org_name: str
    org_email: EmailStr
    org_password: str
    total_hits_limit: int
    available_hits: Optional[int] = 0 
    parent_sub_org_name: str | None = None
    

class OrganisationResponse(BaseModel):
    org_id: int
    created_by_admin: int
    org_name: str
    org_email: EmailStr

class UserCommon(BaseModel):
    name : str
    email : EmailStr
    password : str
    total_hits : int
    role:Role

class UserResponse(BaseModel):
    name:str
    email : EmailStr
    allocated_hits:int



    
    

class UserLogin(BaseModel):
    username: str
    password: str

class VerifyUser(BaseModel):
    Email:EmailStr
    Role:str
class ResponseData(BaseModel):
    status: str
    data: Union[OrganisationBase, SubOrganisationBase, UserBase]


class CommonBase(BaseModel):
    name: str 
    email: EmailStr
    password: str
    allocated_hits: Optional[int] = None  
    total_hits_limit: Optional[int] = None  
    
    class Config:
         arbitrary_types_allowed = True

        # from_attributes = True

        # orm_mode=True
    
