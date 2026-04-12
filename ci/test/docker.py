import logging
import os
import subprocess
from typing import List, Optional

from config import DOCKER_COMPONENTS, TEST_LOGS_DIR

logger = logging.getLogger(__name__)


def run_command(cmd: List[str],
                expect_ok: bool = True,
                timeout: int = 60,
                capture_output: bool = False) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=capture_output, timeout=timeout, text=True)
    if expect_ok and result.returncode != 0:
        raise Exception("Failed to execute command")
    return result


def start_docker() -> None:
    logger.info("Starting Docker compose services")
    run_command(["docker", "compose", "up", "-d"], timeout=60)


def stop_docker() -> None:
    logger.info("Stopping Docker compose services")
    run_command(["docker", "compose", "stop"], expect_ok=False)
    run_command(["docker", "compose", "rm", "-f"], expect_ok=False)


def capture_logs() -> None:
    os.makedirs(TEST_LOGS_DIR, exist_ok=True)

    for component in DOCKER_COMPONENTS:
        log_file_path = os.path.join(TEST_LOGS_DIR, f"{component}.log")
        logger.info(f"Capturing logs for {component}")

        try:
            result = run_command(
                ["docker", "compose", "logs", component],
                expect_ok=False,
                capture_output=True,
            )
            logs = result.stdout + result.stderr
            with open(log_file_path, "w") as f:
                f.write(logs)
        except Exception as e:
            logger.error(f"Failed to capture logs for {component}: {e}")
