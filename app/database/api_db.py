from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased
from sqlalchemy import join

from db_connect import SessionLocal
from datetime import datetime

from schemas.user import tb_users

class API_DB:
    def __init__(self):
        self.session = SessionLocal()

    def register_user(self, payload_user: tb_users):
        pass
    