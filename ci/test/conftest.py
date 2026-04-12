import logging
from typing import Generator
import pytest
from environment import test_environment

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_env() -> Generator[None, None, None]:
    """Set up test environment once for all tests in the session."""
    logger.info("Setting up test environment")
    with test_environment():
        yield
    logger.info("Test environment teardown complete")