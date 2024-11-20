from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from database.model import Admin,Organisation,SubOrganisation, ToolMaster,User, Role
from Utills.oauth2 import create_access_token,get_current_user_with_roles,verify_password
from database.database import get_db
from datetime import timedelta
from pydantic import BaseModel
from typing import Any, Union
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from config.pydantic_config import settings
from Schema.auth_schema import VerifyUser, UserLogin,OrganisationResponse, UserCommon, OrganisationBase,SubOrganisationBase,UserBase
from Utills.oauth2 import organization,suborganization,user,check_duplicate_email,get_current_user


router = APIRouter()

@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    # Query for superadmin (Admin)
    result = await db.execute(
        select(Admin).filter(
            (Admin.email == user.email)
        )
    )
    superadmin = result.scalars().first()
    if superadmin:
        db_user = superadmin
        role = 'superadmin'
    else:
        # Query for organization if no superadmin found
        result = await db.execute(
            select(Organisation).filter(Organisation.email == user.email)
        )
        organisation = result.scalars().first()
        if organisation:
            db_user = organisation
            role = 'org'
        else:
            # Query for sub-organization if no organization found
            result = await db.execute(
                select(SubOrganisation).filter(SubOrganisation.email == user.email)
            )
            suborg = result.scalars().first()
            if suborg:
                db_user = suborg
                role = 'sub_org'
            else:
                # Query for user if no sub-organization found
                result = await db.execute(
                    select(User).filter(User.email == user.email)
                )
                user_db = result.scalars().first()
                if user_db:
                    db_user = user_db
                    role = 'user'
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Incorrect username or password",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

    # Validate `tool_id` for roles other than superadmin
    if role != 'superadmin':
        if user.tool_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tool ID is required for non-superadmin roles",
            )

        # Check if the tool is active in the ToolMaster table
        tool_query = await db.execute(
            select(ToolMaster.is_active).filter(ToolMaster.tool_id == user.tool_id)
        )
        tool_status = tool_query.scalar()

        if tool_status is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool ID not found in ToolMaster",
            )
        if not tool_status:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tool is not active",
            )
        
        if user.tool_id not in db_user.tool_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid or inactive tool_id for this organization",
                )

    # Check the password
    if not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please Enter Correct Password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"email": user.email, "role": role},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "user_role": role}


@router.get("/users/me")
async def read_users_me(
    current_user: tuple = Depends(get_current_user),
):
    user, role = current_user  # Unpack the tuple returned by `get_current_user`
    if user is not None:
        # Access user attributes dynamically based on the role
        user_email: Any = getattr(user, "email", None)
        # name: Any = getattr(user, "username", None) or getattr(user, "admin_name", None)
        max_hit: Any = getattr(user, "allocated_hits", None)

        if role == "superadmin":
            user_id: Any = getattr(user, "admin_id", None)
            name: Any = getattr(user, "admin_name", None)
        elif role == "org":
            user_id: Any = getattr(user, "org_id", None)
            name:Any = getattr(user, "org_name", None) 
        elif role == "sub_org":
            user_id: Any = getattr(user, "sub_org_id", None)
            name:Any = getattr(user, "sub_org_name", None) 
        elif role == "user":
            user_id: Any = getattr(user, "user_id", None)
            name:Any = getattr(user, "name", None) 
        else:
            raise HTTPException(detail="Access Denied!", status_code=403)
    else:
        raise HTTPException(detail="User not Found", status_code=404)   
    

    return {
        "user_id": user_id,
        "email": user_email,
        "name": name,
        "max_hit": max_hit,
        "role": role,
    }

@router.post("/signup")
async def create(
    user: UserCommon,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", 'org', 'sub_org']))
):
    user1, role = current_user
    await check_duplicate_email(db, user.email,user.username)
    if role == 'superadmin':
        org = OrganisationBase(
            org_email=user.email, 
            org_password=user.password, 
            org_name=user.name, 
            allocated_hits= user.total_hits, 
            username=user.username)
        return await create_organization(org, db, current_user)
    
    elif role == 'org' :
        org = SubOrganisationBase(
            sub_org_email=user.email,
            sub_org_password=user.password,
            sub_org_name=user.name,
            username=user.username,
            allocated_hits=user.total_hits,
        )
        return await create_sub_organization(org, db, current_user)
    
    elif role =='sub_org':
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
    result = await organization(org, user, db)
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