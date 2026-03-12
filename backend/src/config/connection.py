import logging
from functools import wraps

from starlette import status
from starlette.exceptions import HTTPException

from config.database import SessionLocal


def connection(method):
    @wraps(method)
    async def wrapper(*args, **kwargs):
        async with SessionLocal() as session:
            try:
                # Явно не открываем транзакции, так как они уже есть в контексте
                return await method(*args, session=session, **kwargs)
            except HTTPException as e: # TODO: нужно обрабатывать различные ошибки в зависимости от типа и оборачивать в HTTPException
                logging.error(e.detail)
                raise e
            except Exception as e:
                logging.error(e.detail)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"Internal server error: {str(e)}")
            finally:
                await session.rollback() # Откатываем сессию при ошибке
                await session.close()  # Закрываем сессию

    return wrapper