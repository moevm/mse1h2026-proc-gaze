from fastapi import FastAPI, UploadFile, HTTPException
from routers import upload_router

app = FastAPI()


app.include_router(upload_router.router)

@app.get("/")
async def root():
    return {"message": "API started"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)