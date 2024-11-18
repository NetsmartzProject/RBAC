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
from Schema.auth_schema import VerifyUser, UserLogin,OrganisationResponse, UserCommon, OrganisationBase,SubOrganisationBase,UserBase
from Utills.oauth2 import organization,suborganization,user,check_duplicate_email,get_current_user


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
    if user_db is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incoorect Username",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user or not verify_password(user.password, user_db.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect  password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"email": user.username,"Role":user_db.role},expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}



@router.get("/users/me")
async def read_users_me(
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org", "user"]))
):
    user_info, user_role = current_user
    user_id, max_hit, user_email, name, role = user_info

    return {
        "id": user_id,
        "name": name,
        "email": user_email,
        "role": user_role,
        "max_hit": max_hit
    }

@router.post("/signup")
async def create(
    user: UserCommon,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", 'org', 'sub_org']))
):
    user1, role = current_user
    await check_duplicate_email(db, user.email,user.username)
    if user1.role == 'superadmin':
        org = OrganisationBase(org_email=user.email, org_password=user.password, org_name=user.name, total_hits_limit=user.total_hits, parent_sub_org_name="" ,username=user.username)
        return await create_organization(org, db, current_user)
    
    elif user1.role == 'org' :
        org = SubOrganisationBase(
            sub_org_email=user.email,
            sub_org_password=user.password,
            sub_org_name=user.name,
            username=user.username,
            allocated_hits=user.total_hits,
            remaining_hits=user.total_hits,
            used_hits=user.total_hits
        )
        return await create_sub_organization(org, db, current_user)
    
    elif user1.role =='sub_org':
         org = UserBase(
            name=user.name,
            email=user.email,
            username=user.username,
            password=user.password,
            allocated_hits=user.total_hits    
         )
         return await create_user(org,db,current_user)
     
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. User cannot be created."
        )
 
async def create_organization(
    org: OrganisationBase,
    db: AsyncSession,
    current_user: tuple
):
    user, role = current_user
    print(user)
    result = await organization(org, user, db,parent_sub_org_name=org.parent_sub_org_name)
    return result

async def create_sub_organization(
    org:SubOrganisationBase,
    db:AsyncSession ,
    current_user:tuple
):
    user, role = current_user
    result = await suborganization(org,user,db)
    return result

async def create_user(
    org:UserBase,
    db:AsyncSession,
    current_user:tuple
):
    user1, role = current_user
    result = await user(org,user1,db)
    return result
    
@router.get("/subOrg")
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
            "created_at": sub_org.created_at.isoformat() if sub_org.created_at else None,
            "updated_at": sub_org.updated_at.isoformat() if sub_org.updated_at else None,
        }
        for sub_org in sub_organisations
    ]
    
    return sub_organisations_list
