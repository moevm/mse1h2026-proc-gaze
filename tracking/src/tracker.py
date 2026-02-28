import json
import os
from pathlib import Path
from typing import Any, Optional

from src.video import Video


class Tracker:
    def __init__(self) -> None:
        self._data_dir = Path(os.environ.get("DATA_DIR", "/data")).resolve()

    def _resolve_key(self, key: str) -> Path:
        p = Path(str(key))
        if p.is_absolute() or ".." in p.parts:
            raise ValueError(f"Invalid key: {key}")
        abs_path = (self._data_dir / p).resolve()
        abs_path.relative_to(self._data_dir)
        return abs_path

    def _to_key(self, path: Path) -> str:
        return path.resolve().relative_to(self._data_dir).as_posix()

    def process_video(self, video: Video, out_dir: Optional[Path] = None) -> dict[str, str]:
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
            "video_info": self._to_key(info_path),
            "trajectory": self._to_key(traj_path),
        }

    def process_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = str(payload["job_id"])
        inputs = payload.get("inputs") or {}

        in_key = inputs.get("screen") or inputs.get("video")
        if not in_key:
            raise KeyError("payload.inputs must contain 'screen' or 'video'")

        video_path = self._resolve_key(str(in_key))
        out_dir = (self._data_dir / "results" / job_id).resolve()
        out_dir.relative_to(self._data_dir)

        with Video(video_path) as v:
            outputs = self.process_video(v, out_dir=out_dir)

        return {"job_id": job_id, "status": "DONE", "outputs": outputs}