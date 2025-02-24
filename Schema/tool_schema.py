from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator,field_validator,constr
from uuid import UUID
from typing import List, Optional,Union
import re
import regex
from typing import Literal
from database.model import Role
 
class Tool(BaseModel):
    toolname:str
    description:str
   
class ToolResponse(BaseModel):
    tool_id: UUID
    tool_name: str
    description: str
 
class AddToolResponse(BaseModel):
    message: str
    organization_id: UUID
    tool_ids: List[UUID]
    tool_grant_dates: List[datetime]

class AssignToolSchema(BaseModel):
    target_user_id: UUID
    tools_ids: List[UUID]

class AssignHitsSchema(BaseModel):
    target_user_id: UUID
    hits: int = Field(..., gt=0, description="Number of hits to assign")

class AssignAiTokensSchema(BaseModel):
    target_user_id: UUID
    tokens: int = Field(..., gt=0, description="Number of AI tokens to assign")
