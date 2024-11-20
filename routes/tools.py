from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.model import Organisation,SubOrganisation,User
from Utills.oauth2 import get_current_user_with_roles
from database.database import get_db
from typing import Any, List, Optional
from sqlalchemy import select
from Utills.tool import add_tool,assign_tools_to_organisation,assign_tools_to_suborganisation,assign_tools_to_user, delete_tool, fetch_all_tools, fetch_tool_by_id
from Schema.tool_schema import Tool

router = APIRouter()

@router.get("/listorganizations", response_model=List[dict])
async def get_organizations(
    current_user: list = Depends(get_current_user_with_roles(["superadmin"])),
    db: AsyncSession = Depends(get_db)
):
    user_info, user_role = current_user

    if user_role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for non-superadmin users"
        )

    # Fetch all organizations
    orgs_result = await db.execute(select(Organisation))
    organizations = orgs_result.scalars().all()

    return [
        {
            "org_id": org.org_id,
            "org_name": org.org_name,
            "email": org.email,
            "allocated_hits": org.allocated_hits,
            "remaining_hits": org.available_hits,
        }
        for org in organizations
    ]

@router.get("/listsuborganizations", response_model=List[dict])
async def get_suborganizations(
    org_id: Optional[UUID] = None,
    current_user: list = Depends(get_current_user_with_roles(["superadmin", "org"])),
    db: AsyncSession = Depends(get_db)
):
    user_info, user_role = current_user

    if user_role == 'superadmin' and org_id == None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide Organization Id"
        )

    if user_role == 'org':
        org_id = getattr(user_info, 'org_id', None)

    # Fetch suborganizations for the specified organization
    sub_orgs_result = await db.execute(
        select(SubOrganisation).filter(SubOrganisation.org_id == org_id)
    )
    sub_organizations = sub_orgs_result.scalars().all()

    return [
        {
            "sub_org_id": sub_org.sub_org_id,
            "sub_org_name": sub_org.sub_org_name,
            "org_id":sub_org.org_id,
            "email": sub_org.email,
            "allocated_hits": sub_org.allocated_hits,
            "remaining_hits": sub_org.available_hits,
        }
        for sub_org in sub_organizations
    ]

@router.get("/users", response_model=List[dict])
async def get_users_by_suborg(
    sub_org_id: Optional[UUID],
    current_user: list = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org"])),
    db: AsyncSession = Depends(get_db)
):
    user_info, user_role = current_user

    if (user_role == 'superadmin' and sub_org_id is None) or (user_role == 'org' and sub_org_id is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide Suborganization Id"
        )

    if user_role == 'sub_org':
        sub_org_id = getattr(user_info, 'sub_org_id', None)

    # Fetch users for the specified suborganization
    users_result = await db.execute(
        select(User).filter(User.sub_org_id == sub_org_id)
    )
    users = users_result.scalars().all()

    return [
        {
            "user_id": user.user_id,
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "allocated_hits": user.allocated_hits,
            "remaining_hits": user.available_hits,
            "is_active": user.is_active,
        }
        for user in users
    ]

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

@router.post("/tool")
async def create_tool(
    tool: Tool,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin"]))
) -> Any:
    """
    Create a new tool. Only accessible to superadmin users.
    """
    try:
        user, role = current_user
        result = await add_tool(tool, db)
        return result
    except Exception as e:
        print(f"Unexpected error in create_tool: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
 
 
@router.delete("/tool/{tool_id}")
async def remove_tool(
    tool_id: int = Path(..., description="The ID of the tool to be deleted."),
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin"]))
) -> Any:
    """
    Delete a tool (soft delete) by its ID. Only accessible to superadmin users.
    """
    try:
        user, role = current_user
        result = await delete_tool(tool_id, db)
        if not result:
            raise HTTPException(status_code=404, detail="Tool not found.")
        return {"message": "Tool successfully deleted.", "tool_id": tool_id}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error in remove_tool: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
 
 
@router.get("/tool")
async def get_tool_by_id(
    tool_id: int = Query(..., description="The ID of the tool to be retrieved."),
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin"]))
) -> Any:
    """
    Retrieve a tool by its ID. Only accessible to superadmin users.
    """
    try:
        user, role = current_user
        result = await fetch_tool_by_id(tool_id, db)
        if not result:
            raise HTTPException(status_code=404, detail="Tool not found.")
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error in get_tool_by_id: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
 
 
@router.get("/tool/all")
async def get_all_tools(
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin"]))
) -> Any:
    """
    Retrieve all tools. Only accessible to superadmin users.
    """
    try:
        user, role = current_user
        result = await fetch_all_tools(db)
        return result
    except Exception as e:
        print(f"Unexpected error in get_all_tools: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")