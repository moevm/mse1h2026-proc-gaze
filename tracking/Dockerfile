FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir openvino-dev[onnx] && \
    omz_downloader --name face-detection-0200 -o /intel && \
    omz_downloader --name landmarks-regression-retail-0009 -o /intel && \
    omz_downloader --name facial-landmarks-98-detection-0001 -o /intel && \
    omz_downloader --name head-pose-estimation-adas-0001 -o /intel && \
    omz_downloader --name gaze-estimation-adas-0002 -o /intel

COPY main.py .
COPY src ./src

ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]