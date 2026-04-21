FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg=7:7.1.3-0+deb13u1 \
    libglib2.0-0t64=2.84.4-3~deb13u2 \
    libsm6=2:1.2.6-1 \
    libxext6=2:1.3.4-1+b3 \
    libxrender1=1:0.9.12-1 \
    wget=1.25.0-2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir \
    --default-timeout=1000 \
    --retries=5 \
    -r requirements.txt

ARG MODELS_URL=https://raw.githubusercontent.com/jcdkiki/gaze-models/v2
RUN set -eux; \
    models_url="${MODELS_URL%/}"; \
    mkdir -p /models; \
    wget -O /models/resnet.tar.gz "${models_url}/resnet.tar.gz"; \
    wget -O /models/intel.tar.gz "${models_url}/models.tar.gz"; \
    tar -xzf /models/resnet.tar.gz -C /models/ && \
    tar -xzf /models/intel.tar.gz -C /models/ && \
    mv /models/models /models/intel && \
    rm -f /models/resnet.tar.gz /models/intel.tar.gz

COPY main.py .
COPY src ./src

ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]

FROM base AS test

RUN pip install --no-cache-dir pytest-asyncio
COPY tests ./tests

CMD ["python", "-m", "pytest", "tests", "-v"]

FROM base AS runtime
