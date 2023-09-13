from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

main_page = APIRouter()
templates = Jinja2Templates("templates/")

@main_page.get("/")
async def main_homepage(request: Request):
    contexts = {"request": request}
    return templates.TemplateResponse("main.html", context=contexts)