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
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from typing import Literal, List
from fastapi import Request, HTTPException
from Schema.auth_schema import OrganisationBase,OrganisationResponse,SubOrganisationBase,UserBase,CommonBase
from database.model import Organisation,SubOrganisation,User
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

# WORKING FINE
# def get_current_user_with_roles(roles: List[Literal["superadmin", "user", "org", "sub_org"]]):
#     async def _get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#         return await get_current_user(token=token, roles=roles, db=db)
#     print(_get_current_user,"this is the current user",roles)
#     return _get_current_user

# async def get_current_user(
#     token: str,
#     roles: List[Literal["superadmin", "user", "org", "sub_org"]],
#     db: Session 
# ):
#     temp = token.credentials
#     print(temp, "this is the token")

#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("email")
#         if username is None:
#             raise credentials_exception
#         token_data = username
#     except JWTError:
#         raise credentials_exception

#     users = await db.execute(
#         text(
#             """
#             SELECT id, max_hit, user_id, name as username,  role FROM (
#                 SELECT admin_id as id, '' as user_id, admin_name AS name, email as email, max_hits as max_hit, 'superadmin' AS role
#                 FROM "SuperAdmin"
#                 WHERE admin_name = :username OR email = :username

#                 UNION ALL

#                 SELECT org_id as id, '' as user_id, org_name as name, email as email, total_hits_limit as max_hit ,  'org' AS role
#                 FROM "organisations"
#                 WHERE email = :username
                
#                 UNION ALL 
                
#                 SELECT sub_org_id as id, '' as user_id, sub_org_name as name, email as email,allocated_hits as max_hit, 'sub_org' AS role 
#                 FROM "sub_organisations"
#                 WHERE email = :username
                
#                 UNION ALL 
                
#                 SELECT 0 as id, user_id, username as name,  email as email, 0 as max_hit, 'user' AS role 
#                 FROM "users"
#                 WHERE email = :username
#             ) AS combined
#             """
#         ),
#         {"username": username}
#     )
#     user = users.fetchone()
    
#     if user is None:
#         raise credentials_exception

#     if not roles or len(roles) == 0 or user.role in roles:
#         return user

#     raise HTTPException(status_code=403, detail="Access denied")
# WORKING FINE



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

    # Query the database to get user information
    result = await db.execute(
        text(
            """
            SELECT id, max_hit, user_id, name AS username, role FROM (
                SELECT admin_id AS id, '' AS user_id, admin_name AS name, email AS email, max_hits AS max_hit, 'superadmin' AS role
                FROM "SuperAdmin"
                WHERE admin_name = :username OR email = :username

                UNION ALL

                SELECT org_id AS id, '' AS user_id, org_name AS name, email AS email, total_hits_limit AS max_hit, 'org' AS role
                FROM "organisations"
                WHERE email = :username

                UNION ALL

                SELECT sub_org_id AS id, '' AS user_id, sub_org_name AS name, email AS email, allocated_hits AS max_hit, 'sub_org' AS role
                FROM "sub_organisations"
                WHERE email = :username

                UNION ALL

                SELECT 0 AS id, user_id, username AS name, email AS email, 0 AS max_hit, 'user' AS role
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

    # Check if user's role matches any of the required roles
    if not roles or user.role in roles:
        # Return user and their roles
        return (user, user.role)

    raise HTTPException(status_code=403, detail="Access denied")

async def organization(org: OrganisationBase, current_user: tuple, db: AsyncSession,parent_sub_org_name: str) -> OrganisationResponse:
    try:
        hashed_password = oauth2.hash_password(org.org_password)
        created_by_admin_id = current_user.id
        total_hits_limit=current_user.max_hit
        available_hits=total_hits_limit-(total_hits_limit)*0.10
        
        new_org = Organisation(
            org_name=org.org_name,
            email=org.org_email,
            password=hashed_password,
            total_hits_limit=total_hits_limit,
            available_hits=available_hits,
            created_by_admin=created_by_admin_id 
            )
        
        db.add(new_org)
        await db.commit()
        await db.refresh(new_org)
        
        ten_percent_of_max_hit = current_user.max_hit * 0.10
        
        parent_sub_org = SubOrganisation(
            org_id=new_org.org_id,
            sub_org_name=parent_sub_org_name,
            is_parent=True,
            email=org.org_email,
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
            org_email=new_org.email
    )
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")


async def suborganization(suborg:SubOrganisationBase,current_user:tuple,db:AsyncSession):
    try:
        hashed_password=oauth2.hash_password(suborg.sub_org_password)
        query = select(SubOrganisation.allocated_hits).where(SubOrganisation.org_id == current_user.id)
        result = await db.execute(query)
        total_allocated_hits = sum(row[0] for row in result.fetchall())
        available_hits = current_user.max_hit - total_allocated_hits
        created_by_org_id = current_user.id   
         
        print(suborg.allocated_hits,"suborg",available_hits) 
        if suborg.allocated_hits > available_hits:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Allocated hits cannot exceed the available hits "
            )
        
        new_sub_org = SubOrganisation (
            sub_org_name=suborg.sub_org_name,
            email=suborg.sub_org_email,
            password=hashed_password,
            allocated_hits=suborg.allocated_hits,
            remaining_hits=available_hits,
            used_hits=suborg.used_hits,
            org_id=created_by_org_id             
            )
        
        db.add(new_sub_org)
        await db.commit()
        await db.refresh(new_sub_org)
        
        
    except Exception as e:
        await db.rollback()
        print(f"Error creating organization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")


# async def user(userbase:UserBase,current_user:tuple,db:AsyncSession):
    try:
        hashed_password=oauth2.hash_password(userbase.password)        
        sub_org_id = current_user.id 
        new_user= User(
            username=userbase.username,
            email=userbase.email,
            password=hashed_password,
            sub_org_id=sub_org_id,
            is_active=True,
            role="USER"
            )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)   
                 
    except Exception as e:
        await db.rollback()
        print(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


async def user(userbase: UserBase, current_user: tuple, db: AsyncSession):
    try:
        hashed_password = oauth2.hash_password(userbase.password)        
        sub_org_id = current_user.id

        # Step 1: Check if the current organization is a parent
        org_query = select(SubOrganisation).where(SubOrganisation.id == sub_org_id)
        org_result = await db.execute(org_query)
        current_org = org_result.scalar_one_or_none()

        if not current_org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found."
            )

        # Step 2: Calculate available hits based on whether the org is a parent or not
        if current_org.is_parent:
            # If parent, calculate based on total allocated hits
            allocated_hits_query = select(User.allocated_hits).where(User.sub_org_id == sub_org_id)
            result = await db.execute(allocated_hits_query)
            total_allocated_hits = sum(row[0] for row in result.fetchall())
            print(available_hits,"parent_suborg_hit",current_org.allocated_hits)
            available_hits = current_org.allocated_hits - total_allocated_hits
        else:
            # If not parent, only allow allocation within its own allocated hits
            available_hits = current_org.allocated_hits

        # Step 3: Validate if the requested hits exceed available hits
        if userbase.allocated_hits > available_hits:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Allocated hits for the user cannot exceed the available hits of the organization."
            )

        # Step 4: Proceed with user creation if within limit
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

    except Exception as e:
        await db.rollback()
        print(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
