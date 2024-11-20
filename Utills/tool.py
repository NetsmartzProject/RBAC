from datetime import datetime , timedelta
from fastapi import Depends, status, HTTPException, Request
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from database import model,database
from uuid import UUID
from config.pydantic_config import settings
from database.database import get_db
from sqlalchemy import text, select,update
from sqlalchemy.orm import Session
from typing import Literal, List
from Schema.tool_schema import Tool,ToolResponse
from database.model import ToolMaster
from database.model import Organisation, ToolMaster,SubOrganisation,User

# async def add_tool(org: Tool, current_user: tuple, db: AsyncSession) -> ToolResponse:
#     try:
#         new_tool = ToolMaster(
#             tool_name=org.toolname,
#             description=org.description,
#             is_active=True
#         )
#         print(new_tool,"this is my new Tool")
        
 
#         db.add(new_tool)
#         await db.commit()
#         await db.refresh(new_tool)
        
#         return ToolResponse(
#             tool_id=new_tool.tool_id,
#             tool_name=new_tool.tool_name,
#             description=new_tool.description
#         )

    
#     except Exception as e:
#         print(e)
#         await db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to create Table: {str(e)}")

async def add_tool(tool: Tool, db: AsyncSession) -> ToolResponse:
    try:
        # Check if a tool with the same name already exists
        result = await db.execute(select(ToolMaster).filter(ToolMaster.tool_name == tool.toolname))
        existing_tool = result.scalar_one_or_none()  # Get the first result or None

        if existing_tool:
            # If tool already exists, raise an HTTP exception with status code 400
            raise HTTPException(status_code=400, detail="Tool with this name already exists.")
        
        # Create a new tool
        new_tool = ToolMaster(
            tool_name=tool.toolname,
            description=tool.description,
            is_active=True
        )
        print(new_tool, "this is my new Tool")
        
        # Add and commit the new tool to the database
        db.add(new_tool)
        await db.commit()
        await db.refresh(new_tool)
        
        # Return the response with the new tool details
        return ToolResponse(
            tool_id=new_tool.tool_id,
            tool_name=new_tool.tool_name,
            description=new_tool.description
        )

    except Exception as e:
        print(e)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create tool: {str(e)}")
 
async def fetch_all_tools(db: AsyncSession) -> List[ToolResponse]:
    try:
        query = select(ToolMaster).where(ToolMaster.is_active == True)
        result = await db.execute(query)
        tools = result.scalars().all()
 
        return [
            ToolResponse(
                tool_id=tool.tool_id,
                tool_name=tool.tool_name,
                description=tool.description
            )
            for tool in tools
        ]
 
    except Exception as e:
        print(f"Error fetching tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tools: {str(e)}")
 
async def fetch_tool_by_id(tool_id: int, db: AsyncSession) -> ToolResponse:
    try:
        query = select(ToolMaster).where(ToolMaster.tool_id == tool_id, ToolMaster.is_active == True)
        result = await db.execute(query)
        tool = result.scalar_one_or_none()
 
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found.")
 
        return ToolResponse(
            tool_id=tool.tool_id,
            tool_name=tool.tool_name,
            description=tool.description
        )
 
    except Exception as e:
        print(f"Error fetching tool by ID: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tool: {str(e)}")
 
async def update_tool(tool_id: int, tool_update: Tool, db: AsyncSession) -> ToolResponse:
    try:
        query = select(ToolMaster).where(ToolMaster.tool_id == tool_id, ToolMaster.is_active == True)
        result = await db.execute(query)
        tool = result.scalar_one_or_none()
 
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found.")
 
        tool.tool_name = tool_update.toolname
        tool.description = tool_update.description
 
        await db.commit()
        await db.refresh(tool)
 
        return ToolResponse(
            tool_id=tool.tool_id,
            tool_name=tool.tool_name,
            description=tool.description
        )
 
    except Exception as e:
        await db.rollback()
        print(f"Error updating tool: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update tool: {str(e)}")
 
async def delete_tool(tool_id: int, db: AsyncSession):
    try:
        query = select(ToolMaster).where(ToolMaster.tool_id == tool_id, ToolMaster.is_active == True)
        result = await db.execute(query)
        tool = result.scalar_one_or_none()
 
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found.")
 
        tool.is_active = False  # Perform a soft delete
        await db.commit()
 
        return {"message": f"Tool with ID {tool_id} has been deactivated successfully."}
 
    except Exception as e:
        await db.rollback()
        print(f"Error deleting tool: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete tool: {str(e)}")
 

# async def assign_tools_to_suborganisation(
#     sub_org_id: int,
#     tool_ids: list[int],
#     db: AsyncSession
# ) -> dict:
#     tool_query = await db.execute(select(ToolMaster).filter(ToolMaster.tool_id.in_(tool_ids)))
#     existing_tools = tool_query.scalars().all()
    
#     if len(existing_tools) != len(tool_ids):
#         raise HTTPException(status_code=404, detail="One or more tools not found")

#     org_query = await db.execute(select(SubOrganisation).filter(SubOrganisation.sub_org_id == sub_org_id))
#     target_org = org_query.scalar()
    
#     if not target_org:
#         raise HTTPException(status_code=404, detail="Sub-organisation not found")

#     existing_tool_ids = set(target_org.tool_ids or [])
#     new_tool_ids = [tool_id for tool_id in tool_ids if tool_id not in existing_tool_ids]
    
#     if not new_tool_ids:
#         return {
#             "message": "All provided tool IDs are already assigned to this sub-organisation",
#             "sub_org_id": sub_org_id,
#             "existing_tool_ids": list(existing_tool_ids)
#         }

#     updated_tool_ids = list(existing_tool_ids | set(new_tool_ids))
#     updated_tool_grant_dates = (target_org.tool_grant_dates or []) + [datetime.now() for _ in new_tool_ids]
    
#     target_org.tool_ids = updated_tool_ids
#     target_org.tool_grant_dates = updated_tool_grant_dates

#     print("Tool IDs before commit:", target_org.tool_ids)
#     await db.commit()
#     await db.refresh(target_org)
#     print("Tool IDs after commit:", target_org.tool_ids)

#     return {
#         "message": "Tools assigned successfully",
#         "sub_org_id": sub_org_id,
#         "tool_ids": target_org.tool_ids
#     }

async def assign_tools_to_suborganisation(
    sub_org_id: int,
    tool_ids: list[int],
    db: AsyncSession
) -> dict:
    tool_query = await db.execute(select(ToolMaster).filter(ToolMaster.tool_id.in_(tool_ids)))
    existing_tools = tool_query.scalars().all()
    
    if len(existing_tools) != len(tool_ids):
        raise HTTPException(status_code=404, detail="One or more tools not found")

    org_query = await db.execute(select(SubOrganisation).filter(SubOrganisation.sub_org_id == sub_org_id))
    target_org = org_query.scalar()
    
    if not target_org:
        raise HTTPException(status_code=404, detail="Sub-organisation not found")

    parent_org = await db.execute(select(Organisation).filter(Organisation.org_id == target_org.org_id))
    parent_org = parent_org.scalar()
    
    if not parent_org:
        raise HTTPException(status_code=404, detail="Parent organisation not found")

    parent_tool_ids = set(parent_org.tool_ids or [])

    invalid_tools = [tool_id for tool_id in tool_ids if tool_id not in parent_tool_ids]
    
    if invalid_tools:
        raise HTTPException(status_code=400, detail=f"Tools {invalid_tools} are not available in the parent organisation")

    existing_tool_ids = set(target_org.tool_ids or [])
    new_tool_ids = [tool_id for tool_id in tool_ids if tool_id not in existing_tool_ids]
    
    if not new_tool_ids:
        return {
            "message": "All provided tool IDs are already assigned to this sub-organisation",
            "sub_org_id": sub_org_id,
            "existing_tool_ids": list(existing_tool_ids)
        }

    updated_tool_ids = list(existing_tool_ids | set(new_tool_ids))
    updated_tool_grant_dates = (target_org.tool_grant_dates or []) + [datetime.now() for _ in new_tool_ids]
    
    target_org.tool_ids = updated_tool_ids
    target_org.tool_grant_dates = updated_tool_grant_dates

    print("Tool IDs before commit:", target_org.tool_ids)
    await db.commit()
    await db.refresh(target_org)
    print("Tool IDs after commit:", target_org.tool_ids)

    return {
        "message": "Tools assigned successfully",
        "sub_org_id": sub_org_id,
        "tool_ids": target_org.tool_ids
    }

# WORKING FINE FOR SUBORGANISATION ON THE BASIS OF ROLE

async def assign_tools_to_user(
    user_id: int,
    tool_ids: list[int],
    db: AsyncSession
) -> dict:
    tool_query = await db.execute(select(ToolMaster).filter(ToolMaster.tool_id.in_(tool_ids)))
    existing_tools = tool_query.scalars().all()
    
    if len(existing_tools) != len(tool_ids):
        raise HTTPException(status_code=404, detail="One or more tools not found")

    org_query = await db.execute(select(User).filter(User.user_id == user_id))
    target_org = org_query.scalar()
    
    if not target_org:
        raise HTTPException(status_code=404, detail="Sub-organisation not found")

    existing_tool_ids = set(target_org.tool_ids or [])
    new_tool_ids = [tool_id for tool_id in tool_ids if tool_id not in existing_tool_ids]
    
    if not new_tool_ids:
        return {
            "message": "All provided tool IDs are already assigned to this sub-organisation",
            "sub_org_id": user_id,
            "existing_tool_ids": list(existing_tool_ids)
        }

    updated_tool_ids = list(existing_tool_ids | set(new_tool_ids))
    updated_tool_grant_dates = (target_org.tool_grant_dates or []) + [datetime.now() for _ in new_tool_ids]
    
    target_org.tool_ids = updated_tool_ids
    target_org.tool_grant_dates = updated_tool_grant_dates

    print("Tool IDs before commit:", target_org.tool_ids)
    await db.commit()
    await db.refresh(target_org)
    print("Tool IDs after commit:", target_org.tool_ids)

    return {
        "message": "Tools assigned successfully",
        "sub_org_id": user_id,
        "tool_ids": target_org.tool_ids
    }

async def assign_tools_to_organisation(
    org_id: int,
    tool_ids: list[int],
    db: AsyncSession
) -> dict:
    tool_query = await db.execute(select(ToolMaster).filter(ToolMaster.tool_id.in_(tool_ids)))
    existing_tools = tool_query.scalars().all()
    
    if len(existing_tools) != len(tool_ids):
        raise HTTPException(status_code=404, detail="One or more tools not found")

    org_query = await db.execute(select(Organisation).filter(Organisation.org_id == org_id))
    target_org = org_query.scalar()
    
    if not target_org:
        raise HTTPException(status_code=404, detail="Sub-organisation not found")

    existing_tool_ids = set(target_org.tool_ids or [])
    new_tool_ids = [tool_id for tool_id in tool_ids if tool_id not in existing_tool_ids]
    
    if not new_tool_ids:
        return {
            "message": "All provided tool IDs are already assigned to this sub-organisation",
            "sub_org_id": org_id,
            "existing_tool_ids": list(existing_tool_ids)
        }

    updated_tool_ids = list(existing_tool_ids | set(new_tool_ids))
    updated_tool_grant_dates = (target_org.tool_grant_dates or []) + [datetime.now() for _ in new_tool_ids]
    
    target_org.tool_ids = updated_tool_ids
    target_org.tool_grant_dates = updated_tool_grant_dates

    print("Tool IDs before commit:", target_org.tool_ids)
    await db.commit()
    await db.refresh(target_org)
    print("Tool IDs after commit:", target_org.tool_ids)

    return {
        "message": "Tools assigned successfully",
        "sub_org_id": org_id,
        "tool_ids": target_org.tool_ids
    }


# BY SHIVAM 

# from datetime import datetime , timedelta
# from fastapi import Depends, status, HTTPException, Request
# from jose import JWTError, jwt
# from fastapi.security import OAuth2PasswordBearer, HTTPBearer
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload
# from sqlalchemy import select
# from database import model,database
# from uuid import UUID
# from config.pydantic_config import settings
# from database.database import get_db
# from sqlalchemy import text, select,update
# from sqlalchemy.orm import Session
# from typing import Literal, List
# from Schema.tool_schema import Tool,ToolResponse
# from database.model import ToolMaster
# from database.model import Organisation, ToolMaster,SubOrganisation,User
 
# async def add_tool(org: Tool, db: AsyncSession) -> ToolResponse:
#     try:
#         new_tool = ToolMaster(
#             tool_name=org.toolname,
#             description=org.description,
#             is_active=True
#         )
#         print(new_tool,"this is my new Tool")
       
 
#         db.add(new_tool)
#         await db.commit()
#         await db.refresh(new_tool)
       
#         return ToolResponse(
#             tool_id=new_tool.tool_id,
#             tool_name=new_tool.tool_name,
#             description=new_tool.description
#         )
 
   
#     except Exception as e:
#         print(e)
#         await db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to create Table: {str(e)}")
 
# async def fetch_all_tools(db: AsyncSession) -> List[ToolResponse]:
#     try:
#         query = select(ToolMaster).where(ToolMaster.is_active == True)
#         result = await db.execute(query)
#         tools = result.scalars().all()
 
#         return [
#             ToolResponse(
#                 tool_id=tool.tool_id,
#                 tool_name=tool.tool_name,
#                 description=tool.description
#             )
#             for tool in tools
#         ]
 
#     except Exception as e:
#         print(f"Error fetching tools: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to retrieve tools: {str(e)}")
 
# async def get_tool_by_id(tool_id: int, db: AsyncSession) -> ToolResponse:
#     try:
#         query = select(ToolMaster).where(ToolMaster.tool_id == tool_id, ToolMaster.is_active == True)
#         result = await db.execute(query)
#         tool = result.scalar_one_or_none()
 
#         if not tool:
#             raise HTTPException(status_code=404, detail="Tool not found.")
 
#         return ToolResponse(
#             tool_id=tool.tool_id,
#             tool_name=tool.tool_name,
#             description=tool.description
#         )
 
#     except Exception as e:
#         print(f"Error fetching tool by ID: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to retrieve tool: {str(e)}")
 
# async def update_tool(tool_id: int, tool_update: Tool, db: AsyncSession) -> ToolResponse:
#     try:
#         query = select(ToolMaster).where(ToolMaster.tool_id == tool_id, ToolMaster.is_active == True)
#         result = await db.execute(query)
#         tool = result.scalar_one_or_none()
 
#         if not tool:
#             raise HTTPException(status_code=404, detail="Tool not found.")
 
#         tool.tool_name = tool_update.toolname
#         tool.description = tool_update.description
 
#         await db.commit()
#         await db.refresh(tool)
 
#         return ToolResponse(
#             tool_id=tool.tool_id,
#             tool_name=tool.tool_name,
#             description=tool.description
#         )
 
#     except Exception as e:
#         await db.rollback()
#         print(f"Error updating tool: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to update tool: {str(e)}")
 
# async def delete_tool(tool_id: int, db: AsyncSession):
#     try:
#         query = select(ToolMaster).where(ToolMaster.tool_id == tool_id, ToolMaster.is_active == True)
#         result = await db.execute(query)
#         tool = result.scalar_one_or_none()
 
#         if not tool:
#             raise HTTPException(status_code=404, detail="Tool not found.")
 
#         tool.is_active = False  # Perform a soft delete
#         await db.commit()
 
#         return {"message": f"Tool with ID {tool_id} has been deactivated successfully."}
 
#     except Exception as e:
#         await db.rollback()
#         print(f"Error deleting tool: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to delete tool: {str(e)}")
 
# async def add_tools_to_organisation(
#     organisation_id: int,
#     tool_ids: List[int],
#     db: AsyncSession
# ) -> dict:
#     try:
#         # Fetch the organization
#         query = select(Organisation).where(Organisation.org_id == organisation_id)
#         result = await db.execute(query)
#         organisation = result.scalars().first()
 
#         if not organisation:
#             raise HTTPException(status_code=404, detail="Organization not found.")
 
#         print(f"Current tool_ids: {organisation.tool_ids}")
 
#         # Fetch valid tools from ToolMaster
#         valid_tools_query = select(ToolMaster.tool_id).where(ToolMaster.tool_id.in_(tool_ids))
#         valid_tools_result = await db.execute(valid_tools_query)
#         valid_tool_ids = set(valid_tools_result.scalars().all())
#         print(f"Valid tool IDs from ToolMaster: {valid_tool_ids}")
 
#         # Check for invalid tool_ids
#         invalid_tool_ids = set(tool_ids) - valid_tool_ids
#         if invalid_tool_ids:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Invalid tool_ids: {invalid_tool_ids}. Tools must exist in ToolMaster."
#             )
 
#         # Filter out tools that are already granted
#         new_tools = [tool_id for tool_id in valid_tool_ids if tool_id not in organisation.tool_ids]
#         print(f"New tools to be added: {new_tools}")
 
#         if not new_tools:
#             raise HTTPException(
#                 status_code=400,
#                 detail="All provided tools are already granted to this organization."
#             )
 
#         # Add new tools and their grant dates
#         organisation.tool_ids = organisation.tool_ids + new_tools
#         organisation.tool_grant_dates = organisation.tool_grant_dates + [datetime.utcnow()] * len(new_tools)
 
#         print(f"Updated tool_ids: {organisation.tool_ids}")
#         print(f"Updated tool_grant_dates: {organisation.tool_grant_dates}")
 
#         # Commit the changes
#         await db.commit()
#         await db.refresh(organisation)
 
#         return {
#             "message": "Tools added successfully.",
#             "organization_id": organisation.org_id,
#             "tool_ids": organisation.tool_ids,
#             "tool_grant_dates": organisation.tool_grant_dates,
#         }
#     except HTTPException as e:
#         await db.rollback()
#         raise e
#     except Exception as e:
#         print(f"Error in add_tools_to_organisation: {e}")
#         await db.rollback()
#         raise HTTPException(status_code=500, detail="Internal server error.")
 
# async def add_tools_to_suborganisation(
#     suborganisation_id: int,
#     tool_ids: list[int],
#     db: AsyncSession
# ) -> dict:
#     """
#     Assign multiple tools to a suborganisation.
#     Validates the tool IDs against the Master Tool table and assigns them to the suborganisation.
#     """
#     # Check if the suborganisation exists
#     stmt = select(SubOrganisation).where(SubOrganisation.id == suborganisation_id)
#     result = await db.execute(stmt)
#     suborganisation = result.scalars().first()
   
#     if not suborganisation:
#         raise HTTPException(status_code=404, detail="Suborganisation not found.")
 
#     # Check if all tools exist in the master tool table
#     stmt = select(Tool).where(Tool.id.in_(tool_ids))
#     result = await db.execute(stmt)
#     tools = result.scalars().all()
 
#     if len(tools) != len(tool_ids):
#         raise HTTPException(status_code=404, detail="One or more tools not found in the Master Tool table.")
 
#     # Add tools to suborganisation
#     suborganisation.tool_ids.extend(tool_ids)
#     suborganisation.tool_grant_dates.extend([datetime.now()] * len(tool_ids))  # Add grant dates
 
#     # Commit the changes to the database
#     await db.commit()
 
#     return {"message": "Tools assigned successfully to the suborganisation.", "suborganisation_id": suborganisation_id, "tool_ids": tool_ids, "tool_grant_dates": suborganisation.tool_grant_dates}
 
# async def add_tools_to_user(
#     user_id: int,
#     tool_ids: list[int],
#     db: AsyncSession
# ) -> dict:
#     """
#     Assign multiple tools to a user.
#     Validates the tool IDs against the Master Tool table and assigns them to the user.
#     """
#     # Check if the user exists
#     stmt = select(User).where(User.id == user_id)
#     result = await db.execute(stmt)
#     user = result.scalars().first()
 
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found.")
 
#     # Check if all tools exist in the master tool table
#     stmt = select(Tool).where(Tool.id.in_(tool_ids))
#     result = await db.execute(stmt)
#     tools = result.scalars().all()
 
#     if len(tools) != len(tool_ids):
#         raise HTTPException(status_code=404, detail="One or more tools not found in the Master Tool table.")
 
#     # Add tools to user
#     user.tool_ids.extend(tool_ids)
#     user.tool_grant_dates.extend([datetime.now()] * len(tool_ids))  # Add grant dates
 
#     # Commit the changes to the database
#     await db.commit()
 
#     return {"message": "Tools assigned successfully to the user.", "user_id": user_id, "tool_ids": tool_ids}
 
