from fastapi import Request, HTTPException
from database.main import check_user_session

async def get_current_user(request: Request):
    user_data = request.session.get('session_id')

    if check_user_session(user_data):
        return user_data
    else:
        raise HTTPException(status_code=303, headers={"Location": "/authentication/login"})