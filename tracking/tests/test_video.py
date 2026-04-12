
from __future__ import annotations

import numpy as np
import pytest


def test_video_exposes_metadata_and_info(video_module, fake_cv2):
    """Объект Video должен возвращать основную информацию о потоке."""

    path = "/tmp/input.mp4"
    frames = [np.zeros((3, 4, 3), dtype=np.uint8), np.ones((3, 4, 3), dtype=np.uint8)]
    fake_cv2.register_capture(path, frames=frames, fps=25.0)

    video = video_module.Video(path)

    assert video.fps == 25.0
    assert video.frame_count == 2
    assert video.info == {
        "path": path,
        "fps": 25.0,
        "frame_count": 2,
        "width": 4,
        "height": 3,
        "duration_sec": 2 / 25.0,
    }


def test_video_raises_when_source_cannot_be_opened(video_module, fake_cv2):
    """Недоступный источник должен приводить к ValueError при создании Video."""

    fake_cv2.register_capture("/tmp/missing.mp4", frames=[], opened=False)

    with pytest.raises(ValueError, match="Cannot open video source"):
        video_module.Video("/tmp/missing.mp4")


def test_frame_at_sec_clamps_to_first_and_last_frames(video_module, fake_cv2):
    """Запрос кадра по времени должен ограничиваться доступным диапазоном."""

    path = "/tmp/clamped.mp4"
    frames = [
        np.full((2, 2, 3), 1, dtype=np.uint8),
        np.full((2, 2, 3), 2, dtype=np.uint8),
        np.full((2, 2, 3), 3, dtype=np.uint8),
    ]
    fake_cv2.register_capture(path, frames=frames, fps=10.0)
    video = video_module.Video(path)

    first_frame = video.frame_at_sec(-2.0)
    last_frame = video.frame_at_sec(10.0)

    assert np.array_equal(first_frame, frames[0])
    assert np.array_equal(last_frame, frames[-1])


def test_frame_at_idx_reads_requested_frame_and_restores_position(video_module, fake_cv2):
    """Чтение произвольного кадра не должно сбивать текущую позицию чтения."""

    path = "/tmp/seek.mp4"
    frames = [np.full((2, 2, 3), index, dtype=np.uint8) for index in range(4)]
    fake_cv2.register_capture(path, frames=frames, fps=10.0)
    video = video_module.Video(path)
    video._video.set(fake_cv2.CAP_PROP_POS_FRAMES, 1)

    frame = video.frame_at_idx(3)

    assert np.array_equal(frame, frames[3])
    assert video._video.get(fake_cv2.CAP_PROP_POS_FRAMES) == 1


def test_frame_at_idx_validates_bounds(video_module, fake_cv2):
    """Неверный индекс кадра должен вызывать ожидаемые исключения."""

    path = "/tmp/bounds.mp4"
    frames = [np.zeros((2, 2, 3), dtype=np.uint8) for _ in range(2)]
    fake_cv2.register_capture(path, frames=frames, fps=10.0)
    video = video_module.Video(path)

    with pytest.raises(ValueError, match="frame_index must be >= 0"):
        video.frame_at_idx(-1)

    with pytest.raises(IndexError, match="out of range"):
        video.frame_at_idx(2)


def test_frame_at_idx_raises_when_capture_cannot_read_frame(video_module, fake_cv2):
    """Ошибка чтения конкретного кадра должна передаваться наружу."""

    path = "/tmp/broken-read.mp4"
    frames = [np.zeros((2, 2, 3), dtype=np.uint8) for _ in range(2)]
    fake_cv2.register_capture(path, frames=frames, fps=10.0, failed_positions={1})
    video = video_module.Video(path)

    with pytest.raises(RuntimeError, match="Failed to read frame"):
        video.frame_at_idx(1)


def test_iter_frames_yields_indices_timestamps_and_frames(video_module, fake_cv2):
    """Последовательная итерация должна возвращать индекс, время и кадр."""

    path = "/tmp/iter.mp4"
    frames = [np.full((2, 2, 3), index, dtype=np.uint8) for index in range(3)]
    fake_cv2.register_capture(path, frames=frames, fps=5.0)
    video = video_module.Video(path)

    items = list(video.iter_frames(start=1))

    assert len(items) == 2
    assert items[0][0] == 1
    assert items[0][1] == 0.2
    assert np.array_equal(items[0][2], frames[1])
    assert items[1][0] == 2
    assert items[1][1] == 0.4
    assert np.array_equal(items[1][2], frames[2])


def test_close_releases_capture_and_prevents_further_use(video_module, fake_cv2):
    """После закрытия Video дальнейшее использование объекта должно быть запрещено."""

    path = "/tmp/closed.mp4"
    frames = [np.zeros((2, 2, 3), dtype=np.uint8)]
    fake_cv2.register_capture(path, frames=frames, fps=10.0)
    video = video_module.Video(path)
    capture = fake_cv2.created_captures[-1]

    video.close()

    assert capture.released is True
    with pytest.raises(RuntimeError, match="Video is closed"):
        video.frame_at_idx(0)
