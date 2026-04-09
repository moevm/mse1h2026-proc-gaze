FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src
COPY ./migration ./migration
COPY ./alembic.ini ./alembic.ini

EXPOSE 8000
CMD alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000