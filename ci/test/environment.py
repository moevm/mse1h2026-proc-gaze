"""
Test environment setup and utilities for integration testing.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from database import clear_db
from docker import start_docker, stop_docker, capture_logs
from backend import wait_for_backend_ready

logger = logging.getLogger(__name__)


@contextmanager
def test_environment() -> Generator[None, None, None]:
    logger.info("Starting test environment")
    start_docker()
    wait_for_backend_ready()
    clear_db()
    
    try:
        yield
    finally:
        logger.info("Stopping test environment")
        capture_logs()
        stop_docker()
