from sqlalchemy import String, Integer, Column
from database.db_connection import Base

class TableRecipients(Base):
    __tablename__ = "tb_recipients"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    recipient_mail = Column(String)
    recipient_name = Column(String)
    recipient_division = Column(String)
    recipient_category = Column(String)