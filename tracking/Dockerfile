FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0t64=2.84.4-3~deb13u2 \
    libsm6=2:1.2.6-1 \
    libxext6=2:1.3.4-1+b3 \
    libxrender1=1:0.9.12-1 \
    wget=1.25.0-2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG MODELS_URL
RUN pip install --no-cache-dir "openvino-dev[onnx]==2024.6.0" && \
    wget ${MODELS_URL} -O intel.tar.gz && \
    tar -xzf intel.tar.gz -C / && \
    rm intel.tar.gz

COPY main.py .
COPY src ./src

ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]