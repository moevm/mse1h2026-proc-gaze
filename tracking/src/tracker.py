import json
import os
from pathlib import Path
from typing import Any, Optional

from src.video import Video


class Tracker:
    def __init__(self) -> None:
        self._data_dir = Path(os.environ.get("DATA_DIR", "/data")).resolve()

    def _resolve_path(self, relative_path: str) -> Path:
        """
        Преобразует относительный путь внутри DATA_DIR в абсолютный путь.

        Args:
            relative_path: относительный путь к входному файлу из payload.inputs,
                например ``videos/screen.mp4``.

        Returns:
            Абсолютный путь к файлу, расположенному внутри директории DATA_DIR.
        """
        p = Path(str(relative_path))
        if p.is_absolute() or ".." in p.parts:
            raise ValueError(f"Invalid path: {relative_path}")
        abs_path = (self._data_dir / p).resolve()
        abs_path.relative_to(self._data_dir)
        return abs_path

    def _to_relative_path(self, path: Path) -> str:
        return path.resolve().relative_to(self._data_dir).as_posix()

    def process_video(self, video: Video, out_dir: Optional[Path] = None) -> dict[str, str]:
        """
        Обрабатывает одно видео и сохраняет результаты в out_dir.

        Args:
            video: объект видео для обработки.
            out_dir: директория, в которую нужно сохранить результаты.

        Returns:
            Словарь с относительными путями до артефактов внутри DATA_DIR.
        """
        if out_dir is None:
            return {}

        out_dir = out_dir.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        info_path = out_dir / "video_info.json"
        info_path.write_text(json.dumps(video.info, ensure_ascii=False, indent=2), encoding="utf-8")

        traj_path = out_dir / "trajectory.json"
        if not traj_path.exists():
            traj_path.write_text("{}", encoding="utf-8")

        return {
            "video_info": self._to_relative_path(info_path),
            "trajectory": self._to_relative_path(traj_path),
        }

    def process_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Обрабатывает задание на трекинг.

        Ожидаемый формат payload:
            {
                "job_id": "123",
                "inputs": {
                    "screen_video": "uploads/screen.mp4",
                    "webcam_video": "uploads/webcam.mp4"
                }
            }

        Перед началом обработки в results/<job_id>/status.json записывается
        промежуточный статус IN_PROGRESS. После успешного завершения статус
        обновляется на DONE, а при ошибке — на FAILED.

        Формат результата:
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
        """
        job_id = str(payload["job_id"])
        inputs = payload.get("inputs") or {}

        screen_video_path = inputs.get("screen_video")
        webcam_video_path = inputs.get("webcam_video")

        if not screen_video_path or not webcam_video_path:
            raise KeyError("payload.inputs must contain both 'screen_video' and 'webcam_video'")

        out_dir = (self._data_dir / "results" / job_id).resolve()
        out_dir.relative_to(self._data_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        status_path = out_dir / "status.json"
        status_path.write_text(
            json.dumps(
                {
                    "job_id": job_id,
                    "status": "IN_PROGRESS",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        outputs: dict[str, Any] = {}

        try:
            for input_name, input_path in {
                "screen_video": screen_video_path,
                "webcam_video": webcam_video_path,
            }.items():
                video_path = self._resolve_path(str(input_path))
                source_out_dir = out_dir / input_name

                with Video(video_path) as v:
                    outputs[input_name] = self.process_video(v, out_dir=source_out_dir)

            result = {"job_id": job_id, "status": "DONE", "outputs": outputs}

            status_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            return result

        except Exception:
            status_path.write_text(
                json.dumps(
                    {
                        "job_id": job_id,
                        "status": "FAILED",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            raise