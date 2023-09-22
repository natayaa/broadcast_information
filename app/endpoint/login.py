from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from uuid import uuid4

from utils.auth import Tokenize
from utils.verification import VerPass

login_api = APIRouter()
template = Jinja2Templates("templates/")
tokenz = Tokenize()
verpass = VerPass()

@login_api.get("/")
async def login_page(request: Request):
    context = {"request": request}
    return template.TemplateResponse("login_.html", context=context)

@login_api.post("/api/authentication", summary="Create access and refresh token for user")
async def login_auth(request: Request, payload: OAuth2PasswordRequestForm = Depends()):
    user = db.get_user(payload.username, None) # database creation and connection
    if user is None:
        context = {"request": request, "noLog": "Failed to login, check your username or password"}
        return template.TemplateResponse('login_.html', context=context)
    hashed_pass = user['password']
    if not verpass.verify_password(payload.password, hashed_pass):
        context = {"request": request, "noLog": "Failed to login, check your password"}
        return template.TemplateResponse("login_.html", context=context)

    accepted = {"access_token": tokenz.create_access_token(user['email']), "refresh_token": tokenz.create_refresh_token(user['email'])}
    return accepted