from __future__ import annotations

import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.tracker import Tracker
from src.video import Video


def write_test_video(path, n_frames=3, width=10, height=10, fps=30.0):
    """Создает маленький тестовый видеофайл."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    for i in range(n_frames):
        writer.write(np.full((height, width, 3), (i * 30) % 256, dtype=np.uint8))
    writer.release()


@pytest.fixture
def tracker(tmp_path):
    """Создает реальный Tracker с временной директорией данных."""
    os.environ["DATA_DIR"] = str(tmp_path)
    return Tracker()
