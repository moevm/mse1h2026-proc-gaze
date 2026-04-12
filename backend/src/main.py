import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.consumers import suspicious_consumer, calibration_consumer
from src.routers import recording_router, notification_router, suspicious_router, student_router
from src.util.broker import broker
from src.util.config import RMQ_URL
from src.util.database import engine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.start()
    logging.info(f"RabbitMQ broker started at url: {RMQ_URL}")

    yield
    await broker.close()
    logging.info("RabbitMQ broker stopped")
    await engine.dispose()
    logging.info("Connection to DB closed")


app = FastAPI(
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recording_router.router)
app.include_router(notification_router.router)
app.include_router(suspicious_router.router)
app.include_router(student_router.router)


@app.get("/")
async def root():
    return {"message": "API started"}
