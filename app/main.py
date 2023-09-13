from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from endpoint import main_page, document_list, register_recipient, upload_document

broadcast_mailing = FastAPI()
broadcast_mailing.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")

broadcast_mailing.include_router(main_page.main_page, tags=["Home App"], prefix="/app")
broadcast_mailing.include_router(document_list.document_list_ep, tags=['Documents Table'], prefix=("/app/documents"))
broadcast_mailing.include_router(register_recipient.recipient, tags=["Recipient"], prefix="/app/user/recipients")
broadcast_mailing.include_router(upload_document.upload_endpoint, tags=["Upload Document"], prefix="/app/document/upload")