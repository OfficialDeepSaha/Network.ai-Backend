from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import sessionmaker, Session
from models import Base
from fastapi import FastAPI, Depends



DATABASE_URL= "postgresql://postgres:VKTbOKIJLfiXXbIBOjddyXDQuPLqmySH@postgres.railway.internal:5432/railway"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/items/")
def read_items(db: Session = Depends(get_db)):
    # Your logic to fetch items from the database
    print("Application Working>>>>>>>>>>>>>>>>>>>>>>")
    pass

