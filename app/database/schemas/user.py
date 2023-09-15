from pydantic import BaseModel

class tb_users(BaseModel):
    uid: int
    username: str
    password: str
    role: str
    email: str