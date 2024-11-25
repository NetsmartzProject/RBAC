from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.model import Organisation,SubOrganisation,User
from Utills.oauth2 import get_current_user_with_roles
from database.database import get_db
from typing import Any, List, Optional
from sqlalchemy import select
from Utills.tool import add_tool, assign_ai_tokens_to_organisation, assign_ai_tokens_to_suborganisation, assign_ai_tokens_to_user, assign_hits_to_organisation, assign_hits_to_suborganisation, assign_hits_to_user,assign_tools_to_organisation,assign_tools_to_suborganisation,assign_tools_to_user, delete_tool, fetch_all_tools, fetch_tool_by_id, fetch_tool_by_name
from Schema.tool_schema import AssignAiTokensSchema, AssignHitsSchema, AssignToolSchema, Tool

router = APIRouter()

@router.get("/listorganizations")
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

    return {"Organizations": [
        {
            "org_id": org.org_id,
            "org_name": org.org_name,
            "email": org.email,
            "allocated_hits": org.allocated_hits,
            "remaining_hits": org.available_hits,
        }
        for org in organizations
    ]}

@router.get("/listsuborganizations")
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

    return {"suborganizations":[
        {
            "sub_org_id": sub_org.sub_org_id,
            "sub_org_name": sub_org.sub_org_name,
            "org_id":sub_org.org_id,
            "email": sub_org.email,
            "allocated_hits": sub_org.allocated_hits,
            "remaining_hits": sub_org.available_hits,
        }
        for sub_org in sub_organizations
    ]}

@router.get("/users")
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

    return {"users":[
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
    ]}

@router.post("/assign_tool_to_user")
async def assign_tool_to_user(
    request: AssignToolSchema,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "user", "org", "sub_org"]))
):
    user, role = current_user
    ID = request.target_user_id
    tool_ids = request.tools_ids
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
        return {"message":"Tool/s is/are successfully added", "result":result}
    except Exception as e:
        print(f"Unexpected error in create_tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))
 
 
@router.delete("/tool/{tool_id}")
async def remove_tool(
    tool_id: UUID = Path(..., description="The ID of the tool to be deleted."),
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
    tool_id: UUID = Query(..., description="The ID of the tool to be retrieved."),
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
        return {"message":result}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error in get_tool_by_id: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
 
@router.get("/tool")
async def get_tool_by_name(
    tool_name: str = Query(..., description="The Name of the tool to be retrieved."),
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin"]))
) -> Any:
    """
    Retrieve a tool by its ID. Only accessible to superadmin users.
    """
    try:
        user, role = current_user
        result = await fetch_tool_by_name(tool_name, db)
        if not result:
            raise HTTPException(status_code=404, detail="Tool not found.")
        return {"message":result}
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
        return {"message":result}
    except Exception as e:
        print(f"Unexpected error in get_all_tools: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

@router.post("/allocate_hits")
async def hit_allocation(
    hit:AssignHitsSchema,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org"]))
    ):
    user, role = current_user
    ID = hit.target_user_id
    hits = hit.hits
    if role == "superadmin":
        result = await assign_hits_to_organisation(ID, hits, db)
    elif role == "org":
        result = await assign_hits_to_suborganisation(ID,hits,db)
    elif role == "sub_org":
        result = await assign_hits_to_user(ID,hits,db)
    else:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    return {"message":result}

@router.post("/allocate_ai_tokens")
async def ai_token_allocation(
    ai_token: AssignAiTokensSchema,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org"]))
):
    user, role = current_user
    ID = ai_token.target_user_id
    tokens = ai_token.tokens
    
    if role == "superadmin":
        result = await assign_ai_tokens_to_organisation(ID, tokens, db)
    elif role == "org":
        result = await assign_ai_tokens_to_suborganisation(ID, tokens, db)
    elif role == "sub_org":
        result = await assign_ai_tokens_to_user(ID, tokens, db)
    else:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    return {"message": result}