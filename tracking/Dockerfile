FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG MODELS_URL
RUN pip install --no-cache-dir openvino-dev[onnx] && \
    wget ${MODELS_URL} -O intel.tar.gz && \
    tar -xzf intel.tar.gz -C / && \
    rm intel.tar.gz

COPY main.py .
COPY src ./src

ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]