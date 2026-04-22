import logging
import time
import requests
from config import BACKEND_URL

logger = logging.getLogger(__name__)


def wait_for_backend_ready() -> bool:
    logger.info(f"Waiting for backend at {BACKEND_URL}")

    for _ in range(10):
        try:
            response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
            if response.status_code == 200:
                logger.info("Backend is ready!")
                return True
        except requests.exceptions.RequestException:
            logger.info(f"Backend not ready yet")
        time.sleep(1)

    raise Exception("Backend is not ready")
