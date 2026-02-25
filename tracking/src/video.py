import cv2
import numpy as np
from pathlib import Path

from typing import Iterator


class Video:
    def __init__(self, video_path: str | Path) -> None:
        # video_path - локальный путь | url
        self._path = video_path
        self._video: cv2.VideoCapture = cv2.VideoCapture(self._path)

        self._fps: float = 0.0
        self._frame_count: int = 0
        self._width: int = 0
        self._height: int = 0
        if self._frame_count > 0 and self._fps > 0:
            self._duration_sec: float = self._frame_count / self._fps
        else:
            self._duration_sec = None

    @property
    def info(self) -> dict:
        return {
            "path": str(self._path),
            "fps": self._fps,
            "frame_count": self._frame_count,
            "width": self._width,
            "height": self._height,
            "duration_sec": self._duration_sec,
        }

    def frame_at_sec(self, second: float) -> np.ndarray:
        pass

    def frame_at_idx(self, frame_index: int) -> np.ndarray:
        pass

    def __iter__(self) -> Iterator:
        pass

    def __del__(self) -> None:
        pass
