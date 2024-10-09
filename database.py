from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker
from models import Base
from databases import Database
import os

# Load the DATABASE_URL from the environment (Render environment variables are already available)
DATABASE_URL = "postgresql://connector_xu3z_user:bFNP3icqOpvpxchbOaLlexo4M6OAzvY1@dpg-cs2n5et6l47c73blnmt0-a.oregon-postgres.render.com/connector_xu3z"

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Sync engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# For async support
database = Database(DATABASE_URL)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

