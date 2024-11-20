import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from fastapi import APIRouter, Depends ,HTTPException,status
from Utills.oauth2 import get_current_user_with_roles,verify_password,hash_password
from config.log_config import logger
from database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select,update
from database.model import Admin,Organisation,SubOrganisation, User
from pydantic import BaseModel
from sqlalchemy.orm import Session
from config.pydantic_config import Settings
from Schema.auth_schema import EditOrganisation,OrganisationBase
from Utills.editprofile import update_org_info

router = APIRouter()

@router.put("/editorganization")
async def update_organization(
    org_id: int,
    org_data: EditOrganisation,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin"])),  
):
    user1, role = current_user

    if role != "superadmin":
        raise HTTPException(status_code=403, detail="Permission denied")

    result = await update_org_info(org_id, org_data, db)
    return result
