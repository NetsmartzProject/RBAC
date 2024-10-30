from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from database.database import get_db
import traceback
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from config.log_config import logger


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FOR THE DATABASE CONNECTIVITY WITH POSTGRESS ASYNCHRONOUSLY

@app.get("/check_db/raw")
async def check_db_connection_raw(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            return {
                "status": "success",
                "message": "Connected to the database!",
                "method": "raw SQL",
            }
        else:
            return {
                "status": "failure",
                "message": "Database query did not return expected result",
                "method": "raw SQL",
            }
    except Exception as e:
        print("Database connection error:", e)
        logger.error("Database connection error :",e)
        print(traceback.format_exc( ))
        return {
            "status": "failure",
            "message": f"Database connection failed: {str(e)}",
            "method": "raw SQL",
        }

# END OF THE CONNECTIVITY WITH THE POSTGRESS DATABASE ASYNCHRONOUSLY


# @app.get("/check_db")
# async def check_db_connection(db: Session = Depends(get_db)):
#     try:
#         # Use text() to wrap the raw SQL string
#         result = db.execute(text("SELECT 1")).scalar()
#         if result == 1:
#             return {"status": "success", "message": "Connected to the database!"}
#         else:
#             return {
#                 "status": "failure",
#                 "message": "Database query did not return expected result",
#             }
#     except Exception as e:
#         return {"status": "failure", "message": f"Database connection failed: {str(e)}"}
