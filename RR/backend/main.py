from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database.connection import create_tables
from .api.auth_routes import router as auth_router
from .api.research_routes import router as research_router
from .api.workspace_routes import router as workspace_router
from .api.document_routes import router as document_router
from .api.export_routes import router as export_router

app = FastAPI(
    title="Cyberify Research Agent API",
    description="Autonomous Business Research Agent",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_tables()

app.include_router(auth_router)
app.include_router(research_router)
app.include_router(workspace_router)
app.include_router(document_router)
app.include_router(export_router)

@app.get("/")
def root():
    return {"message": "Cyberify Research Agent API is running ✅"}