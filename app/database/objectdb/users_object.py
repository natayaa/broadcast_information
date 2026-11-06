from sqlalchemy import String, Column, Integer

from database.db_connection import Base

class UsersTable(Base):
    __tablename__ = "tb_users"
    user_id = Column(Integer, autoincrement=True, unique=True, primary_key=True, nullable=False)
    username = Column(String, unique=True)
    user_email = Column(String)
    password = Column(String)
    mail_password = Column(String)
    firstname = Column(String)
    lastname = Column(String)