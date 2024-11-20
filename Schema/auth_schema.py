from uuid import UUID
from pydantic import BaseModel, EmailStr
from typing import List, Optional,Union

class UserBase(BaseModel):
    name:str
    email:EmailStr
    username: str 
    password:str
    allocated_hits:int
    
class SubOrganisationBase(BaseModel):
    sub_org_name:str
    sub_org_email:EmailStr
    username: str
    sub_org_password:str
    allocated_hits:int
    

class SuborganisationResponse(BaseModel):
    sub_org_name:str
    sub_org_email:EmailStr
    username: str
    allocated_hits:int
    created_by_org_id:UUID


class EditOrganisation(BaseModel):
    org_name:str
    org_email:EmailStr
    allocated_hits:int
    username: str 
    tools: List[int] = []


# Remaining are tools in EditOrganisation 
    
class OrganisationBase(BaseModel):
    org_name: str
    org_email: EmailStr
    org_password: str
    allocated_hits: int
    username: str
    available_hits: Optional[int] = 0 
    

class OrganisationResponse(BaseModel):
    org_id: UUID
    created_by_admin: UUID
    org_name: str
    org_email: EmailStr
    username: str
    allocated_hits:int

class UserCommon(BaseModel):
    name : str
    email : EmailStr
    password : str
    total_hits : int
    username: str  


class UserResponse(BaseModel):
    name:str
    email : EmailStr
    allocated_hits:int
    user_name: str
    created_by_admin: UUID

class UserLogin(BaseModel):
    email: str
    password: str
    tool_id:Optional[UUID] = None

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
    allocated_hits: Optional[int] = None  
       
class ForgotPassword(BaseModel):
    email:EmailStr
  
    class Config:
         arbitrary_types_allowed = True