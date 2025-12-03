from fastapi import FastAPI, Request, HTTPException
from listeners.registration import users_router
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Depends
from servis.auth import get_current_user
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
    excluded_prefixes = {
        "/.well-known/appspecific/com.chrome.devtools.json",
        # "/robots.txt",
        # "/authentication/google/callback",   # ← редиректы OAuth
        # "/authentication/google/authorize",
        '/openapi.json',
        "/docs",             # Swagger
    }

    path = request.url.path
    if path in excluded_prefixes:
        # Просто пропускаем, в БД не лезем
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
    max_age=3600, # сколько сессия будет жить в секундах
    same_site="lax", # защита от CSRF средняя
    https_only=False, # будут ли куки отправлятся только по https
)

# session_cookie = request.cookies.get("session")
    # if not session_cookie:
    #     return None

    # Это ровно то, что делает SessionMiddleware внутри
    # session_data = SessionMiddleware.load_session_from_cookie(
    #         session_cookie,
    #         secret_key=os.getenv('session_key_open'),
    #         session_cookie="session",   # должно совпадать с твоим add_middleware
    #     )
    # print(session_data)

    # print('Запрос пришёл!')  # Это уже будет печататься
    # print(session_cookie)
    # if check_user_session(session_cookie):
    #     update_session_time(session_cookie)
    #     print('время обновлено')  # Это уже будет печататься


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

# @app.get("/.well-known/appspecific/com.chrome.devtools.json")
# async def shut_up_chrome():
#     raise HTTPException(status_code=404)