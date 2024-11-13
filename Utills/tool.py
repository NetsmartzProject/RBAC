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

async def add_tool(org: Tool, current_user: tuple, db: AsyncSession) -> ToolResponse:
    try:
        new_tool = ToolMaster(
            tool_name=org.toolname,
            description=org.description,
            is_active=True
        )
        print(new_tool,"this is my new Tool")
        
 
        db.add(new_tool)
        await db.commit()
        await db.refresh(new_tool)
        
        return ToolResponse(
            tool_id=new_tool.tool_id,
            tool_name=new_tool.tool_name,
            description=new_tool.description
        )

    
    except Exception as e:
        print(e)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create Table: {str(e)}")

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
