from fastapi import Request, HTTPException
from database.main import check_user_session_by_id, get_UserId_by_SessionId, get_info_user, update_user_session_current
from datetime import datetime, timezone, timedelta
from servis.log import logger

from dotenv import load_dotenv
import os

load_dotenv('./config.env')
session_time_life = int(os.getenv('session_time_life'))

async def cheak_session_current(is_user_id: bool, id: str) -> bool:
    """ Проверят действительность сессии есть ли в бд и не вышло ли время сесиии """
    session, id_session, last_active = check_user_session_by_id(is_user_id, id)
    if session:
        now = datetime.now(timezone.utc)
        last_active_utc = last_active.astimezone(timezone.utc)
        time_difference = now - last_active_utc

        if time_difference <= timedelta(seconds=session_time_life):
            return True, id_session
        else:
            logger.info('Время сессии вышло')
            update_user_session_current(id_session)
            return False, id_session
    else:
        return False, False

async def get_current_user(request: Request):
    user_data = request.session.get('db_session_id')

    if user_data and (await cheak_session_current(False, user_data))[0]:
        return get_info_user(get_UserId_by_SessionId(user_data))
    else:
        print('сессия не найдена', user_data)
        raise HTTPException(status_code=303, headers={"Location": "/authentication/login"})