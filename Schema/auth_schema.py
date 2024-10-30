from pydantic import BaseModel, EmailStr, Field, model_validator,field_validator
from uuid import UUID
from typing import List, Optional
import re


class OrganisationBase(BaseModel):
    org_name: str
    org_email: EmailStr
    org_password: str
    total_hits_limit: int
    available_hits: int
    
    

class OrganisationResponse(OrganisationBase):
    org_id:int
    superadmin_id:int
    org_name:str
    org_email:EmailStr
    org_password:str 
    
    
    
    
    
    
    class Config:
        orm_mode=True
    
    

