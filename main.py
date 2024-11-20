from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from database.database import get_db
import traceback
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from config.log_config import logger
from Utills.oauth2 import verify_password
from routes.auth import router as auth_router
from routes.organisation import router as org_router
from routes.tools import router as tool_router
from routes.edit import router as edit_router


app = FastAPI(root_path="/api", docs_url="/docs", openapi_url="/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(org_router)
app.include_router(tool_router)
app.include_router(edit_router)

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, port=8801)