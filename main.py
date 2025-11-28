from fastapi import FastAPI, Request, HTTPException
from listeners.registration import users_router
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Depends
from servis.auth import get_current_user

from dotenv import load_dotenv
import os

load_dotenv('.\config.env')

app = FastAPI()
templates = Jinja2Templates(directory="frontend")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('session_key_open'), # ключ для шифровки кук
    session_cookie="session", # имя сессии
    max_age=3600, # сколько сессия будет жить в секундах
    same_site="lax", # защита от CSRF средняя
    https_only=True, # будут ли куки отправлятся только по https
)

app.include_router(users_router)

@app.get("/", response_class=HTMLResponse)
async def get_main(request: Request):
    return templates.TemplateResponse(
        request,
        "main.html",
        {
        'date': 'динамические данные'
        }
    )

@app.get("/profile")
async def user_profile(request: Request, user: dict = Depends(get_current_user)):
    return {
        "page": "Личный кабинет",
        "user": user
    }