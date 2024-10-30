# import asyncio
# from sqlalchemy.ext.asyncio import AsyncSession
# from database.model import Admin
# from config.log_config import logger
# from Utills import oauth2
# from database import model,database
# from config.pydantic_config import settings

# async def create_superuser(
#     admin_name: str,
#     email: str,
#     password: str,
#     max_hits:str,
#     db: AsyncSession
# ):
#     try:
#         async with db.begin():

#             hashed_password = oauth2.hash_password(password)
#             new_superuser = model.Admin(
#                 admin_name=admin_name,
#                 email=email,
#                 password=hashed_password,
#                 max_hits=max_hits,
#             )

#             db.add(new_superuser)
#             await db.commit()

#         logger.info(f"Superuser '{admin_name}' created successfully!")
#     except Exception as e:
#         logger.error(f"Error creating superuser: {str(e)}")
#         raise

# async def main():
#     admin_name = settings.superuser_username
#     email = settings.superuser_email
#     password = settings.superuser_password
#     max_hits=settings.max_hits

#     async for db in database.get_db():
#         await create_superuser(admin_name, email, password,max_hits,db)

# if __name__ == "__main__":
#     asyncio.run(main())


import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from config.log_config import logger
from Utills import oauth2
from database import model, database
from config.pydantic_config import settings


async def create_superuser(
    admin_name: str, email: str, password: str, max_hits: int, db: AsyncSession
):
    try:
        async with db.begin():
            hashed_password = oauth2.hash_password(password)
            new_superuser = model.Admin(
                admin_name=admin_name,
                email=email,
                password=hashed_password,
                max_hits=max_hits,
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
    max_hits = settings.max_hits

    async for db in database.get_db():
        await create_superuser(admin_name, email, password, max_hits, db)


if __name__ == "__main__":
    asyncio.run(main())
