import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from src.routers import recording_router, notification_router, suspicious_router, student_router
from src.consumers import suspicious_consumer  # noqa: F401
from src.util.broker import broker
from src.util.config import RMQ_URL
from src.util.database import engine, Base


# TODO: tmp function only for show second MSE-2026 result 
async def init_test_database():
    async with engine.begin() as conn:
        student_rows = await conn.execute(text('SELECT COUNT(*) FROM student'))
        
        if student_rows.scalar_one() == 0:
            logging.info("Table `student` is empty. Try to seed test students")
            
            await conn.execute(text("""
                INSERT INTO student(student_id, first_name, last_name, patronymic, "group")
                VALUES
                    ('285a1389-be7c-43eb-9d76-9afbfb715458', 'Максим', 'Берлет', 'Валерьевич', '3385'),
                    ('1de37e3f-1a66-44a7-8bb3-adf1c5565dd5', 'Александр', 'Рудаков', 'Леонидович', '3384');
            """))
            
            logging.info("Table `student` initialize done")
        else:
            logging.info("Table `student` is not empty. Skip")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        logging.info(f"Creating DB {app}")
        await conn.run_sync(Base.metadata.create_all)
        
    await init_test_database()
    
    while True:
        try:
            await broker.start()
            logging.info(f"RabbitMQ broker started at url: {RMQ_URL}")
            break
        except Exception as e:
            logging.warning(f"RabbitMQ not ready: {e}. Retry in 2s...")
            await asyncio.sleep(2)
    yield
    await broker.close()
    logging.info("RabbitMQ broker stopped")
    await engine.dispose()
    logging.info("Connection to DB closed")


app = FastAPI(
    lifespan=lifespan
)

app.include_router(recording_router.router)
app.include_router(notification_router.router)
app.include_router(suspicious_router.router)
app.include_router(student_router.router)


@app.get("/")
async def root():
    return {"message": "API started"}
