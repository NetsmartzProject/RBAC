from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from database.model import Admin,Organisation,SubOrganisation,User, Role
from Utills.oauth2 import create_access_token,get_current_user_with_roles,verify_password
from database.database import get_db
from datetime import timedelta
from pydantic import BaseModel
from typing import Union
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from config.pydantic_config import settings
from Utills.tool import mastertool,assign_tools_to_organisation,assign_tools_to_suborganisation,assign_tools_to_user
from Schema.tool_schema import Tool,ToolResponse
from database.model import MasterTable
from datetime import datetime


router = APIRouter()


@router.get("/subOrgss")
async def getSubOrganizations(
    current_user: list = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org", "user"])),
    db: AsyncSession = Depends(get_db)
):
    user_info, user_role = current_user
    print(user_info,"userinf")
    if user_role != 'org':
        return {"message": "No Access"} 

    result = await db.execute(select(SubOrganisation).filter(SubOrganisation.org_id == user_info[0]))

    sub_organisations = result.scalars().all()

    sub_organisations_list = [
        {
            "sub_org_id": sub_org.sub_org_id,
            "org_id": sub_org.org_id,
            "username": sub_org.username,
            "sub_org_name": sub_org.sub_org_name,
            "is_parent": sub_org.is_parent,
            "email": sub_org.email,
            "allocated_hits": sub_org.allocated_hits,
            "remaining_hits": sub_org.remaining_hits,
            "used_hits": sub_org.used_hits,
            "tool_ids":sub_org.tool_ids,
            "tool_grant_dates":sub_org.tool_grant_dates,
            "created_at": sub_org.created_at.isoformat() if sub_org.created_at else None,
            "updated_at": sub_org.updated_at.isoformat() if sub_org.updated_at else None,
        }
        for sub_org in sub_organisations
    ]
    
    return sub_organisations_list




@router.post("/create_tools")
async def creat_tools(
    user: Tool,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin"]))
    ):
    user1, role = current_user
    if user1.role == 'superadmin':
        org = Tool(toold=user.toold, toolname=user.toolname, description=user.description)
        return await create_tool(org, db, current_user)


async def create_tool(
    org: Tool,
    db: AsyncSession,
    current_user: tuple
):
    user, role = current_user
    print(user)
    result = await mastertool(org, user, db)
    return result



@router.post("/assign_tool_to_user")
async def assign_tool_to_user(
    ID: int,
    tool_ids: list[int],
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "user", "org", "sub_org"]))
):
    user, role = current_user
    
    if role == "superadmin":
        return await assign_tools_to_organisation(ID, tool_ids, db)
    
    elif role == "org":
        return await assign_tools_to_suborganisation(ID,tool_ids,db)
    
    elif role == "sub_org":
        return await assign_tools_to_user(ID,tool_ids,db)
    
    else:
        raise HTTPException(status_code=403, detail="Unauthorized access")


