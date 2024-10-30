from datetime import datetime , timedelta
from fastapi import Depends, status, HTTPException, Request
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from database import model,database
# from src.config.pydantic_config import settings
# from src.database import models,database
from passlib.context import CryptContext
from uuid import UUID

oauth2_scheme = OAuth2PasswordBearer(tokenUrl = 'login')
pwd_context = CryptContext(schemes=["bcrypt"],deprecated = "auto")

# SECRET_KEY = settings.secret_key
# ALGORITHM = settings.algorithm
# ACCESS_TOKEN_EXPIRES_MINUTES = settings.access_token_expire_minutes

# async def create_access_token(data : dict):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
#     to_encode.update({"exp":expire})
#     encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm = ALGORITHM)
#     return encoded_jwt

# async def verify_access_token(token : str, credentials_exception):
#     try:
#         payload = jwt.decode(token, SECRET_KEY,algorithms = [ALGORITHM])
#         user_id: UUID = payload.get("user_id")
#         if user_id is None:
#             raise credentials_exception
#         token_data = user_id
#     except JWTError:
#         raise credentials_exception
#     return token_data

# async def get_current_user(token : str = Depends(oauth2_scheme), db: AsyncSession = Depends(database.get_db)):
#     async with db.begin():
#         credentials_exception = HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail = "Could not validate credentials",
#             headers = {"WWW-Authenticate":"Bearer"}
#         )
#         token_data = await verify_access_token(token,credentials_exception)

#         result = await db.execute(select(model.User).where(model.User.user_id==token_data).options(
#                 selectinload(model.User.organizations), 
#                 selectinload(model.User.conversations),
#                 selectinload(model.User.suborganizations)
#             ))
#         user = result.scalar()
#         if not user:
#             raise credentials_exception
#         return user

def hash_password(password : str):
    return pwd_context.hash(password)

# def verify_password(plain_password, hashed_password):
#     return pwd_context.verify(plain_password,hashed_password)

# async def superuser_check(current_user: model.User = Depends(get_current_user)):
#     if not current_user.is_superuser:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only superusers can access this route")
#     return current_user

# async def superuser_or_admin_check(
#     request: Request,
#     current_user: model.User = Depends(get_current_user),
#     db: AsyncSession = Depends(database.get_db)
# ):
#     if current_user.is_superuser:
#         return current_user

#     if current_user.is_admin:
#         content_type = request.headers.get('content-type', '')

#         if 'application/json' in content_type:
#             payload = await request.json()
#             org_id = payload.get('org_id')
#             parent_org_id = payload.get('parent_org_id')
#         elif 'multipart/form-data' in content_type:
#             form = await request.form()
#             org_id = form.get('org_id')
#             parent_org_id = form.get('parent_org_id')
#         else:
#             raise HTTPException(status_code=400, detail="Unsupported content type")

#         if not org_id and not parent_org_id:
#             raise HTTPException(status_code=400, detail="Organization ID (org_id or parent_org_id) is required")

#         org_to_check = org_id if org_id else parent_org_id

#         async with db.begin():
#             result = await db.execute(
#                 select(model.user_org_association).where(
#                     (model.user_org_association.c.user_id == current_user.user_id) &
#                     (model.user_org_association.c.org_id == org_to_check)
#                 )
#             )
#             user_org = result.first()
#             if user_org:
#                 return current_user

#     raise HTTPException(
#         status_code=status.HTTP_403_FORBIDDEN,
#         detail="Only superusers or admins of the parent organization can access this route"
#     )