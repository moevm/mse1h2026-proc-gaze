import logging
from functools import wraps

from starlette import status
from starlette.exceptions import HTTPException

from src.util.database import SessionLocal


def connection(method):
    @wraps(method)
    async def wrapper(*args, **kwargs):
        async with SessionLocal() as session:
            try:
                return await method(*args, session=session, **kwargs)
            except HTTPException as e:  # TODO: нужно обрабатывать различные ошибки в зависимости от типа и оборачивать в HTTPException
                logging.error(e.detail)
                raise
            except Exception as e:
                logging.error(e)
                await session.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"Internal server error: {str(e)}")
            finally:
                await session.close()

    return wrapper
