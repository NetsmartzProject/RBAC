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
from Utills.tool import add_tool,assign_tools_to_organisation,assign_tools_to_suborganisation,assign_tools_to_user
from Schema.tool_schema import Tool,ToolResponse
from datetime import datetime


router = APIRouter()


# @router.get("/listingUser")
# async def getSubOrganizations(
#     current_user: list = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org", "user"])),
#     db: AsyncSession = Depends(get_db)
# ):
#     user_info, user_role = current_user
#     print(user_info,"userinf")
#     if user_role != 'org':
#         return {"message": "No Access"} 

#     result = await db.execute(select(SubOrganisation).filter(SubOrganisation.org_id == user_info[0]))

#     sub_organisations = result.scalars().all()

#     sub_organisations_list = [
#         {
#             "sub_org_id": sub_org.sub_org_id,
#             "org_id": sub_org.org_id,
#             "username": sub_org.username,
#             "sub_org_name": sub_org.sub_org_name,
#             "is_parent": sub_org.is_parent,
#             "email": sub_org.email,
#             "allocated_hits": sub_org.allocated_hits,
#             "remaining_hits": sub_org.remaining_hits,
#             "used_hits": sub_org.used_hits,
#             "tool_ids":sub_org.tool_ids,
#             "tool_grant_dates":sub_org.tool_grant_dates,
#             "created_at": sub_org.created_at.isoformat() if sub_org.created_at else None,
#             "updated_at": sub_org.updated_at.isoformat() if sub_org.updated_at else None,
#         }
#         for sub_org in sub_organisations
#     ]
    
#     return sub_organisations_list

@router.get("/listingUser")
async def get_hierarchical_listing(
    current_user: list = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org", "user"])),
    db: AsyncSession = Depends(get_db)
):
    user_info, user_role = current_user
    
    print(user_role,"user_role")
    if user_role == 'org':
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
                "tool_ids": sub_org.tool_ids,
                "tool_grant_dates": sub_org.tool_grant_dates,
                "created_at": sub_org.created_at.isoformat() if sub_org.created_at else None,
                "updated_at": sub_org.updated_at.isoformat() if sub_org.updated_at else None,
            }
            for sub_org in sub_organisations
        ]
        return sub_organisations_list

    elif user_role == 'sub_org':
        result = await db.execute(select(User).filter(User.sub_org_id == user_info[0]))
        users = result.scalars().all()
        # print(users.remaninig_hits)

        users_list = [
            {
                "user_id": user.user_id,
                "sub_org_id": user.sub_org_id,
                "username": user.username,
                "name":user.name,
                "email": user.email,
                "remaninig_hits":user.remaninig_hits,
                "allocated_hits": user.allocated_hits,
                "tool_ids": user.tool_ids,
                "is_active":user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            }
            for user in users
        ]
        return users_list

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to view hierarchy"
        )



@router.post("/tool")
async def creat_tool(
    tool: Tool,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin"]))
    ):
    user, role = current_user
    result = await add_tool(tool, user, db)
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



# BY SHIVAM 


# from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status, Response
# from sqlalchemy.ext.asyncio import AsyncSession
# from database.model import Admin,Organisation,SubOrganisation,User, Role
# from Utills.oauth2 import create_access_token,get_current_user_with_roles,verify_password
# from database.database import get_db
# from datetime import timedelta
# from pydantic import BaseModel
# from typing import Any, List, Union
# from sqlalchemy import text, select
# from sqlalchemy.orm import Session
# from config.pydantic_config import settings
# # from Utills.tool import add_tool, add_tools_to_organisation,assign_tools_to_suborganisation,assign_tools_to_user, delete_tool, fetch_all_tools
# from Schema.tool_schema import AddToolResponse, Tool,ToolResponse
# from datetime import datetime
# from Utills.tool import add_tool ,delete_tool,update_tool,add_tools_to_organisation,add_tools_to_suborganisation,add_tools_to_user
 
# router = APIRouter()
 
# @router.get("/subOrgss")
# async def getSubOrganizations(
#     current_user: list = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org", "user"])),
#     db: AsyncSession = Depends(get_db)
# ):
#     user_info, user_role = current_user
#     print(user_info,"userinf")
#     if user_role != 'org':
#         return {"message": "No Access"}
 
#     result = await db.execute(select(SubOrganisation).filter(SubOrganisation.org_id == user_info[0]))
 
#     sub_organisations = result.scalars().all()
 
#     sub_organisations_list = [
#         {
#             "sub_org_id": sub_org.sub_org_id,
#             "org_id": sub_org.org_id,
#             "username": sub_org.username,
#             "sub_org_name": sub_org.sub_org_name,
#             "is_parent": sub_org.is_parent,
#             "email": sub_org.email,
#             "allocated_hits": sub_org.allocated_hits,
#             "remaining_hits": sub_org.remaining_hits,
#             "used_hits": sub_org.used_hits,
#             "tool_ids":sub_org.tool_ids,
#             "tool_grant_dates":sub_org.tool_grant_dates,
#             "created_at": sub_org.created_at.isoformat() if sub_org.created_at else None,
#             "updated_at": sub_org.updated_at.isoformat() if sub_org.updated_at else None,
#         }
#         for sub_org in sub_organisations
#     ]
   
#     return sub_organisations_list
 
# @router.post("/tool")
# async def create_tool(
#     tool: Tool,
#     db: AsyncSession = Depends(get_db),
#     current_user: tuple = Depends(get_current_user_with_roles(["superadmin"]))
# ) -> Any:
#     """
#     Create a new tool. Only accessible to superadmin users.
#     """
#     try:
#         user, role = current_user
#         result = await add_tool(tool, user, db)
#         return result
#     except Exception as e:
#         print(f"Unexpected error in create_tool: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error.")
 
 
# @router.delete("/tool/{tool_id}")
# async def remove_tool(
#     tool_id: int = Path(..., description="The ID of the tool to be deleted."),
#     db: AsyncSession = Depends(get_db),
#     current_user: tuple = Depends(get_current_user_with_roles(["superadmin"]))
# ) -> Any:
#     """
#     Delete a tool (soft delete) by its ID. Only accessible to superadmin users.
#     """
#     try:
#         user, role = current_user
#         result = await delete_tool(tool_id, db)
#         if not result:
#             raise HTTPException(status_code=404, detail="Tool not found.")
#         return {"message": "Tool successfully deleted.", "tool_id": tool_id}
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         print(f"Unexpected error in remove_tool: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error.")
 
 
# @router.get("/tool")
# async def get_tool_by_id(
#     tool_id: int = Query(..., description="The ID of the tool to be retrieved."),
#     db: AsyncSession = Depends(get_db),
#     current_user: tuple = Depends(get_current_user_with_roles(["superadmin"]))
# ) -> Any:
#     """
#     Retrieve a tool by its ID. Only accessible to superadmin users.
#     """
#     try:
#         user, role = current_user
#         result = await fetch_tool_by_id(tool_id, db)
#         if not result:
#             raise HTTPException(status_code=404, detail="Tool not found.")
#         return result
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         print(f"Unexpected error in get_tool_by_id: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error.")
 
 
# @router.get("/tool/all")
# async def get_all_tools(
#     db: AsyncSession = Depends(get_db),
#     current_user: tuple = Depends(get_current_user_with_roles(["superadmin"]))
# ) -> Any:
#     """
#     Retrieve all tools. Only accessible to superadmin users.
#     """
#     try:
#         user, role = current_user
#         result = await fetch_all_tools(db)
#         return result
#     except Exception as e:
#         print(f"Unexpected error in get_all_tools: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error.")
 
# # @router.post("/assign_tool_to_user")
# # async def assign_tool_to_user(
# #     ID: int,
# #     tool_ids: list[int],
# #     db: AsyncSession = Depends(get_db),
# #     current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "user", "org", "sub_org"]))
# # ):
# #     user, role = current_user
   
# #     if role == "superadmin":
# #         return await assign_tools_to_organisation(ID, tool_ids, db)
   
# #     elif role == "org":
# #         return await assign_tools_to_suborganisation(ID,tool_ids,db)
   
# #     elif role == "sub_org":
# #         return await assign_tools_to_user(ID,tool_ids,db)
   
# #     else:
# #         raise HTTPException(status_code=403, detail="Unauthorized access")
 
 
# # @router.post("/organisation/{organisation_id}/tools")
# # async def grant_tools_to_organisation(
# #     organisation_id: int = Path(..., description="The ID of the organisation."),
# #     tool_ids: List[int] = Body(..., description="A list of tool IDs to be granted."),
# #     db: AsyncSession = Depends(get_db),
# #     current_user: tuple = Depends(get_current_user_with_roles(["superadmin"]))
# # ) -> AddToolResponse:
# #     """
# #     Grant multiple tools to an organization. Accessible only by superadmin.
# #     """
# #     try:
# #         user, role = current_user
# #         result = await add_tools_to_organisation(organisation_id, tool_ids, db)
# #         return result
# #     except HTTPException as e:
# #         raise e
# #     except Exception as e:
# #         print(f"Unexpected error in grant_tools_to_organisation: {e}")
# #         raise HTTPException(status_code=500, detail="Internal server error.")
 
# @router.post("/assign-tools/{entity_id}")
# async def assign_tools(
#     entity_id: int = Path(..., description="The ID of the entity (organisation, suborganisation, or user)."),
#     tool_ids: List[int] = Body(..., description="A list of tool IDs to be assigned."),
#     db: AsyncSession = Depends(get_db),
#     current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org"]))
# ) -> Any:
#     """
#     Assign tools based on the role of the user:
#     - Superadmin: Assign tools to an organisation.
#     - Organisation: Assign tools to a suborganisation.
#     - Suborganisation: Assign tools to a user.
#     """
#     try:
#         user, role = current_user
 
#         if role == "superadmin":
#             result = await add_tools_to_organisation(entity_id, tool_ids, db)
#         elif role == "org":
#             result = await add_tools_to_suborganisation(entity_id, tool_ids, db)
#         elif role == "sub_org":
#             result = await add_tools_to_user(entity_id, tool_ids, db)
#         else:
#             raise HTTPException(
#                 status_code=403,
#                 detail="User role does not have permission to assign tools."
#             )
 
#         return result
 
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         print(f"Unexpected error in assign_tools: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error.")