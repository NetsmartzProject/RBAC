from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router
from routes.organisation import router as org_router
from routes.tools import router as tool_router

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

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, port=8801)