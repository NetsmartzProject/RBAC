import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from uuid import UUID
from fastapi import APIRouter, Depends ,HTTPException,status
from Schema.auth_schema import UpdateUserDetailsRequest
from Utills.oauth2 import get_current_user_with_roles,verify_password,hash_password
from config.log_config import logger
from database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.model import Admin,Organisation,SubOrganisation, User
from sqlalchemy.orm import Session

router = APIRouter()


def generate_temp_password(length=8):
    """Generate a random temporary password."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

async def send_temp_password_email(recipient_email, temp_password):
    """Send an email with the temporary password."""
    subject = "Temporary Password for Your Account"
    body = (
        f"Dear user,\n\n"
        f"Here is your temporary password: {temp_password}\n\n"
        "This temp password can be used for login. Please change your password after logging in to avoid any security concerns."
    )
   
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = "ak0590810@gmail.com"  
    msg['To'] = recipient_email
    
    msg.attach(MIMEText(body, "plain"))

    try:
        logger.info(f"Connecting to SMTP server: {"smtp.gmail.com"}:{587}")
        smtp_server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        
        if True:
            logger.info("Starting TLS connection...")
            smtp_server.starttls()
            smtp_server.ehlo()
        
        logger.info(f"Authenticating as: {"ak0590810@gmail.com"}")
        smtp_server.login("ak0590810@gmail.com", "vjgb uywp kiba gixu")
        
        smtp_server.send_message(msg)
        smtp_server.quit()
        
        logger.info(f"Password reset email sent successfully to {recipient_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as auth_error:
        error_msg = f"SMTP Authentication Error: {str(auth_error)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email authentication failed: {error_msg}"
        )
    except smtplib.SMTPServerDisconnected as disc_error:
        error_msg = f"SMTP Server Disconnected: {str(disc_error)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email server connection failed"
        )
    except smtplib.SMTPException as smtp_error:
        error_msg = f"SMTP Error: {str(smtp_error)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email sending failed"
        )
        
    except Exception as e:
        error_msg = f"Failed to send password reset email: {str(e)}"
    logger.error(error_msg)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to send reset password email"
    )


async def send_confirmation_email(email):
    """Send an email confirming the password change."""
    subject = "Password Change Confirmation"
    body = "Dear user,\n\nYour password has been successfully changed.\n\nBest regards,\nYour Team"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = "ak0590810@gmail.com"
    msg['To'] = email

    try:
        with smtplib.SMTP("smtp.example.com", 587) as server: 
            server.starttls()
            server.login("ak0590810@gmail.com", "vjgb uywp kiba gixu")  
            server.sendmail(email, msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send email")


@router.get("/fetch-details")
async def fetch_details(
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org", "user"])),
    db: Session = Depends(get_db)
):
    try:
        user_info, user_role = current_user
        print(user_info,"suborg")
        logger.info(f"User role: {user_role}")

        if user_role == "user":
            user_id = getattr(user_info, 'user_id',None)
            sub_org_id = getattr(user_info, 'sub_org_id',None)
            org_id_query = await db.execute(
                select(SubOrganisation.org_id).where(
                    SubOrganisation.sub_org_id == sub_org_id
                )
            )
            org_id = org_id_query.scalar_one_or_none()
            org_query = await db.execute(
                select(Organisation.org_name).where(
                    Organisation.org_id == org_id
                )
            )
            org_name = org_query.scalar_one_or_none()
            sub_org_query = await db.execute(
                select(SubOrganisation.sub_org_name).where(
                    SubOrganisation.sub_org_id == sub_org_id
                )
            )
            sub_org_name = sub_org_query.scalar_one_or_none()

            print(org_id,"orgid")
            # org_id = db.query(SubOrganisation.org_id).filter(SubOrganisation.sub_org_id == sub_org_id).scalar()
            user_allocated_hit = getattr(user_info, 'allocated_hits',None)
            user_available_hit = getattr(user_info, 'available_hits', None)
            username = getattr(user_info, 'username',None)
            name=getattr(user_info, 'name',None)
            user_email = getattr(user_info, 'email',None)
            return {
                "id": user_id,
                "allocated_hits": user_allocated_hit,
                "available_hits": user_available_hit,
                "sub_org_id":sub_org_id,
                "sub_org_name":sub_org_name,
                "org_name":org_name,
                "org_id":org_id,
                "username": username,
                "name":name,
                "email": user_email,
                "role": user_role
            }
        elif user_role == "sub_org":
            sub_org_id = getattr(user_info, 'sub_org_id',None)
            org_id = getattr(user_info, 'org_id',None)
            org_query = await db.execute(
                select(Organisation.org_name).where(
                    Organisation.org_id == org_id
                )
            )
            org_name = org_query.scalar_one_or_none()
            sub_org_name = getattr(user_info, 'sub_org_name',None)
            sub_org_username=getattr(user_info, 'username',None)
            sub_org_email = getattr(user_info, 'email',None)
            sub_allocated_hit=getattr(user_info, 'allocated_hits',None)
            sub_org_available_hits = getattr(user_info, 'available_hits', None)
            return {
                "id": sub_org_id,
                "sub_org_id": None,
                "sub_org_name":None,
                "org_id": org_id,
                "org_name":org_name,
                "name": sub_org_name,
                "username":sub_org_username,
                "email": sub_org_email,
                "allocated_hits":sub_allocated_hit,
                "available_hits":sub_org_available_hits,
                "role": user_role
            }

        elif user_role == "org":
            org_id = getattr(user_info, 'org_id',None)
            org_username=getattr(user_info, 'username',None)
            org_name = getattr(user_info, 'org_name',None)
            org_allocated_hits = getattr(user_info, 'allocated_hits',None)
            org_available_hits = getattr(user_info, 'available_hits', None)
            org_email = getattr(user_info, 'email',None)

            return {
                "id": org_id,
                "sub_org_id":None,
                "org_id":None,
                "sub_org_name":None,
                "org_name":None,
                "name": org_name,
                "allocated_hits": org_allocated_hits,
                "available_hits": org_available_hits,
                "email": org_email,
                "username":org_username,
                "role": user_role
            }

        elif user_role == "superadmin":
            superadmin_id = getattr(user_info, 'admin_id',None)
            superadmin_username=getattr(user_info, 'username',None)
            superadmin_name = getattr(user_info, 'admin_name',None)
            superadmin_email = getattr(user_info, 'email',None)

            return {
                "id": superadmin_id,
                "sub_org_id":None,
                "org_id":None,
                "sub_org_name":None,
                "org_name":None,
                "name": superadmin_name,
                "email": superadmin_email,
                "allocated_hits":None,
                "available_hits":None,
                "username":superadmin_username,
                "role": user_role
            }

        else:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized role"
            )

    except (IndexError, ValueError) as e:
        logger.error(f"Error extracting user information: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user details. Please check the user data format."
        )

@router.put("/editpersonalprofile")
async def edit_profile(
    new_name: str = None,
    new_username: str = None,
    new_email: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org", "user"]))
):
    user_info, user_role = current_user
    user_email = getattr(user_info, "email", None)
    
    if user_role == "superadmin":
        model = Admin
        name_field = "admin_name"
    elif user_role == "org":
        model = Organisation
        name_field = "org_name"
    elif user_role == "sub_org":
        model = SubOrganisation
        name_field = "sub_org_name"
    elif user_role == "user":
        model = User
        name_field = "name"
    else:
        raise HTTPException(status_code=403, detail="Invalid role")
    
    username_field = "username"  # Assuming `username` field is consistent across roles
    
    # Fetch the user
    result = await db.execute(select(model).where(model.email == user_email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Update username if provided
    if new_username:
        existing_user = await db.execute(select(model).where(getattr(model, username_field) == new_username))
        if existing_user.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="This username is already taken. Please choose another one.")
        setattr(user, username_field, new_username)
    
    # Update email if provided
    if new_email:
        existing_email_user = await db.execute(select(model).where(model.email == new_email))
        if existing_email_user.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="This email is already taken. Please choose another one.")
        setattr(user, "email", new_email)
    
    # Update name if provided
    if new_name:
        setattr(user, name_field, new_name)
    
    # Commit the changes
    await db.commit()
    await db.refresh(user)
    
    return {
        "message": "Profile updated successfully.",
        "updated_profile": {
            "name": getattr(user, name_field),
            "username": getattr(user, username_field),
            "email": getattr(user, "email"),
        }
    }

@router.post("/forgotpassword", description="Reset Own Password")
async def forgot_password(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_query = select(User).where(User.email == email)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()

        org_query = select(Organisation).where(Organisation.email == email)
        org_result = await db.execute(org_query)
        organisation = org_result.scalars().first()

        sub_org_query = select(SubOrganisation).where(SubOrganisation.email == email)
        sub_org_result = await db.execute(sub_org_query)
        suborganisation = sub_org_result.scalars().first()

        if user or organisation or suborganisation:
            temp_password = generate_temp_password()
            hashed_temp_password = hash_password(temp_password)

            if user:
                user.password = hashed_temp_password
            elif organisation:
                organisation.password = hashed_temp_password
            elif suborganisation:
                suborganisation.password = hashed_temp_password

            await db.commit()

            await send_temp_password_email(email, temp_password)
            
            return {"message": "Temporary password has been sent to your email"}
        else:
            return {"message": "Email does not exist"}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

      
@router.post("/changepassword", description="Change Own Password")
async def change_password(
    email: str,
    old_password: str,
    new_password: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_query = select(User).where(User.email == email)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()

        org_query = select(Organisation).where(Organisation.email == email)
        org_result = await db.execute(org_query)
        organisation = org_result.scalars().first()

        sub_org_query = select(SubOrganisation).where(SubOrganisation.email == email)
        sub_org_result = await db.execute(sub_org_query)
        suborganisation = sub_org_result.scalars().first()

        record = user or organisation or suborganisation
        if not record:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email does not exist")

        if not verify_password(old_password, record.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")

        record.password = hash_password(new_password)
        await db.commit()


        return {"message": "Your password has been changed successfully."}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/deactivateUser")
async def soft_delete(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org"]))
):
    user_info, user_role = current_user

    # Restrict access for the 'user' role
    if user_role == "user":
        raise HTTPException(status_code=403, detail="You do not have access to this route.")

    # Define the deletion hierarchy
    if user_role == "superadmin":
        allowed_models = [Organisation, SubOrganisation, User]
    elif user_role == "org":
        allowed_models = [SubOrganisation, User]
    elif user_role == "sub_org":
        allowed_models = [User]
    else:
        raise HTTPException(status_code=403, detail="Invalid role for soft deletion.")

    # Attempt to find and soft-delete the user/org/sub-org
    for model in allowed_models:
        query = select(model).where(model.id == user_id, model.is_active == True)
        result = await db.execute(query)
        entity = result.scalar_one_or_none()

        if entity:
            # Perform the soft delete by setting `is_active` to False
            setattr(entity, "is_active", False)
            await db.commit()
            return {
                "message": f"{model.__name__} with ID {user_id} has been soft-deleted successfully.",
                "deleted_entity": {
                    "id": user_id,
                    "type": model.__name__,
                    "is_active": entity.is_active
                },
            }

    # If no entity is found in the allowed models
    raise HTTPException(status_code=404, detail="Entity not found or you do not have permissions to delete it.")

@router.post("/activateUser")
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org"]))
):
    user_info, user_role = current_user

    # Restrict access for the 'user' role
    if user_role == "user":
        raise HTTPException(status_code=403, detail="You do not have access to this route.")

    # Define the activation hierarchy
    if user_role == "superadmin":
        allowed_models = [Organisation, SubOrganisation, User]
    elif user_role == "org":
        allowed_models = [SubOrganisation, User]
    elif user_role == "sub_org":
        allowed_models = [User]
    else:
        raise HTTPException(status_code=403, detail="Invalid role for activation.")

    # Attempt to find and activate the user/org/sub-org
    for model in allowed_models:
        query = select(model).where(model.id == user_id, model.is_active == False)
        result = await db.execute(query)
        entity = result.scalar_one_or_none()

        if entity:
            # Activate the user by setting `is_active` to True
            setattr(entity, "is_active", True)
            await db.commit()
            return {
                "message": f"{model.__name__} with ID {user_id} has been activated successfully.",
                "activated_entity": {
                    "id": user_id,
                    "type": model.__name__,
                    "is_active": entity.is_active
                },
            }

    # If no entity is found in the allowed models
    raise HTTPException(status_code=404, detail="Entity not found or you do not have permissions to activate it.")

@router.put("/updateOtherUserDetails/{entity_id}")
async def update_user_details(
    entity_id: UUID,
    update_request: UpdateUserDetailsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: tuple = Depends(get_current_user_with_roles(["superadmin", "org", "sub_org"]))
):
    user_info, user_role = current_user

    # Restrict access for the 'user' role
    if user_role == "user":
        raise HTTPException(status_code=403, detail="You do not have access to this route.")

    # Define role-based models and hierarchy
    models_to_update = {
        "superadmin": [Organisation, SubOrganisation, User],
        "org": [SubOrganisation, User],
        "sub_org": [User],
    }
    allowed_models = models_to_update.get(user_role)

    if not allowed_models:
        raise HTTPException(status_code=403, detail="Invalid role for updating user details.")

    # Attempt to find the entity
    for model in allowed_models:
        query = select(model).where(model.user_id == entity_id if model == User else model.org_id == entity_id)
        if user_role == "org" and model in [SubOrganisation, User]:
            # Restrict results to within the organization
            query = query.where(model.org_id == user_info.org_id)
        elif user_role == "sub_org" and model == User:
            # Restrict results to within the sub-organization
            query = query.where(model.sub_org_id == user_info.sub_org_id)

        result = await db.execute(query)
        entity = result.scalar_one_or_none()

        if entity:
            # Update fields based on request
            if isinstance(entity, User):
                if update_request.name:
                    entity.name = update_request.name
                if update_request.email:
                    existing_email_query = select(User).where(User.email == update_request.email, User.user_id != entity_id)
                    existing_email_result = await db.execute(existing_email_query)
                    if existing_email_result.scalar_one_or_none():
                        raise HTTPException(status_code=400, detail="This email is already in use.")
                    entity.email = update_request.email
                if update_request.username:
                    existing_username_query = select(User).where(User.username == update_request.username, User.user_id != entity_id)
                    existing_username_result = await db.execute(existing_username_query)
                    if existing_username_result.scalar_one_or_none():
                        raise HTTPException(status_code=400, detail="This username is already in use.")
                    entity.username = update_request.username
                if update_request.tool_ids is not None:
                    entity.tool_ids = update_request.tool_ids
                if update_request.allocated_hits is not None:
                    if update_request.allocated_hits < 0:
                        raise HTTPException(status_code=400, detail="Allocated hits cannot be negative.")
                    entity.allocated_hits = update_request.allocated_hits
                    entity.available_hits = update_request.allocated_hits
                if update_request.allocated_ai_tokens is not None:
                    if update_request.allocated_hits < 0:
                        raise HTTPException(status_code=400, detail="Allocated hits cannot be negative.")
                    entity.allocated_ai_tokens = update_request.allocated_ai_tokens
                    entity.remaining_ai_tokens = update_request.allocated_ai_tokens

            elif isinstance(entity, SubOrganisation):
                if update_request.name:
                    entity.sub_org_name = update_request.name
                if update_request.email:
                    existing_email_query = select(SubOrganisation).where(SubOrganisation.email == update_request.email, SubOrganisation.sub_org_id != entity_id)
                    existing_email_result = await db.execute(existing_email_query)
                    if existing_email_result.scalar_one_or_none():
                        raise HTTPException(status_code=400, detail="This email is already in use.")
                    entity.email = update_request.email
                if update_request.username:
                    existing_username_query = select(SubOrganisation).where(SubOrganisation.username == update_request.username, SubOrganisation.sub_org_id != entity_id)
                    existing_username_result = await db.execute(existing_username_query)
                    if existing_username_result.scalar_one_or_none():
                        raise HTTPException(status_code=400, detail="This username is already in use.")
                    entity.username = update_request.username
                if update_request.tool_ids is not None:
                    entity.tool_ids = update_request.tool_ids
                if update_request.allocated_hits is not None:
                    if update_request.allocated_hits < 0:
                        raise HTTPException(status_code=400, detail="Allocated hits cannot be negative.")
                    entity.allocated_hits = update_request.allocated_hits
                    entity.available_hits = update_request.allocated_hits
                if update_request.allocated_ai_tokens is not None:
                    if update_request.allocated_hits < 0:
                        raise HTTPException(status_code=400, detail="Allocated hits cannot be negative.")
                    entity.allocated_ai_tokens = update_request.allocated_ai_tokens
                    entity.remaining_ai_tokens = update_request.allocated_ai_tokens

            elif isinstance(entity, Organisation):
                if update_request.name:
                    entity.org_name = update_request.name
                if update_request.email:
                    existing_email_query = select(Organisation).where(Organisation.email == update_request.email, Organisation.org_id != entity_id)
                    existing_email_result = await db.execute(existing_email_query)
                    if existing_email_result.scalar_one_or_none():
                        raise HTTPException(status_code=400, detail="This email is already in use.")
                    entity.email = update_request.email
                if update_request.tool_ids is not None:
                    entity.tool_ids = update_request.tool_ids
                if update_request.allocated_hits is not None:
                    if update_request.allocated_hits < 0:
                        raise HTTPException(status_code=400, detail="Allocated hits cannot be negative.")
                    entity.allocated_hits = update_request.allocated_hits
                    entity.available_hits = update_request.allocated_hits
                if update_request.allocated_ai_tokens is not None:
                    if update_request.allocated_hits < 0:
                        raise HTTPException(status_code=400, detail="Allocated hits cannot be negative.")
                    entity.allocated_ai_tokens = update_request.allocated_ai_tokens
                    entity.remaining_ai_tokens = update_request.allocated_ai_tokens

            # Commit changes
            await db.commit()
            await db.refresh(entity)

            return {
                "message": f"{model.__name__} details updated successfully.",
                "updated_entity": entity,
            }

    # If no entity is found
    raise HTTPException(status_code=404, detail="Entity not found or you do not have permissions to update it.")
