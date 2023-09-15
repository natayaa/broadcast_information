from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from database.schemas.user import tb_users

# user related API
users_api = APIRouter()
template = Jinja2Templates("templates/")

@users_api.post("/api/register")
async def register_users(user_payload: tb_users):
    print(user_payload)

@users_api.get("/register")
async def register_pg_users(request: Request):
    context = {"request": request}
    return template.TemplateResponse("register_users.html", context=context)