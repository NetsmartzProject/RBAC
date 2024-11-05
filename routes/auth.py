from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from database.model import Admin,Organisation,SubOrganisation,User
from Utills.oauth2 import create_access_token,get_current_user_with_roles,verify_password
from database.database import get_db
from datetime import timedelta
from pydantic import BaseModel
from typing import Union
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from config.pydantic_config import settings
from Schema.auth_schema import UserLogin,OrganisationResponse,OrganisationBase,SubOrganisationBase,UserBase
from Utills.oauth2 import organization,suborganization,user


router = APIRouter()



@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    db_user =await db.execute(
                text(
        """
        SELECT username AS username, password AS password, name, email, role FROM (
            SELECT admin_name AS username, password, admin_name AS name, email, 'superadmin' AS role
            FROM "SuperAdmin"
            WHERE admin_name = :username OR email = :username

            UNION 

            SELECT NULL AS username, password, org_name AS name, email, 'org' AS role
            FROM "organisations"
            WHERE email = :username
            
            UNION  
            
            SELECT NULL AS username, password, sub_org_name AS name, email, 'sub_org' AS role
            FROM "sub_organisations"
            WHERE email = :username
            
            UNION  
            
            SELECT username, password, username AS name, email, 'user' AS role
            FROM "users"
            WHERE email = :username
            
        ) AS combined
        """
    ),
    {"username": user.username}
)

    user_db = db_user.fetchone()
    print(user,"user")
    if not user or not verify_password(user.password, user_db.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"email": user.username,"Role":user_db.role},expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me")
async def read_users_me(current_user: tuple = Depends(get_current_user_with_roles(["superadmin","org","sub_org","user"]))):
    try:
        
        print(current_user,"current user")
        
        result = {
            "id" :  current_user[0],
            "name" :  current_user[3],
            "user_id" :  current_user[2],
            "Role" :  current_user[4],
        }
        return result
    except Exception as e:
        print("Error occurred:", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")


# @router.post("/create_organization", response_model=OrganisationResponse)
# async def create_organization(
#     org: OrganisationBase,
#     db: AsyncSession = Depends(get_db),
#     current_user: tuple = Depends(get_current_user_with_roles(["superadmin"]))
# ):
#     result = await organization(org, current_user, db,parent_sub_org_name=org.parent_sub_org_name)
#     return result



@router.post("/create_organization", response_model=OrganisationResponse)
async def create_organization(
    org: OrganisationBase,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin"]))
):
    user, role = current_user
    result = await organization(org, user, db,parent_sub_org_name=org.parent_sub_org_name)
    return result


@router.post("/create suborganization")
async def create_sub_organization(
    org:SubOrganisationBase,
    db:AsyncSession =Depends(get_db),
    current_user:tuple =Depends(get_current_user_with_roles(["org"]))
):
    result = await suborganization(org,current_user,db)
    return result


@router.post("/create_user")
async def create_user(
    org:UserBase,
    db:AsyncSession =Depends(get_db),
    current_user:tuple =Depends(get_current_user_with_roles(["sub_org"]))
):
    result = await user(org,current_user,db)
    return result

# @router.post("/signup", response_model=OrganisationResponse)
# async def create_entity(
#     entity_type: str,  # Accepts "organization", "sub_organization", or "user"
#     org: Union[OrganisationBase, SubOrganisationBase, UserBase],  # Union allows different schemas based on entity type
#     db: AsyncSession = Depends(get_db),
#     current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org"]))
# ):
#     """
#     Unified API for creating an organization, sub-organization, or user based on entity_type.
#     """
#     print(entity_type,"entity")
#     # Verify user roles based on entity type
#     if entity_type == "organization":
#         # Check if the user has the "superadmin" role for creating an organization
#         if "superadmin" not in current_user[1]:
#             raise HTTPException(status_code=403, detail="Not authorized to create organization")
#         result = await organization(org, current_user, db, parent_sub_org_name=org.parent_sub_org_name)

#     elif entity_type == "sub_organization":
#         # Check if the user has the "org" role for creating a sub-organization
#         if "org" not in current_user[1]:
#             raise HTTPException(status_code=403, detail="Not authorized to create sub-organization")
#         result = await suborganization(org, current_user, db)

#     elif entity_type == "user":
#         # Check if the user has the "sub_org" role for creating a user
#         if "sub_org" not in current_user[1]:
#             raise HTTPException(status_code=403, detail="Not authorized to create user")
#         result = await user(org, current_user, db)

#     else:
#         raise HTTPException(status_code=400, detail="Invalid entity type")

#     return result


# @router.post("/signup", response_model=OrganisationResponse)
# async def create_entity(
#     entity_type: str,  # Accepts "organization", "sub_organization", or "user"
#     org: Union[OrganisationBase, SubOrganisationBase, UserBase],  # Union allows different schemas based on entity type
#     db: AsyncSession = Depends(get_db),
#     current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org"]))
# ):
#     """
#     Unified API for creating an organization, sub-organization, or user based on entity_type.
#     """
#     user, role = current_user  # Unpack the tuple to access the user object directly
#     print(entity_type, "entity")
    
#     # Verify user roles based on entity type
#     if entity_type == "organization":
#         # Check if the user has the "superadmin" role for creating an organization
#         if "superadmin" not in role:
#             raise HTTPException(status_code=403, detail="Not authorized to create organization")
#         result = await organization(org, user, db, parent_sub_org_name=org.parent_sub_org_name)

#     elif entity_type == "sub_organization":
#         # Check if the user has the "org" role for creating a sub-organization
#         if "org" not in role:
#             raise HTTPException(status_code=403, detail="Not authorized to create sub-organization")
#         result = await suborganization(org, user, db)

#     elif entity_type == "user":
#         # Check if the user has the "sub_org" role for creating a user
#         if "sub_org" not in role:
#             raise HTTPException(status_code=403, detail="Not authorized to create user")
#         result = await user(org, user, db)

#     else:
#         raise HTTPException(status_code=400, detail="Invalid entity type")

#     return result


@router.post("/signup", response_model=OrganisationResponse)
async def create_entity(
    org: Union[OrganisationBase, SubOrganisationBase, UserBase],  # The org input remains
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org"]))
):
    user, roles = current_user  # Unpack the tuple to access the user object directly
    entity_type = None  # Initialize entity_type
    
    # Determine entity_type based on user roles
    if "superadmin" in roles:
        entity_type = "organization"
    elif "org" in roles:
        entity_type = "sub_organization"
    elif "sub_org" in roles:
        entity_type = "user"
    else:
        raise HTTPException(status_code=403, detail="Not authorized to create any entity")

    print(f"Entity type determined: {entity_type}")

    # Now, proceed with the creation based on the determined entity_type
    if entity_type == "organization":
        print(entity_type,"organization entity_type")
        result = await organization(org, user, db, parent_sub_org_name=org.parent_sub_org_name)
    elif entity_type == "sub_organization":
        result = await suborganization(org, user, db)
    elif entity_type == "user":
        result = await user(org, user, db)
    
    return result
