from fastapi import APIRouter, Depends ,HTTPException,status
from Utills.oauth2 import get_current_user_with_roles
from config.log_config import logger
from database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select,update
from database.model import Admin,Organisation,SubOrganisation, User
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()


from fastapi import HTTPException, Depends

@router.get("/fetch-details")
async def fetch_details(
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org", "user"]))
):
    try:
        user_info, user_role = current_user
        print(user_info,"suborg")
        logger.info(f"User role: {user_role}")

        if user_role == "user":
            user_id = user_info[2]
            user_allocated_hit = user_info[1]
            username = user_info[3]
            user_email = user_info[6]  
            return {
                "user_id": user_id,
                "user_hit": user_allocated_hit,
                "username": username,
                "email": user_email 
            }
        elif user_role == "sub_org":
            sub_org_id = user_info[0]
            sub_org_name = user_info[5]
            sub_org_email = user_info[6]
            sub_allocated_hit=user_info[1]
            return {
                "sub_org_id": sub_org_id,
                "sub_org_name": sub_org_name,
                "email": sub_org_email,
                "Allocated-Hit":sub_allocated_hit
            }

        elif user_role == "org":
            org_id = user_info[0]
            org_name = user_info[5]
            org_hits = user_info[1]
            org_email = user_info[6]

            return {
                "org_id": org_id,
                "org_name": org_name,
                "available_hits": org_hits,
                "email": org_email
            }

        elif user_role == "superadmin":
            superadmin_id = user_info[0]
            superadmin_name = user_info[3]
            superadmin_email = user_info[7]
            superadmin_max_hits=user_info[1]

            return {
                "superadmin_id": superadmin_id,
                "superadmin_name": superadmin_name,
                "email": superadmin_email,
                "Max-hit":superadmin_max_hits
            }

        else:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized role"
            )

    except (IndexError, ValueError) as e:
        logger.error(f"Error extracting user information: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user details. Please check the user data format."
        )



@router.put("/editpersonalprofile")
async def edit_username(
    new_username: str,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org", "user"]))
):
    user_info, user_role = current_user
    user_email = user_info[6] 

    if user_role == "superadmin":
        model = Admin
        username_field = "admin_name"  
    elif user_role == "org":
        model = Organisation
        username_field = "org_name"  
    elif user_role == "sub_org":
        model = SubOrganisation
        username_field = "sub_org_name"  
    elif user_role == "user":
        model = User
        username_field = "username" 
    else:
        raise HTTPException(status_code=403, detail="Invalid role")

    existing_user = await db.execute(select(model).where(getattr(model, username_field) == new_username))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="This username has already been taken. Please choose another one.")

    result = await db.execute(select(model).where(model.email == user_email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    setattr(user, username_field, new_username)  
    await db.commit()
    await db.refresh(user)  

    return {
        "message": "Username updated successfully.",
        "updated_username": getattr(user, username_field)
    }



    
          
@router.get("/list-users")
async def list_users(
     db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org"]))
):
    try:
        user_role = current_user        
        if user_role == "user":
            raise HTTPException(
                status_code=403,
                detail="Access forbidden for role 'user'"
            )
        
        temp = await db.execute(select(User))
        users = temp.scalars().all()
        
        user_list = [{"user_id":user.user_id,"username": user.username, "email": user.email,"Allocated_hits": user.allocated_hits} for user in users]
        
        return user_list

    except HTTPException as e:
        raise e  
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving the user listing."
        )
    