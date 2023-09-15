from pydantic import BaseModel
from fastapi import File, UploadFile, Form

class BroadcastReport(BaseModel):
    documentNo: str = Form(...)
    documentType: str = Form(...)
    subjectDocument: str = Form(...)
    documentDesc: str = Form(...)
    model_tv: str = Form(...)
    distributed_to: str = File(...)