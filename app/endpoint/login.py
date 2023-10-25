from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from decouple import config
from typing_extensions import Annotated
from datetime import datetime, timedelta

from api.model.authentication_model import TokenModel
from database.auth_db import Users
from api.model.user_model import RegisterUser
from utils.verification import VerPass


login_api = APIRouter()
template = Jinja2Templates("templates/")
users = Users()
authpw = VerPass()

@login_api.get("/")
async def login_page(request: Request):
    context = {"request": request}
    return template.TemplateResponse("login_.html", context=context)

@login_api.post("/register")
async def register_user(request: Request, payload: RegisterUser):
    container = {"username": payload.username, "password": authpw.get_hashed_password(password=payload.password),
                 "firstname": payload.firstname, "lastname": payload.lastname, "user_email": payload.user_email,
                 "mail_password": payload.mail_password}
    rg = users.create_user(**container)
    return rg

@login_api.post("/api/user/authentication", response_model=TokenModel)
async def authentication_endpoint(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = users.authenticate_user(username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password", 
                            headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=int(config("ACCESS_TOKEN_EXPIRE_MINUTES")))

    access_token = access_token = users.create_access_token_user(expires_date=access_token_expires, payload_user={"sub": user.username, "scopes": form_data.scopes})
    
    return {"access_token": access_token, "token_type": "bearer"}
