import logging
from typing import Any

logger = logging.getLogger(__name__)


async def handle_tracking_result(payload: dict[str, Any]) -> None:
    """
    Обработка результата от сервиса трекинга.

    Формат payload (успех):
        {
            "job_id": "123",
            "status": "DONE",
            "outputs": {
                "screen_video": {
                    "video_info": "results/123/screen_video/video_info.json",
                    "trajectory": "results/123/screen_video/trajectory.json"
                },
                "webcam_video": {
                    "video_info": "results/123/webcam_video/video_info.json",
                    "trajectory": "results/123/webcam_video/trajectory.json"
                }
            }
        }

    Формат payload (ошибка):
        {
            "job_id": "123",
            "status": "FAILED",
            "error": "traceback string"
        }
    """
    job_id = payload.get("job_id")
    status = payload.get("status")

    if status == "DONE":
        outputs = payload.get("outputs", {})
        logger.info("Job %s completed. Outputs: %s", job_id, list(outputs.keys()))
    elif status == "FAILED":
        error = payload.get("error", "unknown error")
        logger.error("Job %s failed: %s", job_id, error)
    else:
        logger.warning("Job %s returned unknown status: %s", job_id, status)
