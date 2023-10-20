from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased
from sqlalchemy import join

from database.db_connection import SessionLocal
from database.objectdb import documents

class API_DB:
    def __init__(self):
        self.session = SessionLocal()

    async def get_listing_record(self):
        quer = self.session.query(documents.documentsTable.document_no).all()
        if quer:
            res = [item[0] for item in quer]
            return res
        else:
            return None

    async def get_documents_detail(self, document_number):
        qur = self.session.query(documents.documentsTable.document_no,
                                 documents.documentsTable.document_type,
                                 documents.documentsTable.document_description,
                                 documents.documentsTable.model_tv,
                                 documents.documentsTable.datetime_upload,
                                 documents.documentsTable.distributed_to).filter(documents.documentsTable.document_no==document_number).first()
        if qur:
            data = {
                "document_no": qur.document_no,
                "document_type": qur.document_type,
                "document_description": qur.document_description,
                "model_tv": qur.model_tv,
                "datetime_upload": qur.datetime_upload,
                "distributed_to": qur.distributed_to
            }
            return data
        else:
            return None
    
    async def serve_document_blob(self, document_no):
        quer = self.session.query(documents.documentsTable.filename_upload).filter_by(document_no = document_no).first()
        if quer:
            return quer
        return None
    
    async def write_documentdb(self, **payload):
        try:
            container = documents.documentsTable()
            container.document_no = payload.get("document_no")
            container.document_type = payload.get("document_type")
            container.document_subject = payload.get("document_subject")
            container.document_description = payload.get("document_description")
            container.model_tv = payload.get("m_tv_name")
            container.filename = payload.get("filename")
            container.distributed_to = payload.get("distribute_to")
            container.filename_upload = payload.get("filename_upload")
            container.uploader = payload.get("uploader_name")
            self.session.add(container)
            self.session.commit()
            self.session.close()
            return True
        except IntegrityError as e:
            self.session.rollback()
            return False
        
    async def read_documentdb(self, offset, limit):
        query = self.session.query(documents.documentsTable).offset(offset).limit(limit).all()
        return query

    def count_record_registered_documents(self) -> int:
        qq = self.session.query(documents.documentsTable).count()
        return qq
    

from database.objectdb.recipients_obj import TableRecipients

class Recipients(API_DB):
    def __init__(self):
        super().__init__()

    async def register_recipient(self, **payload):
        try:
            register_container = TableRecipients()
            register_container.recipient_mail = payload.get("recipient_mail")
            register_container.recipient_name = payload.get("recipient_name")
            register_container.recipient_division = payload.get("recipient_division")
            register_container.recipient_category = payload.get("recipient_category")
            self.session.add(register_container)
            self.session.commit()
            self.session.close()
            return True
        except IntegrityError as E:
            print(E)
            self.session.rollback()
            return False
        
    async def get_recipient_list(self, offset, limit):
        query = self.session.query(TableRecipients).offset(offset).limit(limit).all()
        if query:
            return query
        else:
            return None
        
    def count_recipients(self):
        query = self.session.query(TableRecipients).count()
        return query
    
    async def get_recipients_category(self, filted):
        query = self.session.query(TableRecipients).filter(TableRecipients.recipient_division.in_(filted)).all()

        return query