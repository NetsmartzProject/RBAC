from pydantic import BaseModel, EmailStr, Field, model_validator,field_validator,constr
from uuid import UUID
from typing import List, Optional,Union
import re
import regex
from typing import Literal
from database.model import Role

class Tool(BaseModel):
    toold:int
    toolname:str
    description:str
    
class ToolResponse(BaseModel):
    tool_id: int
    tool_name: str
    description: str
