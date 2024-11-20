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
            org_id = db.query(SubOrganisation.org_id).filter(SubOrganisation.sub_org_id == sub_org_id).scalar()
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
                "org_id":org_id,
                "username": username,
                "name":name,
                "email": user_email,
                "role": user_role
            }
        elif user_role == "sub_org":
            sub_org_id = getattr(user_info, 'sub_org_id',None)
            org_id = getattr(user_info, 'org_id',None)
            sub_org_name = getattr(user_info, 'sub_org_name',None)
            sub_org_username=getattr(user_info, 'username',None)
            sub_org_email = getattr(user_info, 'email',None)
            sub_allocated_hit=getattr(user_info, 'allocated_hits',None)
            sub_org_available_hits = getattr(user_info, 'available_hits', None)
            return {
                "id": sub_org_id,
                "sub_org_id": None,
                "org_id": org_id,
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
            org_allocated_hits = getattr(user_info, 'total_hits_limit',None)
            org_available_hits = getattr(user_info, 'available_hits', None)
            org_email = getattr(user_info, 'email',None)

            return {
                "id": org_id,
                "sub_org_id":None,
                "org_id":None,
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
    # user_email = user_info[6]
    user_email = getattr(user_info, "email", None) 

    if user_role == "superadmin":
        model = Admin
        username_field = "admin_name"  
    elif user_role == "org":
        model = Organisation
        username_field = "org_name"  
    elif user_role == "sub_org":
        model = SubOrganisation
        username_field = "sub_org_name"  
    elif user_role == "user":
        model = User
        username_field = "username"  
    else:
        raise HTTPException(status_code=403, detail="Invalid role")

    result = await db.execute(select(model).where(model.email == user_email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if new_username:
        existing_user = await db.execute(select(model).where(getattr(model, username_field) == new_username))
        if existing_user.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="This username has already been taken. Please choose another one.")
        setattr(user, username_field, new_username)

    if new_email:
        existing_email_user = await db.execute(select(model).where(model.email == new_email))
        if existing_email_user.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="This email has already been taken. Please choose another one.")
        user.email = new_email

    if new_name:
        user.name = new_name 

    await db.commit()
    await db.refresh(user)

    return {
        "message": "Profile updated successfully.",
        "updated_profile": {
            "name": user.name,
            "username": getattr(user, username_field),
            "email": user.email
        }
    }

@router.post("/forgotpassword")
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

      
@router.post("/changepassword")
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


        return {"message": "Yes, it is true. Your password has been changed successfully."}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

