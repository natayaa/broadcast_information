from pydantic import BaseModel
from fastapi import Form
from typing import List

class MailContainerBody(BaseModel):
    recipient_list: List[str] = Form(...)
    subjectMail: str = Form(...)
    carbon_copy_mail: List[str] = Form(...)
    mail_message: str = Form(...)
    server_name: str = Form(...)