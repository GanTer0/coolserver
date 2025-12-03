# database/main.py
from sqlalchemy import create_engine, MetaData, Table, exists, select, update
from servis.log import logger

from sqlalchemy.types import TIMESTAMP

from datetime import datetime, timezone
from dotenv import load_dotenv
import os

load_dotenv('./config.env')

engine = create_engine(
    url=os.getenv('database_url'),
    pool_size=5,
    max_overflow=10
)
metadata = MetaData()

# Отражаем таблицу
test_user = Table('test', metadata, autoload_with=engine)
test_user_session = Table('test_session', metadata, autoload_with=engine)

def insert_table_user(email: str, name: str, family_name: str, avatar: str) -> int:
    """Добавляет пользователя и возвращает его ID"""
    with engine.connect() as conn:
        try:
            # Используем RETURNING с вашим стилем
            result = conn.execute(
                test_user.insert().returning(test_user.c.id).values(
                    email=email,
                    name=name,
                    family_name=family_name,
                    avatar=avatar
                )
            )
            
            # Получаем ID
            user_id = result.scalar()
            conn.commit()
            
            logger.info(f"Пользователь успешно добавлен")
            return user_id
            
        except Exception as e:
            logger.error(f'Ошибка при добавлении пользователя: {e}')
            conn.rollback()
            return None

def check_user_exists(email: str) -> tuple[bool, int | None]:
    """Проверяет существование почты и возвращает (exists, user_id)"""
    with engine.connect() as conn:
        try:
            stmt = select(test_user.c.id).where(test_user.c.email == email)
            result = conn.execute(stmt)
            user_id = result.scalar()
            return (user_id is not None, user_id)
        except Exception as e:
            logger.error(f'Ошибка проверки пользователя: {e}')
            return (False, None)

def insert_table_user_session(
        session_id: str,
        user_id: str,
        session_data: dict,
        created_at: TIMESTAMP = None,
        last_seen_at: TIMESTAMP = None
        ) -> bool:
    """Добавляет сесиию"""
    with engine.connect() as conn:
        try:
            conn.execute(
                test_user_session.insert().values(
                    session_id=session_id,
                    user_id = user_id,
                    session_data = session_data
                )
            )
            conn.commit()
            logger.info("Сессия добавлена")
            return True
        except Exception as e:
            logger.error('Возникла ошибка при добавление сессии', e)
            return False
        
def check_user_session(session_id: str) -> bool:
    """Проверяет существование сессии"""
    with engine.connect() as conn:
        try:
            stmt = select(exists().where(test_user_session.c.session_id == session_id))
            result = conn.execute(stmt)
            return result.scalar()
        except Exception as e:
            logger.error(f'Ошибка проверки сессии, по session_id: {e}')
            return False

from datetime import datetime
from typing import Tuple, Optional

def check_user_session_by_id(user_id: bool, id: str) -> Tuple[bool, Optional[str], Optional[datetime]]:
    """
    Проверяет наличие текущей сессии пользователя (is_current = True)
    Возвращает: (exists, session_id, last_seen_at)
    """
    with engine.connect() as conn:
        try:
            if user_id:
                stmt = select(
                    test_user_session.c.session_id,
                    test_user_session.c.last_seen_at
                ).where(
                    (test_user_session.c.user_id == id) &
                    (test_user_session.c.is_current == True)
                ).limit(1)  # на всякий случай, вдруг дубли
            else:
                stmt = select(
                    test_user_session.c.session_id,
                    test_user_session.c.last_seen_at
                ).where(
                    (test_user_session.c.session_id == id) &
                    (test_user_session.c.is_current == True)
                ).limit(1)
            row = conn.execute(stmt).mappings().one_or_none()

            if row:
                return True, row["session_id"], row["last_seen_at"]
            else:
                return False, None, None

        except Exception as e:
            logger.error(f'Ошибка проверки текущей сессии user_id={user_id}: {e}')
            return False, None, None
        
def update_user_session_simple(old_session_id: str, new_session_id: str) -> bool:
    """Обновляет session_id на новое значение"""
    with engine.connect() as conn:
        try:
            stmt = (
                update(test_user_session)
                .where(test_user_session.c.session_id == old_session_id)
                .values(session_id=new_session_id)
            )
            
            result = conn.execute(stmt)
            conn.commit()
            
            return result.rowcount > 0
                
        except Exception as e:
            logger.error(f'Ошибка обновления айди сессии {old_session_id} -> {new_session_id}: {e}')
            conn.rollback()
            return False


def update_session_time(session_id) -> bool:
    """Обновляет последнее время активности в сесиии"""
    with engine.connect() as conn:
        try:
            stmt = (
                update(test_user_session)
                .where(test_user_session.c.session_id == session_id)
                .values(last_seen_at=datetime.now(timezone.utc))
            )
            
            result = conn.execute(stmt)
            conn.commit()
            if result.rowcount > 0:
                logger.info('Время жизни сессии обновлено')
                return True
            return False
                
        except Exception as e:
            logger.error(f'Ошибка обновления времени сессии {e}')
            conn.rollback()
            return False
        
def update_user_session_current(session_id: str) -> bool:
    """Обновляет действительность сессии по айди сессии"""
    with engine.connect() as conn:
        try:
            stmt = (
                update(test_user_session)
                .where(test_user_session.c.session_id == session_id)
                .values(is_current=False)
            )
            
            result = conn.execute(stmt)
            conn.commit()
            
            return result.rowcount > 0
                
        except Exception as e:
            logger.error(f'Ошибка обновления действености сессии: {e}')
            conn.rollback()
            return False
        

def get_UserId_by_SessionId(session_id: str) -> str:
    """Получает userid by sessionId"""
    with engine.connect() as conn:
        try:
            stmt = select(
                test_user_session.c.user_id,
            ).where(
                (test_user_session.c.session_id == session_id) &
                (test_user_session.c.is_current == True)
            ).limit(1)  # на всякий случай, вдруг дубли
    
            row = conn.execute(stmt).mappings().one_or_none()

            if row:
                return row["user_id"]
            else:
                return False

        except Exception as e:
            logger.error(f'Ошибка получения айди по сессион айди: {e}')


def get_info_user(user_id: str) -> tuple:
    """Получает Имя Фамилию Почту аватарку дату регистарции по user_id"""
    with engine.connect() as conn:
        try:
            stmt = select(
                test_user.c.name,
                test_user.c.family_name,
                test_user.c.email,
                test_user.c.avatar,
                test_user.c.date
            ).where(
                (test_user.c.id == user_id) 
            ).limit(1)  # на всякий случай, вдруг дубли
    
            row = conn.execute(stmt).mappings().one_or_none()

            if row:
                return row
            else:
                return False

        except Exception as e:
            logger.error(f'Ошибка получения данных пользователя: {e}')