from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest

from conftest import write_test_video
from src.video import Video


def test_convert_codec_produces_output_file(tracker, tmp_path):
    """Перекодирование должно создать выходной файл."""

    input_path = tmp_path / "input.mp4"
    output_path = tmp_path / "output.mp4"
    write_test_video(str(input_path), n_frames=3, width=10, height=10)

    tracker.convert_codec(input_path, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_convert_codec_output_is_valid_video(tracker, tmp_path):
    """После перекодирования файл должен открываться как видео."""

    input_path = tmp_path / "input.mp4"
    output_path = tmp_path / "output.mp4"
    write_test_video(str(input_path), n_frames=5, width=20, height=20)

    tracker.convert_codec(input_path, output_path)

    video = Video(str(output_path))
    assert video.frame_count > 0
    assert video.width == 20
    assert video.height == 20
    video.close()


def test_convert_codec_raises_on_invalid_input(tracker, tmp_path):
    """Перекодирование несуществующего файла должно бросать исключение."""

    with pytest.raises(Exception):
        tracker.convert_codec(tmp_path / "nope.mp4", tmp_path / "out.mp4")


def test_process_video_returns_immediately_without_output_directory(tracker, tmp_path):
    """Без выходной директории обработка видео должна завершаться без побочных эффектов."""

    screen_path = str(tmp_path / "screen.mp4")
    camera_path = str(tmp_path / "camera.mp4")
    write_test_video(screen_path, n_frames=2, width=10, height=10)
    write_test_video(camera_path, n_frames=2, width=10, height=10)

    screen_video = Video(screen_path)
    camera_video = Video(camera_path)

    try:
        tracker.process_video(screen_video, camera_video, None)
    finally:
        screen_video.close()
        camera_video.close()


def test_process_video_creates_output_files(tracker, tmp_path):
    """Обработка пары видео должна создать выходные файлы."""

    out_dir = tmp_path / "results" / "rec-1"
    screen_path = str(tmp_path / "screen.mp4")
    camera_path = str(tmp_path / "camera.mp4")
    write_test_video(screen_path, n_frames=3, width=10, height=10, fps=30.0)
    write_test_video(camera_path, n_frames=3, width=10, height=10, fps=30.0)

    screen_video = Video(screen_path)
    camera_video = Video(camera_path)

    try:
        tracker.process_video(screen_video, camera_video, out_dir)
    finally:
        screen_video.close()
        camera_video.close()

    assert (out_dir / "camera.mp4").exists()
    assert (out_dir / "screen.mp4").exists()
    assert not (out_dir / "camera_raw.mp4").exists()
    assert not (out_dir / "screen_raw.mp4").exists()


def test_process_video_output_is_readable(tracker, tmp_path):
    """Выходные видео после обработки должны открываться и содержать кадры."""

    out_dir = tmp_path / "results" / "rec-read"
    screen_path = str(tmp_path / "screen.mp4")
    camera_path = str(tmp_path / "camera.mp4")
    write_test_video(screen_path, n_frames=5, width=20, height=20, fps=25.0)
    write_test_video(camera_path, n_frames=5, width=20, height=20, fps=25.0)

    screen_video = Video(screen_path)
    camera_video = Video(camera_path)

    try:
        tracker.process_video(screen_video, camera_video, out_dir)
    finally:
        screen_video.close()
        camera_video.close()

    cam_out = Video(str(out_dir / "camera.mp4"))
    scr_out = Video(str(out_dir / "screen.mp4"))

    assert cam_out.frame_count > 0
    assert scr_out.frame_count > 0
    cam_out.close()
    scr_out.close()


def test_process_video_with_different_frame_counts(tracker, tmp_path):
    """При разном числе кадров обработка должна идти по меньшему."""

    out_dir = tmp_path / "results" / "rec-diff"
    screen_path = str(tmp_path / "screen.mp4")
    camera_path = str(tmp_path / "camera.mp4")
    write_test_video(screen_path, n_frames=10, width=10, height=10, fps=30.0)
    write_test_video(camera_path, n_frames=5, width=10, height=10, fps=30.0)

    screen_video = Video(screen_path)
    camera_video = Video(camera_path)

    try:
        tracker.process_video(screen_video, camera_video, out_dir)
    finally:
        screen_video.close()
        camera_video.close()

    assert (out_dir / "camera.mp4").exists()
    assert (out_dir / "screen.mp4").exists()


def test_process_job_builds_result(tracker, tmp_path):
    """Успешная обработка задания должна вернуть результат с нужными полями."""

    os.makedirs("/data/test_job", exist_ok=True)
    write_test_video("/data/test_job/screen.mp4", n_frames=3, width=10, height=10)
    write_test_video("/data/test_job/webcam.mp4", n_frames=3, width=10, height=10)

    try:
        result = tracker.process_job({
            "recording_id": "rec-42",
            "path_screen": "test_job/screen.mp4",
            "path_webcam": "test_job/webcam.mp4",
        })

        assert result["recording_id"] == "rec-42"
        assert isinstance(result["intervals"], list)
        assert "path_processed_webcam" in result
        assert "path_processed_screen" in result
        assert "camera.mp4" in result["path_processed_webcam"]
        assert "screen.mp4" in result["path_processed_screen"]
    finally:
        Path("/data/test_job/screen.mp4").unlink(missing_ok=True)
        Path("/data/test_job/webcam.mp4").unlink(missing_ok=True)
        Path("/data/test_job").rmdir()


def test_process_job_creates_output_files(tracker, tmp_path):
    """process_job должен создать файлы результатов на диске."""

    os.makedirs("/data/test_job_files", exist_ok=True)
    write_test_video("/data/test_job_files/screen.mp4", n_frames=3, width=10, height=10)
    write_test_video("/data/test_job_files/webcam.mp4", n_frames=3, width=10, height=10)

    try:
        result = tracker.process_job({
            "recording_id": "rec-files",
            "path_screen": "test_job_files/screen.mp4",
            "path_webcam": "test_job_files/webcam.mp4",
        })

        out_dir = tmp_path / "results" / "rec-files"
        assert (out_dir / "camera.mp4").exists()
        assert (out_dir / "screen.mp4").exists()
    finally:
        Path("/data/test_job_files/screen.mp4").unlink(missing_ok=True)
        Path("/data/test_job_files/webcam.mp4").unlink(missing_ok=True)
        Path("/data/test_job_files").rmdir()


def test_process_job_raises_key_error_when_paths_are_missing(tracker):
    """Задание без обязательных путей должно отвергаться."""

    with pytest.raises(KeyError, match="payload must contain both"):
        tracker.process_job({"recording_id": "rec-42", "path_screen": "incoming/screen.mp4"})


def test_process_job_raises_key_error_when_both_paths_missing(tracker):
    """Задание без обоих путей должно отвергаться."""

    with pytest.raises(KeyError, match="payload must contain both"):
        tracker.process_job({"recording_id": "rec-42"})


def test_process_job_raises_on_missing_recording_id(tracker):
    """Задание без recording_id должно вызывать KeyError."""

    with pytest.raises(KeyError):
        tracker.process_job({"path_screen": "s.mp4", "path_webcam": "w.mp4"})


def test_gen_unique_process_id_increments():
    """Каждый вызов gen_unique_process_id должен возвращать уникальное значение."""

    from src.tracker import Tracker

    id1 = Tracker.gen_unique_process_id()
    id2 = Tracker.gen_unique_process_id()
    id3 = Tracker.gen_unique_process_id()

    assert id1 < id2 < id3
