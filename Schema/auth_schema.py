from pydantic import BaseModel, EmailStr, Field, model_validator,field_validator,constr
from uuid import UUID
from typing import List, Optional,Union
import re
import regex
from typing import Literal
from database.model import Role

class UserBase(BaseModel):
    name:str
    email:EmailStr
    username: str = Field(..., pattern=r'^[a-zA-Z0-9]+$', min_length=1)  
    password:str
    allocated_hits:int
    
class SubOrganisationBase(BaseModel):
    sub_org_name:str
    sub_org_email:EmailStr
    username: str = Field(..., pattern=r'^[a-zA-Z0-9]+$', min_length=1)  
    sub_org_password:str
    allocated_hits:int
    remaining_hits:int
    used_hits:int
    

class SuborganisationResponse(BaseModel):
    sub_org_name:str
    sub_org_email:EmailStr
    username: str = Field(..., pattern=r'^[a-zA-Z0-9]+$', min_length=1)  
    allocated_hits:int
    created_by_org_id:int


    
class OrganisationBase(BaseModel):
    org_name: str
    org_email: EmailStr
    org_password: str
    total_hits_limit: int
    username: str = Field(..., pattern=r'^[a-zA-Z0-9]+$', min_length=1)  
    available_hits: Optional[int] = 0 
    parent_sub_org_name: str | None = None
    

class OrganisationResponse(BaseModel):
    org_id: int
    created_by_admin: int
    org_name: str
    org_email: EmailStr
    username: str = Field(..., pattern=r'^[a-zA-Z0-9]+$', min_length=1)  


class UserCommon(BaseModel):
    name : str
    email : EmailStr
    password : str
    total_hits : int
    username: str = Field(..., pattern=r'^[a-zA-Z0-9]+$', min_length=1)  
    # role:Role

class UserResponse(BaseModel):
    name:str
    email : EmailStr
    allocated_hits:int
    username: str = Field(..., pattern=r'^[a-zA-Z0-9]+$', min_length=1) 



    
    

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
    
