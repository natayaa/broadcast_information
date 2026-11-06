from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from decouple import config

SQL_SERVERHOST = config("SQLSERVERHOST")

engine = create_engine(SQL_SERVERHOST, echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(autoflush=False, bind=engine, autocommit=False)

def call_database() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()