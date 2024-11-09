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


@router.get("/fetch-details")
async def fetch_details(
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org", "user"]))
):
    try:
        print(current_user, "currentuser")
        
        user_info, user_role = current_user
        print(user_info, user_role, "userinfo")
        
        user_id = user_info[0]
        user_hit = user_info[1]
        username = user_info[3]
        user_email = user_info[6]  
        
        logger.info(f"User email: {user_email}, Role: {user_role}")
        
        return {
            "user_id": user_id,
            "user_hit": user_hit,
            "username": username,
            "email": user_email 
        }
    
    except (IndexError, ValueError) as e:
        logger.error(f"Error extracting user information: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user details. Please check the user data format."
        )


# @router.put("/edit-username")
# async def edit_username(
#     new_username: str,
#     db: AsyncSession = Depends(get_db),
#     current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org", "user"]))
# ):
#     user_info, user_role = current_user
#     user_email = user_info[6]  # Assuming email is at index 6 in user_info

#     # Determine the model based on the user's role
#     if user_role == "superadmin":
#         model = Admin
#     elif user_role == "org":
#         model = Organisation
#     elif user_role == "sub_org":
#         model = SubOrganisation
#     elif user_role == "user":
#         model = User
#     else:
#         raise HTTPException(status_code=403, detail="Invalid role")

#     # Check if the new username is already taken
#     existing_user = await db.execute(select(model).where(model.admin_name == new_username))
#     print(existing_user,'current')
#     if existing_user.scalar_one_or_none():
#         raise HTTPException(status_code=400, detail="This username has already been taken. Please choose another one.")

#     result = await db.execute(select(model).where(model.email == user_email))
#     user = result.scalar_one_or_none()

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found.")

#     user.username = new_username
#     await db.commit()

#     return {
#         "message": "Username updated successfully.",
#         "updated_username": user.username
#     }

# @router.put("/edit-username")
# async def edit_username(
#     new_username: str,
#     db: AsyncSession = Depends(get_db),
#     current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org", "user"]))
# ):
#     user_info, user_role = current_user
#     user_email = user_info[6]  # Assuming email is at index 6 in user_info
#     username = user_info[3]
#     print(user_email,"user_email")

#     # Step 1: Determine the model based on user role
#     if user_role == "superadmin":
#         model = Admin
#     elif user_role == "org":
#         model = Organisation
#     elif user_role == "sub_org":
#         model = SubOrganisation
#     elif user_role == "user":
#         model = User
#     else:
#         raise HTTPException(status_code=403, detail="Invalid role")

#     # Step 2: Check if new username is already taken in the respective table
#     if user_role == "superadmin":
#         existing_user = await db.execute(select(model).where(model.admin_name == new_username))
#     if existing_user.scalar_one_or_none():
#         raise HTTPException(status_code=400, detail="This username has already been taken. Please choose another one.")
#     elif user_role =="org":
#         org_user = await db.execute(select(model).where(model.sub_org_name == new_username))
#         if org_user.scalar_one_or_none():
#             raise HTTPException(status_code=400,detail="The username has already taken")
#     elif user_role =="sub_org":
#         sub_org_user = await db.execute(select(model).where(model.org_name==new_username))
#         if sub_org_user.scalar_one_or_none():
#             raise HTTPException(status_code=400,detail="The username has already taken")
        
#     # Step 3: Retrieve the current user by email in the appropriate table
#     result = await db.execute(select(model).where(model.email == user_email))
#     print(result,"result")
#     user = result.scalar_one_or_none()
#     print(user,"userss")

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found.")

#     # Step 4: Update the username
#     user.admin_name = new_username
#     await db.commit()

#     # Step 5: Return success message
#     return {
#         "message": "Username updated successfully.",
#         "updated_username": user.admin_name
#     }



@router.put("/edit-username")
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



    
              