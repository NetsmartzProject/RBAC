from datetime import datetime , timedelta
from fastapi import Depends, status, HTTPException, Request
from jose import JWTError, jwt
from fastapi.security import HTTPAuthorizationCredentials, OAuth2PasswordBearer, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from database import model,database
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
from config.log_config import logger
import bcrypt


oauth2_scheme = HTTPBearer()


SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRES_MINUTES = settings.access_token_expire_minutes

def hash_password(password : str):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def check_duplicate_email(db: AsyncSession, email: str, username: str):
    try:
        admin_query = select(Admin).where(Admin.email == email)
        admin_result = await db.execute(admin_query)
        if admin_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already exists.")

        org_query = select(Organisation).where(Organisation.email == email)
        org_result = await db.execute(org_query)
        if org_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already exists.")

        suborg_query = select(SubOrganisation).where(SubOrganisation.email == email)
        suborg_result = await db.execute(suborg_query)
        if suborg_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already exists.")

        user_query = select(User).where(User.email == email)
        user_result = await db.execute(user_query)
        if user_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already exists.")
        
        admin_username_query = select(Admin).where(Admin.username == username)
        admin_username_result = await db.execute(admin_username_query)
        if admin_username_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already exists.")

        org_username_query = select(Organisation).where(Organisation.username == username)
        org_username_result = await db.execute(org_username_query)
        if org_username_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already exists.")

        suborg_username_query = select(SubOrganisation).where(SubOrganisation.username == username)
        suborg_username_result = await db.execute(suborg_username_query)
        if suborg_username_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already exists.")

        user_username_query = select(User).where(User.username == username)
        user_username_result = await db.execute(user_username_query)
        if user_username_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already exists.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking duplicate email or username: {str(e)}")

def get_current_user_with_roles(roles: List[Literal["superadmin", "user", "org", "sub_org"]]):
    async def _get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
        user = await get_current_user(token=token, roles=roles, db=db)
        return user
    return _get_current_user

async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    roles: List[Literal["superadmin", "user", "org", "sub_org"]] = None,
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        print(payload)
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Query each table for the user based on the role
    queries = [
        select(Admin).filter((Admin.email == email)),
        select(Organisation).filter(Organisation.email == email),
        select(SubOrganisation).filter(SubOrganisation.email == email),
        select(User).filter(User.email == email),
    ]

    user = None
    role = None

    for query, role_name in zip(queries, ["superadmin", "org", "sub_org", "user"]):
        result = await db.execute(query)
        user = result.scalars().first()
        if user:
            role = role_name
            break

    if not user:
        raise credentials_exception

    if roles is None or role in roles:
        return user, role

    raise HTTPException(status_code=403, detail="Access denied")


async def organization(org: OrganisationBase, current_user: tuple, db: AsyncSession) -> OrganisationResponse:
    try:
        hashed_password = oauth2.hash_password(org.org_password)
        print(current_user,"user from org")
        created_by_admin_id = getattr(current_user, "admin_id", None)
        available_hits=(org.allocated_hits - (org.allocated_hits * 0.10))
        print(org, created_by_admin_id, "this is the organozation from service",org.username)
        new_org = Organisation(
        email=org.org_email,
        password=hashed_password,
        org_name=org.org_name,
        username=org.username,
        allocated_hits=org.allocated_hits,
        available_hits=available_hits,
        created_by_admin = created_by_admin_id
        )
        print(new_org,"this is my new organization")
        

        
        db.add(new_org)
        await db.commit()
        await db.refresh(new_org)
        
        ten_percent_of_max_hit = org.allocated_hits * 0.10
        
        parent_sub_org = SubOrganisation(
            org_id=new_org.org_id,
            sub_org_name=f"sub_{new_org.org_name}",
            is_parent=True,
            email=f"sub_{new_org.email}",
            password=hashed_password,
            allocated_hits=ten_percent_of_max_hit,
            available_hits=ten_percent_of_max_hit,  
            username=f"sub_{org.username}",
        )
        
        db.add(parent_sub_org)
        await db.commit()
        await db.refresh(parent_sub_org)

        return OrganisationResponse(
            org_id=new_org.org_id,
            created_by_admin=new_org.created_by_admin,
            org_name=new_org.org_name,
            org_email=new_org.email,
            username=org.username,
            allocated_hits=org.allocated_hits
    )
    
    except Exception as e:
        print(e)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")



async def suborganization(suborg: SubOrganisationBase, current_user: tuple, db: AsyncSession):
    try:
        hashed_password = oauth2.hash_password(suborg.sub_org_password)
        org_query = select(Organisation).where(Organisation.org_id == getattr(current_user, "org_id", None))
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
            username=suborg.username,
            password=hashed_password,
            allocated_hits=suborg.allocated_hits,
            available_hits=suborg.allocated_hits,
            org_id=org.org_id,
            is_parent=False  
        )
        
        db.add(new_sub_org)
        await db.commit()
        await db.refresh(new_sub_org)
        
        print("This is from suborgnaisation",suborg)
        return SuborganisationResponse(
            sub_org_name=suborg.sub_org_name,
            sub_org_email=suborg.sub_org_email,
            username=suborg.username,
            allocated_hits=suborg.allocated_hits,
            created_by_org_id=new_sub_org.org_id
        )  

    except Exception as e:
        await db.rollback()
        print(f"Error creating suborganization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create suborganization: {str(e)}")



async def user(userbase: UserBase, current_user: tuple, db: AsyncSession):
    try:
        hashed_password = oauth2.hash_password(userbase.password)        
        sub_org_id = getattr(current_user, "sub_org_id", None)
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
            name=userbase.name,
            email=userbase.email,
            username=userbase.username,
            password=hashed_password,
            sub_org_id=sub_org_id,
            allocated_hits=userbase.allocated_hits,
            available_hits=userbase.allocated_hits,
            is_active=True,
            role="USER"
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        print(userbase.username,"hii")
        return UserResponse(
            name=userbase.name,
            user_name=userbase.username,
            email=userbase.email,
            allocated_hits=userbase.allocated_hits,
            created_by_admin=sub_org_id
        )  

    except Exception as e:
        await db.rollback()
        print(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


