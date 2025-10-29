from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

#build connection url
DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

#create database engine
engine = create_engine(DATABASE_URL)

# create session factory
Sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base class for all models
Base = declarative_base()

#Dependency for FastAPI routes
def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()