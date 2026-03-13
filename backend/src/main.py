import uvicorn
from fastapi import FastAPI

from routers import recording_router, notification_router, suspicious_router, student_router

app = FastAPI()

app.include_router(recording_router.router)
app.include_router(notification_router.router)
app.include_router(suspicious_router.router)
app.include_router(student_router.router)

@app.get("/")
async def root():
    return {"message": "API started"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", log_level="info")