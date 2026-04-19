from __future__ import annotations

import numpy as np
import pytest

from conftest import write_test_video
from src.video import Video


def test_video_exposes_metadata_and_info(tmp_path):
    """Объект Video должен возвращать основную информацию о потоке."""

    path = str(tmp_path / "input.mp4")
    write_test_video(path, n_frames=2, width=20, height=20, fps=25.0)

    video = Video(path)

    assert video.fps == pytest.approx(25.0, abs=1.0)
    assert video.frame_count == 2
    assert video.width == 20
    assert video.height == 20
    assert video.duration_sec is not None
    assert video.info["path"] == path
    video.close()


def test_video_raises_when_source_cannot_be_opened():
    """Недоступный источник должен приводить к ValueError при создании Video."""

    with pytest.raises(ValueError, match="Cannot open video source"):
        Video("/tmp/nonexistent_video_file.mp4")


def test_frame_at_sec_clamps_to_first_and_last_frames(tmp_path):
    """Запрос кадра по времени должен ограничиваться доступным диапазоном."""

    path = str(tmp_path / "clamped.mp4")
    write_test_video(path, n_frames=3, fps=10.0)
    video = Video(path)

    first_frame = video.frame_at_sec(-2.0)
    last_frame = video.frame_at_sec(10.0)

    assert first_frame is not None
    assert last_frame is not None
    assert not np.array_equal(first_frame, last_frame)
    video.close()


def test_frame_at_sec_returns_correct_frame(tmp_path):
    """Запрос кадра по точному времени должен возвращать соответствующий кадр."""

    path = str(tmp_path / "exact.mp4")
    write_test_video(path, n_frames=10, fps=10.0)
    video = Video(path)

    frame_0 = video.frame_at_sec(0.0)
    frame_5 = video.frame_at_sec(0.5)

    assert frame_0 is not None
    assert frame_5 is not None
    video.close()


def test_frame_at_idx_reads_requested_frame(tmp_path):
    """Чтение произвольного кадра должно возвращать корректные данные."""

    path = str(tmp_path / "seek.mp4")
    write_test_video(path, n_frames=4, fps=10.0)
    video = Video(path)

    frame0 = video.frame_at_idx(0)
    frame3 = video.frame_at_idx(3)

    assert frame0 is not None
    assert frame3 is not None
    assert not np.array_equal(frame0, frame3)
    video.close()


def test_frame_at_idx_validates_bounds(tmp_path):
    """Неверный индекс кадра должен вызывать ожидаемые исключения."""

    path = str(tmp_path / "bounds.mp4")
    write_test_video(path, n_frames=2, fps=10.0)
    video = Video(path)

    with pytest.raises(ValueError, match="frame_index must be >= 0"):
        video.frame_at_idx(-1)

    with pytest.raises(IndexError, match="out of range"):
        video.frame_at_idx(2)

    video.close()


def test_frame_at_idx_does_not_affect_sequential_read(tmp_path):
    """Чтение по индексу не должно сбивать последовательное чтение."""

    path = str(tmp_path / "noseek.mp4")
    write_test_video(path, n_frames=5, fps=10.0)
    video = Video(path)

    items_before = list(video.iter_frames(start=0))
    _ = video.frame_at_idx(3)
    items_after = list(video.iter_frames(start=0))

    assert len(items_before) == len(items_after) == 5
    video.close()


def test_iter_frames_yields_indices_timestamps_and_frames(tmp_path):
    """Последовательная итерация должна возвращать индекс, время и кадр."""

    path = str(tmp_path / "iter.mp4")
    write_test_video(path, n_frames=3, fps=5.0)
    video = Video(path)

    items = list(video.iter_frames(start=1))

    assert len(items) == 2
    assert items[0][0] == 1
    assert items[0][1] == pytest.approx(0.2)
    assert items[1][0] == 2
    assert items[1][1] == pytest.approx(0.4)
    video.close()


def test_iter_frames_from_start(tmp_path):
    """Итерация с начала должна вернуть все кадры."""

    path = str(tmp_path / "full.mp4")
    write_test_video(path, n_frames=5, fps=10.0)
    video = Video(path)

    items = list(video.iter_frames(start=0))

    assert len(items) == 5
    assert [i for i, _, _ in items] == [0, 1, 2, 3, 4]
    video.close()


def test_iter_frames_rejects_negative_start(tmp_path):
    """Отрицательный start должен вызывать ValueError."""

    path = str(tmp_path / "neg.mp4")
    write_test_video(path, n_frames=2, fps=10.0)
    video = Video(path)

    with pytest.raises(ValueError, match="start must be >= 0"):
        list(video.iter_frames(start=-1))

    video.close()


def test_dunder_iter_yields_all_frames(tmp_path):
    """__iter__ должен вернуть все кадры как ndarray."""

    path = str(tmp_path / "dunder.mp4")
    write_test_video(path, n_frames=4, fps=10.0)
    video = Video(path)

    frames = list(video)

    assert len(frames) == 4
    for f in frames:
        assert isinstance(f, np.ndarray)
    video.close()


def test_len_returns_frame_count(tmp_path):
    """__len__ должен возвращать количество кадров."""

    path = str(tmp_path / "length.mp4")
    write_test_video(path, n_frames=7, fps=10.0)
    video = Video(path)

    assert len(video) == 7
    video.close()


def test_context_manager(tmp_path):
    """Video должен поддерживать context manager и закрываться при выходе."""

    path = str(tmp_path / "ctx.mp4")
    write_test_video(path, n_frames=2, fps=10.0)

    with Video(path) as video:
        assert video.frame_count == 2
        frame = video.frame_at_idx(0)
        assert frame is not None

    with pytest.raises(RuntimeError, match="Video is closed"):
        video.frame_at_idx(0)


def test_close_prevents_further_use(tmp_path):
    """После закрытия Video дальнейшее использование объекта должно быть запрещено."""

    path = str(tmp_path / "closed.mp4")
    write_test_video(path, n_frames=1, fps=10.0)
    video = Video(path)

    video.close()

    with pytest.raises(RuntimeError, match="Video is closed"):
        video.frame_at_idx(0)


def test_close_twice_does_not_crash(tmp_path):
    """Повторный close не должен вызывать ошибку."""

    path = str(tmp_path / "double.mp4")
    write_test_video(path, n_frames=1, fps=10.0)
    video = Video(path)

    video.close()
    video.close()
