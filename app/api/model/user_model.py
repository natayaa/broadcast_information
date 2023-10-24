from typing import Union
from pydantic import BaseModel

class User(BaseModel):
    username: str
    user_email: Union[str, None] = None
    firstname: Union[str, None] = None
    lastname: Union[str, None] = None
    password: Union[str, None] = None


class RegisterUser(BaseModel):
    username: str 
    password: str 
    user_email: str
    mail_password: str
    firstname: str = None
    lastname: str = None