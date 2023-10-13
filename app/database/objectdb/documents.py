from sqlalchemy import String, Integer, Column, LargeBinary
from datetime import datetime

from database.db_connection import Base

class documentsTable(Base):
    __tablename__ = "tb_documents"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    document_no = Column(String, nullable=False, unique=True)
    document_type = Column(String)
    document_subject = Column(String)
    document_description = Column(String)
    model_tv = Column(String)
    filename_upload = Column(LargeBinary)
    filename = Column(String)
    distributed_to = Column(String)
    uploader = Column(String)
    datetime_upload = Column(String, default=datetime.now().strftime("%d %B %Y, %H:%M"))