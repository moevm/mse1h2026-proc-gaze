import logging
from typing import Generator
import pytest
from environment import test_environment
from database import clear_db

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_env() -> Generator[None, None, None]:
    """Set up test environment once for all tests in the session."""
    logger.info("Setting up test environment")
    with test_environment():
        yield
    logger.info("Test environment teardown complete")


@pytest.fixture(autouse=True)
def clean_database():
    clear_db()
    yield
