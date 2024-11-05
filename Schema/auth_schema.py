from pydantic import BaseModel, EmailStr, Field, model_validator,field_validator
from uuid import UUID
from typing import List, Optional
import re
from typing import Literal


class UserBase(BaseModel):
    username:str
    email:EmailStr
    password:str
    
class SubOrganisationBase(BaseModel):
    sub_org_name:str
    sub_org_email:EmailStr
    sub_org_password:str
    allocated_hits:int
    remaining_hits:int
    used_hits:int
    
class OrganisationBase(BaseModel):
    org_name: str
    org_email: EmailStr
    org_password: str
    total_hits_limit: int
    available_hits: int
    parent_sub_org_name: str | None = None
    

class OrganisationResponse(BaseModel):
    org_id: int
    created_by_admin: int
    org_name: str
    org_email: EmailStr


class UserLogin(BaseModel):
    username: str
    password: str

class VerifyUser(BaseModel):
    name:str
    Role:str


class CommonBase(BaseModel):
    name: str  # This can represent org_name, sub_org_name, or username
    email: EmailStr
    password: str
    allocated_hits: Optional[int] = None  # Optional for UserBase
    total_hits_limit: Optional[int] = None  
    
    class Config:
        orm_mode=True
    
