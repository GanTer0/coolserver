from fastapi import APIRouter, Request, HTTPException,  status
from fastapi.templating import Jinja2Templates
from database.main import insert_table_user, check_user_exists, insert_table_user_session, check_user_session_by_id, update_user_session_simple, update_user_session_current
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from fastapi.responses import RedirectResponse
import secrets
from datetime import datetime, timezone, timedelta
from servis.auth import cheak_session_current
from servis.log import logger

from dotenv import load_dotenv
import os

load_dotenv('./config.env')
session_time_life = int(os.getenv('session_time_life'))

users_router = APIRouter(prefix="/authentication", tags=["users"])
templates = Jinja2Templates(directory="frontend")

oauth = OAuth()

oauth.register(
    name='google',
    client_id = os.getenv('google_oauth_client_id'),
    client_secret = os.getenv('google_oauth_client_secret'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@users_router.get("/login")
async def login_via_google(request: Request):
    redirect_uri = "http://127.0.0.1:8000/authentication/auth"
    
    # принудительный выбор аккаунта
    # authorization_kwargs = {'prompt': 'select_account'}
    
    return await oauth.google.authorize_redirect(
        request, 
        redirect_uri,
    )
    # **authorization_kwargs

@users_router.get("/auth", name="auth_callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')

        if user_info and user_info.get('email_verified'):
            user, user_id = check_user_exists(user_info['email'])
            logger.info(f'Пользователь, {user}')

            # Если пользователя нет в бд
            if not user:
                user_id = insert_table_user(user_info['email'], user_info.get('name'), user_info.get('family_name'), user_info.get('picture'))
            is_session, id_session = await cheak_session_current(True, user_id)
            new_session_id = secrets.token_urlsafe(60)
            # Если сессия существует и её время не вышло
            if is_session:
                update_user_session_simple(id_session, new_session_id)

            insert_table_user_session(new_session_id, user_id, {'data': 'cool'})
            request.session['db_session_id'] = new_session_id
            return RedirectResponse(url='http://127.0.0.1:8000/profile', status_code=status.HTTP_302_FOUND)

        raise HTTPException(400, "Email not verified")
        
    except Exception as e:
        print(f"Auth error: {str(e)}")
        raise HTTPException(400, f"Authentication failed: {str(e)}")
    