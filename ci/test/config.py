import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = "http://localhost:8000"
DATABASE_URL = os.getenv("DATABASE_URL")\
    .replace("db:5432", "localhost:5432")\
    .replace("postgresql+asyncpg://", "postgresql://")
TEST_LOGS_DIR = os.getenv("TEST_LOGS_DIR")
DOCKER_COMPONENTS = ["backend", "tracker", "frontend", "db", "rabbitmq"]
