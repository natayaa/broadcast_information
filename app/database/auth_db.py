from sqlalchemy.exc import IntegrityError
from typing import Union
from datetime import timedelta, datetime
from jose import jwt, JWTError
from decouple import config
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from typing_extensions import Annotated

from database.objectdb.users_object import UsersTable
from database.api_db import API_DB
from api.model import user_model
from api.model import authentication_model
from utils.verification import VerPass

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/app/users/api/user/authentication")
verpass = VerPass()

class Users(API_DB):
    def __init__(self):
        super().__init__()

    def create_user(self, **payload):
        try:
            user_payload = UsersTable()
            user_payload.username = payload.get("username")
            user_payload.user_email = payload.get("user_email")
            user_payload.firstname = payload.get("firstname")
            user_payload.lastname = payload.get("lastname")
            user_payload.password = payload.get("password")
            user_payload.mail_password = payload.get("mail_password")
            self.session.add(user_payload)
            self.session.commit()
            self.session.close()
            return True
        except IntegrityError:
            self.session.rollback()
            self.session.close()
            return False


    def get_user(self, username):
        user = self.session.query(UsersTable).filter(UsersTable.username == username).first()
        
        if user:
            user_dict = {column.name: getattr(user, column.name) for column in UsersTable.__table__.columns}
            return user_model.User(**user_dict)
        else: 
            return None
        
    def authenticate_user(self, username: str, password: str):
        user = self.get_user(username)
        if not user:
            return False
        if not verpass.verify_password(password=password, hashed_password=user.password):
            return False
        return user
    
    def create_access_token_user(self, expires_date: Union[timedelta, None] = None, payload_user = dict):
        to_encode = payload_user.copy()

        if expires_date:
            expire = datetime.now() + expires_date
        else:
            expire = datetime.now() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, config("SECRET_KEYACCESS"), algorithm=config("ALGORITHM"))
        return encoded_jwt
    
    async def get_current_user(self, token: Annotated[str, Depends(oauth2_scheme)]):
        try:
            payload = jwt.decode(token, config("SECRET_KEYACCESS"), algorithms=[config("ALGORITHM")])
            username: str = payload.get("sub")
            if username is None:
                return False
            tokendatta = authentication_model.TokenData(username=username)
        except JWTError as e:
            print(e)
            raise e
        
        user = self.get_user(tokendatta.username)
        if not user:
            return False
        return user