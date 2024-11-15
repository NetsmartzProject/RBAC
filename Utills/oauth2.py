from datetime import datetime , timedelta
from fastapi import Depends, status, HTTPException, Request
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from database import model,database
from passlib.context import CryptContext
from uuid import UUID
from config.pydantic_config import settings
from database.database import get_db
from sqlalchemy import text, select,update
from sqlalchemy.orm import Session
from typing import Literal, List
from fastapi import Request, HTTPException
from Schema.auth_schema import OrganisationBase,OrganisationResponse,UserResponse,SubOrganisationBase,SuborganisationResponse,UserBase,CommonBase
from database.model import Organisation,SubOrganisation,User,Admin
from Utills import oauth2

oauth2_scheme = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"],deprecated = "auto")

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRES_MINUTES = settings.access_token_expire_minutes



def hash_password(password : str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password,hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def check_duplicate_email(db: AsyncSession, email: str):
    try:
        admin_query=select(Admin).where(Admin.email==email)
        admin_result=await db.execute(admin_query)
        if admin_result.scalar_one_or_none():
            raise HTTPException(status_code=400,detail="Email already Exists")
        
        org_query = select(Organisation).where(Organisation.email == email)
        org_result = await db.execute(org_query)
        if org_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already Exists .")
        
        suborg_query = select(SubOrganisation).where(SubOrganisation.email == email)
        suborg_result = await db.execute(suborg_query)
        if suborg_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already Exists.")
        
        user_query = select(User).where(User.email == email)
        user_result = await db.execute(user_query)
        if user_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already Exists.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking duplicate email: {str(e)}")


def get_current_user_with_roles(roles: List[Literal["superadmin", "user", "org", "sub_org"]]):
    async def _get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
        user = await get_current_user(token=token, roles=roles, db=db)
        return user
    return _get_current_user

async def get_current_user(
    token: str,
    roles: List[Literal["superadmin", "user", "org", "sub_org"]],
    db: AsyncSession 
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("email")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        text(
            """
        SELECT id, max_hits, user_id, username, password, name, email, role
FROM (
    SELECT admin_id as id, '' as user_id, max_hits as max_hits, admin_name AS username, password, admin_name AS name, email, 'superadmin' AS role
    FROM "SuperAdmin"
    WHERE admin_name = :username OR email = :username

    UNION

    SELECT org_id as id, '' as user_id, total_hits_limit as max_hits, NULL AS username, password, org_name AS name, email, 'org' AS role
    FROM "organisations"
    WHERE email = :username

    UNION

    SELECT sub_org_id as id, '' as user_id, allocated_hits as max_hits, NULL AS username, password, sub_org_name AS name, email, 'sub_org' AS role
    FROM "sub_organisations"
    WHERE email = :username

    UNION

    SELECT 0 as id, user_id, allocated_hits as max_hits, username, password, username AS name, email, 'user' AS role
    FROM "users"
    WHERE email = :username
) AS combined

            """
        ),
        {"username": username}
    )
    user = result.fetchone()

    if user is None:
        raise credentials_exception

    if not roles or user.role in roles:
        return (user, user.role)

    raise HTTPException(status_code=403, detail="Access denied")

async def organization(org: OrganisationBase, current_user: tuple, db: AsyncSession,parent_sub_org_name: str) -> OrganisationResponse:
    try:
        hashed_password = oauth2.hash_password(org.org_password)
        print(current_user,"user from org")
        created_by_admin_id = current_user.id
        
        total_hits_limit=current_user.max_hits
        available_hits=(org.total_hits_limit - (org.total_hits_limit * 0.10))
        print(org, created_by_admin_id, "this is the organozation from service")
        new_org = Organisation(
        email=org.org_email,
        password=hashed_password,
        org_name=org.org_name,
        total_hits_limit=org.total_hits_limit,
        available_hits=available_hits,
        created_by_admin = created_by_admin_id
        )
        print(new_org,"this is my new organization")
        

        
        db.add(new_org)
        await db.commit()
        await db.refresh(new_org)
        
        ten_percent_of_max_hit = org.total_hits_limit * 0.10
        
        parent_sub_org = SubOrganisation(
            org_id=new_org.org_id,
            sub_org_name=parent_sub_org_name,
            is_parent=True,
            email=f"{org.org_email.split('@')[0]}_sub@{org.org_email.split('@')[1]}",
            password=hashed_password,
            allocated_hits=ten_percent_of_max_hit,  
            remaining_hits=0,
            # remaining_hits=org.available_hits,
            used_hits=0
        )
        
        db.add(parent_sub_org)
        await db.commit()
        await db.refresh(parent_sub_org)


        
        return OrganisationResponse(
            org_id=new_org.org_id,
            created_by_admin=new_org.created_by_admin,
            org_name=new_org.org_name,
            org_email=new_org.email,
            total_hits_limit=org.total_hits_limit
    )
    
    except Exception as e:
        print(e)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")



async def suborganization(suborg: SubOrganisationBase, current_user: tuple, db: AsyncSession):
    try:
        hashed_password = oauth2.hash_password(suborg.sub_org_password)
        org_query = select(Organisation).where(Organisation.org_id == current_user.id)
        result = await db.execute(org_query)
        org = result.scalar_one_or_none()
        if not org:
            raise HTTPException(status_code=404, detail="Organisation not found.")
        
        if suborg.allocated_hits > org.available_hits:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Allocated hits cannot exceed the organisation's available hits."
            )

        org.available_hits -= suborg.allocated_hits
        await db.commit()  

        new_sub_org = SubOrganisation(
            sub_org_name=suborg.sub_org_name,
            email=suborg.sub_org_email,
            password=hashed_password,
            allocated_hits=suborg.allocated_hits,
            remaining_hits=suborg.allocated_hits,
            used_hits=suborg.used_hits,
            org_id=current_user.id,
            is_parent=False  
        )
        
        db.add(new_sub_org)
        await db.commit()
        await db.refresh(new_sub_org)
        
        return SuborganisationResponse(
            sub_org_name=suborg.sub_org_name,
            sub_org_email=suborg.sub_org_email,
            allocated_hits=suborg.allocated_hits,
            created_by_org_id=new_sub_org.sub_org_id
        )  

    except Exception as e:
        await db.rollback()
        print(f"Error creating suborganization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create suborganization: {str(e)}")



async def user(userbase: UserBase, current_user: tuple, db: AsyncSession):
    try:
        hashed_password = oauth2.hash_password(userbase.password)        
        sub_org_id = current_user.id
        print(sub_org_id,"suborgid")
        org_query = select(SubOrganisation).where(SubOrganisation.sub_org_id == sub_org_id)
        org_result = await db.execute(org_query)
        current_sub_org = org_result.scalar_one_or_none()

        if not current_sub_org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SubOrganisation not found."
            )

        if userbase.allocated_hits > current_sub_org.allocated_hits:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Allocated hits for user cannot exceed the available hits of the SubOrganisation."
            )

        current_sub_org.allocated_hits -= userbase.allocated_hits
        await db.commit()  
        new_user = User(
            username=userbase.username,
            email=userbase.email,
            password=hashed_password,
            sub_org_id=sub_org_id,
            allocated_hits=userbase.allocated_hits,
            is_active=True,
            role="USER"
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return UserResponse(
            name=userbase.username,
            email=userbase.email,
            allocated_hits=userbase.allocated_hits,
        )  

    except Exception as e:
        await db.rollback()
        print(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
