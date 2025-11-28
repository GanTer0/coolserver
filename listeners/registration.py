from fastapi import APIRouter, Request, HTTPException,  status
from fastapi.templating import Jinja2Templates
from database.main import insert_table_user, check_user_exists, insert_table_user_session, check_user_session

from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from fastapi.responses import RedirectResponse
import secrets

from dotenv import load_dotenv
import os

load_dotenv('.\config.env')

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
            # Сохраняем данные пользователя
            if not check_user_exists(user_info['email']):
                id = insert_table_user(user_info['email'], user_info.get('name'), user_info.get('family_name'), user_info.get('picture'))

            session_id = secrets.token_urlsafe(40)
            print(id)
            insert_table_user_session(session_id, id, {'data': 'cool'})
            request.session['session_id'] = session_id

            return RedirectResponse(url='http://127.0.0.1:8000/profile', status_code=status.HTTP_302_FOUND)


        
        raise HTTPException(400, "Email not verified")
        
    except Exception as e:
        print(f"Auth error: {str(e)}")
        raise HTTPException(400, f"Authentication failed: {str(e)}")