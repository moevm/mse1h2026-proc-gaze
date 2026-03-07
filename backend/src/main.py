from fastapi import FastAPI
from .routers import recording_router, notification_router, suspicious_router, student_router
from .database import engine, Base

app = FastAPI()

app.include_router(recording_router.router)
app.include_router(notification_router.router)
app.include_router(suspicious_router.router)
app.include_router(student_router.router)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "API started"}
