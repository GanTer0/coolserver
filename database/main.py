# database/main.py
from sqlalchemy import create_engine, MetaData, Table, exists, select
from servis.log import logger

from dotenv import load_dotenv
import os

load_dotenv('.\config.env')

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
            
            logger.info(f"Пользователь успешно добавлен с ID: {user_id}")
            return user_id
            
        except Exception as e:
            logger.error(f'Ошибка при добавлении пользователя: {e}')
            conn.rollback()
            return None

def check_user_exists(email: str) -> bool:
    """Проверяет существование пользователя по email"""
    with engine.connect() as conn:
        try:
            stmt = select(exists().where(test_user.c.email == email))
            result = conn.execute(stmt)
            return result.scalar()
        except Exception as e:
            print(f'Ошибка проверки пользователя: {e}')
            return False
        
def insert_table_user_session(session_id: str, user_id: str, session_data: dict):
    """Добавляет сесиию"""
    print('из бд')
    print(session_id)
    print(len(session_id))
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
            logger.error('Возникла ошибка', e)
            return False
        
def check_user_session(session_id: str) -> bool:
    """Проверяет существование сессии"""
    with engine.connect() as conn:
        try:
            stmt = select(exists().where(test_user_session.c.session_id == session_id))
            result = conn.execute(stmt)
            return result.scalar()
        except Exception as e:
            print(f'Ошибка проверки пользователя: {e}')
            return False