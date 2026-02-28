import cv2
import numpy as np
from pathlib import Path
from typing import Iterator, Optional


class Video:
    def __init__(self, video_path: str | Path) -> None:
        # video_path - локальный путь | url
        self._path = video_path
        self._video: Optional[cv2.VideoCapture] = cv2.VideoCapture(str(self._path))
        if self._video is None or not self._video.isOpened():
            self._video = None
            raise ValueError(f"Cannot open video source: {self._path}")

        self._fps: float = float(self._video.get(cv2.CAP_PROP_FPS) or 0.0)
        self._frame_count: int = int(self._video.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        self._width: int = int(self._video.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        self._height: int = int(self._video.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        if self._frame_count > 0 and self._fps > 0:
            self._duration_sec: Optional[float] = self._frame_count / self._fps
        else:
            self._duration_sec = None

    def _ensure_open(self) -> cv2.VideoCapture:
        if self._video is None:
            raise RuntimeError("Video is closed.")
        return self._video

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

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def frame_count(self) -> int:
        return self._frame_count

    def frame_at_sec(self, second: float) -> np.ndarray:
        """Return the video frame corresponding to the given time (in seconds)."""
        if self._fps <= 0:
            raise ValueError("FPS is unknown (0). Can't seek by seconds reliably.")

        second = max(0.0, float(second))

        frame_index = int(second * self._fps)

        if self._frame_count > 0:
            frame_index = min(frame_index, self._frame_count - 1)

        return self.frame_at_idx(frame_index)

    def frame_at_idx(self, frame_index: int) -> np.ndarray:
        """Return the video frame with the given frame index."""
        if frame_index < 0:
            raise ValueError("frame_index must be >= 0")
        if 0 < self._frame_count <= frame_index:
            raise IndexError(f"frame_index {frame_index} out of range (frame_count={self._frame_count})")

        cap = self._ensure_open()
        prev = int(cap.get(cv2.CAP_PROP_POS_FRAMES) or 0)

        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()
        finally:
            cap.set(cv2.CAP_PROP_POS_FRAMES, prev)

        if not ret or frame is None:
            raise RuntimeError(f"Failed to read frame at index={frame_index} from {self._path}")

        return frame

    def iter_frames(self, start: int = 0) -> Iterator[tuple[int, Optional[float], np.ndarray]]:
        """Iterate frames sequentially starting from the given frame index."""
        if start < 0:
            raise ValueError("start must be >= 0")

        cap = self._ensure_open()
        cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        idx = start

        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            t = (idx / self._fps) if self._fps > 0 else None
            yield idx, t, frame
            idx += 1

    def __iter__(self) -> Iterator[np.ndarray]:
        for _, _, frame in self.iter_frames(start=0):
            yield frame

    def close(self) -> None:
        """Release the underlying video capture resource."""
        if self._video is not None:
            try:
                self._video.release()
            finally:
                self._video = None

    def __enter__(self) -> "Video":
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass