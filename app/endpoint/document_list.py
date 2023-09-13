from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

document_list_ep = APIRouter()
templates = Jinja2Templates("templates/")

@document_list_ep.get("/")
async def home_documents(request: Request):
    contexts = {"request": request}
    return templates.TemplateResponse("documents.html", context=contexts)