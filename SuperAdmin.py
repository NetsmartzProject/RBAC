import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from config.log_config import logger
from Utills import oauth2
from database import model, database
from config.pydantic_config import settings
from datetime import datetime


async def create_superuser(
    admin_name: str, username:str, email: str, password: str, db: AsyncSession
):
    try:
        async with db.begin():
            hashed_password = oauth2.hash_password(password)
            new_superuser = model.Admin(
                admin_name=admin_name,
                username=username,
                email=email,
                password=hashed_password,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            db.add(new_superuser)
            await db.commit()

        logger.info(f"Superuser '{admin_name}' created successfully!")
    except Exception as e:
        logger.error(f"Error creating superuser: {str(e)}")
        raise


async def main():
    admin_name = settings.superuser_username
    email = settings.superuser_email
    password = settings.superuser_password
    username= settings.db_username

    async for db in database.get_db():
        await create_superuser(admin_name,username, email, password, db)


if __name__ == "__main__":
    asyncio.run(main())
