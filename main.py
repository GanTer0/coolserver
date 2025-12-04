from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
from listeners.registration import users_router
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Depends
from servis.auth import get_current_user, cheak_session_current
from database.main import check_user_session, update_session_time
from dotenv import load_dotenv
import os

# Удаление мусорных логов
import logging
logging.getLogger("uvicorn.access").addFilter(
    lambda record: "com.chrome.devtools.json" not in record.getMessage()
)

load_dotenv('./config.env')

app = FastAPI()
templates = Jinja2Templates(directory="frontend")

@app.middleware("http")
async def update_session(request: Request, call_next):
    """При каждом запросе обновляет время жизни сессии, если она есть"""
    excluded_prefixes = {
        "/.well-known/appspecific/com.chrome.devtools.json",
        '/openapi.json',
        "/docs"
    }
    # url по которым сессия не обновляется
    path = request.url.path
    if path in excluded_prefixes:
        return await call_next(request)
    
    user_data = request.session.get('db_session_id')
    if user_data:
        if check_user_session(user_data):
            update_session_time(user_data)

    response = await call_next(request)
    return response

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv('session_key_open'), # ключ для шифровки кук
    session_cookie="session", # имя сессии
    max_age=int(os.getenv('session_time_life')), # сколько сессия будет жить в секундах
    same_site="lax", # защита от CSRF средняя
    https_only=False # будут ли куки отправлятся только по https
)

app.include_router(users_router)

@app.get("/", response_class=HTMLResponse)
async def get_main(request: Request):
    if (await cheak_session_current(False, request.session.get('db_session_id')))[0]:
        session = True
    else:
        session = False

    return templates.TemplateResponse(
        request,
        "main.html",
        {
        'date': 'динамические данные',
        'session': session
        }
    )

@app.get("/profile")
async def user_profile(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(
        request,
        "profile.html",
        {
        'session': True,
        'date': user,
        }
    )

@app.get("/logout")
async def user_profile(request: Request):
    if 'db_session_id' in request.session:
        del request.session['db_session_id']
    return RedirectResponse(url='http://127.0.0.1:8000', status_code=status.HTTP_302_FOUND)

from pydantic import BaseModel
import httpx

class TokenRequest(BaseModel):
    token: str

@app.post("/verify-recaptcha")
async def verify_recaptcha(data: TokenRequest):
    payload = {
        "secret": '6LfgNSAsAAAAAGd7vXOMw6XZORz73I0B8262uSg_',
        "response": data.token
    }

    async with httpx.AsyncClient() as client:
        r = await client.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
        result = r.json()

    # возвращает score 0.0–1.0
    success = result.get("success") and result.get("score", 0) >= 0.5

    return {
        "success": success,
        "score": result.get("score"),
        "action": result.get("action"),
        "raw": result
    }