import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.routers import recording_router, notification_router, suspicious_router, student_router
from src.consumers import suspicious_consumer  # noqa: F401
from src.util.broker import broker
from src.util.config import RMQ_URL
from src.util.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        logging.info(f"Creating DB {app}")
        await conn.run_sync(Base.metadata.create_all)
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
