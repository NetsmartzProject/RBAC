from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.model import Organisation,SubOrganisation,User
from Utills.oauth2 import get_current_user_with_roles
from database.database import get_db
from typing import Any, List, Optional
from sqlalchemy import select
from Utills.tool import add_tool, assign_ai_tokens_to_organisation, assign_ai_tokens_to_suborganisation, \
    assign_ai_tokens_to_user, assign_hits_to_organisation, assign_hits_to_suborganisation, assign_hits_to_user, \
    assign_tools_to_organisation, assign_tools_to_suborganisation, assign_tools_to_user, delete_tool, fetch_all_tools, \
    fetch_available_hits, fetch_tool_by_id, fetch_tool_by_name, fetch_remaining_ai_tokens
from Schema.tool_schema import AssignAiTokensSchema, AssignHitsSchema, AssignToolSchema, Tool

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    org_id1: Optional[UUID] = None,
    current_user: list = Depends(get_current_user_with_roles(["superadmin", "org"])),
    db: AsyncSession = Depends(get_db)
):
    user_info, user_role = current_user

    # Base query to select all suborganizations
    query = select(SubOrganisation)

    if user_role == "superadmin":
        if org_id1:
            query = query.filter(SubOrganisation.org_id == org_id1)  # Optional filter if org_id is provided
        # No further filtering needed for superadmin, they can see all suborganizations

    elif user_role == "org":
        org_id = getattr(user_info, 'org_id', None)
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization details not found for the current user"
            )
        # Org can only see suborganizations under their own org
        query = query.filter(SubOrganisation.org_id == org_id)

    sub_orgs_result = await db.execute(query)
    sub_organizations = sub_orgs_result.scalars().all()

    if not sub_organizations:
        return {"suborganizations": []}

    sub_org_list = []
    for sub_org in sub_organizations:
        sub_org_data = {
            "sub_org_id": sub_org.sub_org_id,
            "sub_org_name": sub_org.sub_org_name,
            "org_id": sub_org.org_id,
            "email": sub_org.email,
            "allocated_hits": sub_org.allocated_hits,
            "remaining_hits": sub_org.available_hits,
        }

        sub_org_data["parent_org_id"] = sub_org.org_id
        sub_org_list.append(sub_org_data)

    return {"suborganizations": sub_org_list}

# @router.get("/listsuborganizations")
# async def get_suborganizations(
#     org_id: Optional[UUID] = None,
#     current_user: list = Depends(get_current_user_with_roles(["superadmin", "org"])),
#     db: AsyncSession = Depends(get_db)
# ):
#     user_info, user_role = current_user

#     query = select(SubOrganisation)

#     if user_role == "superadmin":
#         if org_id:
#             query = query.filter(SubOrganisation.org_id == org_id)  # Optional filter if org_id is provided
        

#     elif user_role == "org":
#         org_id = getattr(user_info, 'org_id', None)
#         if not org_id:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Organization details not found for the current user"
#             )
#         # Org can only see suborganizations under their own org
#         query = query.filter(SubOrganisation.org_id == org_id)
#         print(query, "query")

#     # Execute the query
#     sub_orgs_result = await db.execute(query)
#     sub_organizations = sub_orgs_result.scalars().all()

#     if not sub_organizations:
#         return {"suborganizations": []}

#     # Fetch parent sub-organization IDs and parent organization IDs
#     sub_org_response = []
#     for sub_org in sub_organizations:
#         # If `parent_sub_org_id` exists, fetch the parent's details
#         if sub_org.org_id:
#             parent_query = select(SubOrganisation).where(SubOrganisation.sub_org_id == sub_org.org_id)
#             parent_result = await db.execute(parent_query)
#             parent_sub_org = parent_result.scalar_one_or_none()
#             parent_id = parent_sub_org.sub_org_id if parent_sub_org else None
#         else:
#             parent_id = None

#         sub_org_response.append({
#             "sub_org_id": sub_org.sub_org_id,
#             "sub_org_name": sub_org.sub_org_name,
#             "org_id": sub_org.org_id,
#             "parent_sub_org_id": parent_id,
#             "email": sub_org.email,
#             "allocated_hits": sub_org.allocated_hits,
#             "remaining_hits": sub_org.available_hits,
#         })

#     return {"suborganizations": sub_org_response}


# BY SHIVAM
# @router.get("/users")
# async def get_users_by_suborg(
#     sub_org_id: Optional[UUID]=None,
#     current_user: list = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org"])),
#     db: AsyncSession = Depends(get_db)
# ):
#     user_info, user_role = current_user

#     if (user_role == 'superadmin' and sub_org_id is None) or (user_role == 'org' and sub_org_id is None):
#         users_result = await db.execute(
#         select(User).filter(User.sub_org_id == sub_org_id))
#         users = users_result.scalars().all()

#     return {"users":[
#         {
#             "user_id": user.user_id,
#             "username": user.username,
#             "name": user.name,
#             "email": user.email,
#             "allocated_hits": user.allocated_hits,
#             "remaining_hits": user.available_hits,
#             "is_active": user.is_active,
#         }
#         for user in users
#     ]}



#     if user_role == 'sub_org':
#         sub_org_id = getattr(user_info, 'sub_org_id', None)

#     # Fetch users for the specified suborganization
#     users_result = await db.execute(
#         select(User).filter(User.sub_org_id == sub_org_id)
#     )
#     users = users_result.scalars().all()

#     return {"users":[
#         {
#             "user_id": user.user_id,
#             "username": user.username,
#             "name": user.name,
#             "email": user.email,
#             "allocated_hits": user.allocated_hits,
#             "remaining_hits": user.available_hits,
#             "is_active": user.is_active,
#         }
#         for user in users
#     ]}
# BY SHIVAM

@router.get("/users")
async def get_users(
    sub_org_id: Optional[UUID] = None,
    current_user: list = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org"])),
    db: AsyncSession = Depends(get_db)
):
    user_info, user_role = current_user

    # Base query with joins for sub-organization and organization relationships
    query = select(
        User,
        SubOrganisation.sub_org_id.label("parent_sub_org_id"),
        Organisation.org_id.label("parent_org_id")
    ).outerjoin(
        SubOrganisation, User.sub_org_id == SubOrganisation.sub_org_id
    ).outerjoin(
        Organisation, SubOrganisation.org_id == Organisation.org_id
    )

    if sub_org_id:
        query = query.filter(User.sub_org_id == sub_org_id)
    elif user_role == "superadmin":
        pass
    elif user_role == "org":
        org_id = getattr(user_info, 'org_id', None)
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization details not found for the current user."
            )
        sub_orgs_result = await db.execute(
            select(SubOrganisation.sub_org_id).filter(SubOrganisation.org_id == org_id)
        )
        sub_org_ids = [sub_org.sub_org_id for sub_org in sub_orgs_result]
        query = query.filter(User.sub_org_id.in_(sub_org_ids))
    elif user_role == "sub_org":
        # SubOrg role sees only users under its own sub-organization
        sub_org_id = getattr(user_info, 'sub_org_id', None)
        if not sub_org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sub-organization details not found for the current user."
            )
        query = query.filter(User.sub_org_id == sub_org_id)

    # Execute the query
    users_result = await db.execute(query)
    results = users_result.fetchall()

    return {
        "users": [
            {
                "user_id": user.User.user_id,
                "username": user.User.username,
                "name": user.User.name,
                "email": user.User.email,
                "allocated_hits": user.User.allocated_hits,
                "remaining_hits": user.User.available_hits,
                "is_active": user.User.is_active,
                "parent_org_id": user.parent_org_id,
                "parent_sub_org_id": user.parent_sub_org_id,
            }
            for user in results
        ]
    }


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
        return await assign_tools_to_suborganisation(ID,tool_ids,db,current_user)
    elif role == "sub_org":
        return await assign_tools_to_user(ID,tool_ids,db,current_user)
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
 
 
@router.get("/gettoolbyid")
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
 
@router.get("/toolname")
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

@router.get("/available_hits_tokens")
async def get_available_hits_ortoken_for_user(
        type:str,
        db: AsyncSession = Depends(get_db),
        current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org", "user"]))
):
    user, role = current_user
    email = getattr(user, "email", None)
    if type == "api_hits":
        result = await fetch_available_hits(email, role, db)
    elif type =="ai_tokens":
        result = await fetch_remaining_ai_tokens(email, role, db)

        
    return {"message": result}

@router.get("/remaining_ai_tokens")
async def get_remaining_ai_tokens_for_user(
        db: AsyncSession = Depends(get_db),
        current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org"]))
):
    user, role = current_user
    email = getattr(user, "email", None)

    # Fetch remaining AI tokens based on role
    remaining_ai_tokens = await fetch_remaining_ai_tokens(email, role, db)

    # Return appropriate response
    if isinstance(remaining_ai_tokens, dict):  # Message for certain roles
        return remaining_ai_tokens

    return {"remaining_ai_tokens": remaining_ai_tokens}
