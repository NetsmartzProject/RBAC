from datetime import datetime , timedelta
from fastapi import Depends, status, HTTPException, Request
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from database import model,database
from uuid import UUID
from config.pydantic_config import settings
from database.database import get_db
from sqlalchemy import text, select,update
from sqlalchemy.orm import Session
from typing import Literal, List
from fastapi import Request, HTTPException
from Schema.auth_schema import  EditOrganisation
from database.model import Organisation,SubOrganisation,User,Admin,ToolMaster
from Utills import oauth2
from config.log_config import logger
import bcrypt




# async def update_org_info(org_id: int, org_data: EditOrganisation, db: AsyncSession):
#     try:
#         # Fetch the organization to be updated
#         query = select(Organisation).where(Organisation.org_id == org_id)
#         result = await db.execute(query)
#         organization = result.scalar_one_or_none()

#         if not organization:
#             raise HTTPException(status_code=404, detail="Organization not found")
        
#         # Update organization fields with the new data
#         organization.org_name = org_data.org_name or organization.org_name
#         organization.org_email = org_data.org_email or organization.org_email
#         organization.total_hits_limit = org_data.total_hits_limit or organization.total_hits_limit
#         organization.username = org_data.username or organization.username
#         organization.available_hits = org_data.available_hits if org_data.available_hits is not None else organization.available_hits

#         # Check if the object has been modified
#         if db.is_modified(organization):
#             await db.flush()
#             await db.commit()

#             logger.info(f"Organization updated successfully: {organization}")

#             # Return the success message and the updated organization
#             return {"message": "Organization updated successfully", "organization": organization}
#         else:
#             return {"message": "No changes made to the organization"}
    
#     except SQLAlchemyError as e:
#         logger.error(f"Error while updating organization: {e}")
#         await db.rollback()
#         raise HTTPException(status_code=500, detail="Internal Server Error")


# async def update_org_info(org_id: int, org_data: EditOrganisation, db: AsyncSession):
#     try:
#         # Fetch the organization to be updated
#         query = select(Organisation).where(Organisation.org_id == org_id)
#         result = await db.execute(query)
#         organization = result.scalar_one_or_none()

#         if not organization:
#             raise HTTPException(status_code=404, detail="Organization not found")
        
#         if org_data.org_name:
#             organization.org_name = org_data.org_name
#         if org_data.org_email:
#             organization.email = org_data.org_email
#         if org_data.total_hits_limit is not None:
#             organization.total_hits_limit = org_data.total_hits_limit
#         if org_data.username:
#             organization.username = org_data.username

#         if org_data.tools:
#             organization.tool_ids = org_data.tools

#         # Commit changes to the database
#         if db.is_modified(organization):
#             await db.flush()
#             await db.commit()

#             logger.info(f"Organization updated successfully: {organization}")

#             # Return the success message and the updated organization
#             return {"message": "Organization updated successfully", "organization": organization}
#         else:
#             return {"message": "No changes made to the organization"}
    
#     except SQLAlchemyError as e:
#         logger.error(f"Error while updating organization: {e}")
#         await db.rollback()
#         raise HTTPException(status_code=500, detail="Internal Server Error")


async def update_org_info(org_id: int, org_data: EditOrganisation, db: AsyncSession):
    try:
        # Fetch the organization to be updated
        query = select(Organisation).where(Organisation.org_id == org_id)
        result = await db.execute(query)
        organization = result.scalar_one_or_none()

        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Update organization fields
        if org_data.org_name:
            organization.org_name = org_data.org_name
        if org_data.org_email:
            organization.email = org_data.org_email
        if org_data.total_hits_limit is not None:
            organization.total_hits_limit = org_data.total_hits_limit
        if org_data.username:
            organization.username = org_data.username
        
        # Check if the provided tool_ids are valid
        if org_data.tools:
            # Fetch the tool_ids from the ToolMaster table
            tool_ids_query = select(ToolMaster.tool_id).where(ToolMaster.tool_id.in_(org_data.tools))
            tool_ids_result = await db.execute(tool_ids_query)
            valid_tool_ids = [row[0] for row in tool_ids_result]
            
            # Update the organization's tool_ids
            organization.tool_ids = valid_tool_ids
            organization.tool_grant_dates = [datetime.now()] * len(valid_tool_ids)

        # Commit changes to the database
        if db.is_modified(organization):
            await db.flush()
            await db.commit()

            logger.info(f"Organization updated successfully: {organization}")

            # Return the success message and the updated organization
            return {"message": "Organization updated successfully", "organization": organization}
        else:
            return {"message": "No changes made to the organization"}
    
    except SQLAlchemyError as e:
        logger.error(f"Error while updating organization: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")