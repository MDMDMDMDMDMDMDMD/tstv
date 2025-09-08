from fastapi import FastAPI
from .core.config import settings
from .db.session import engine
from .db.base import Base
from .api.v1.api import api_router

def create_tables():
    Base.metadata.create_all(bind=engine)

def create_app():
    app = FastAPI(title=settings.PROJECT_NAME)
    app.include_router(api_router, prefix=settings.API_V1_STR)
    create_tables() # Re-added for immediate table creation
    return app

app = create_app()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Document Management System"}
