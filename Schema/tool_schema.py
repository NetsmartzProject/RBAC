# from pydantic import BaseModel, EmailStr, Field, model_validator,field_validator,constr
# from uuid import UUID
# from typing import List, Optional,Union
# import re
# import regex
# from typing import Literal
# from database.model import Role

# class Tool(BaseModel):
#     toolname:str
#     description:str
    
# class ToolResponse(BaseModel):
#     tool_id: int
#     tool_name: str
#     description: str

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