from fastapi import FastAPI, status, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from endpoint import main_page, document_list, register_recipient, upload_document, login


broadcast_mailing = FastAPI()
broadcast_mailing.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")

# handle 404
@broadcast_mailing.exception_handler(status.HTTP_404_NOT_FOUND)
async def page_not_found(request: Request, __):
    content_page = {"request": request, "message": "The page you are looking for are not to be found",
                    "message2": "please go back to homepage."}
    return templates.TemplateResponse("404.html", context=content_page, status_code=status.HTTP_404_NOT_FOUND)

broadcast_mailing.include_router(main_page.main_page, tags=["Home App"], prefix="")
broadcast_mailing.include_router(document_list.document_list_ep, tags=['Documents Table'], prefix=("/app/documents"))
broadcast_mailing.include_router(register_recipient.recipient, tags=["Recipient"], prefix="/app/user/recipients")
broadcast_mailing.include_router(upload_document.upload_endpoint, tags=["Upload Document"], prefix="/app/document/upload")
broadcast_mailing.include_router(login.login_api, tags=['Login'], prefix="/app/login")