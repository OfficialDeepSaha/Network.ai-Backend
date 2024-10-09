from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import sessionmaker, Session
from models import Base
from fastapi import FastAPI, Depends



DATABASE_URL= "postgresql://connector_a546_user:bezm3TTrHodZg8iN2T8vbTtOgKvI6xEO@dpg-cs35jge8ii6s738ggq3g-a.oregon-postgres.render.com/connector_a546"

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

