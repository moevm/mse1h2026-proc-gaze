"""Тесты основного контура обработки в трекере."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest


class IterableVideo:
    """Итерируемый набор кадров для тестов process_video."""

    def __init__(self, frames: list[np.ndarray], fps: float, width: int, height: int) -> None:
        self._frames = frames
        self.fps = fps
        self.width = width
        self.height = height
        self.duration_sec = len(frames) / fps if fps else None
        self.info = {
            "fps": fps,
            "frame_count": len(frames),
            "width": width,
            "height": height,
            "duration_sec": self.duration_sec,
        }

    def __iter__(self):
        return iter(self._frames)

    def __len__(self) -> int:
        return len(self._frames)


def test_convert_codec_calls_ffmpeg_with_expected_arguments(tracker_module):
    """Перекодирование должно вызывать ffmpeg с ожидаемыми параметрами."""

    tracker_module.Tracker.convert_codec(Path("/tmp/input.mp4"), Path("/tmp/output.mp4"))

    assert tracker_module.ffmpeg.input_calls == ["/tmp/input.mp4"]
    assert tracker_module.ffmpeg.output_calls == [
        (
            "/tmp/input.mp4",
            "/tmp/output.mp4",
            {
                "vcodec": "libx264",
                "pix_fmt": "yuv420p",
                "movflags": "+faststart",
                "an": None,
            },
        )
    ]
    assert tracker_module.ffmpeg.run_calls == [
        (
            "/tmp/input.mp4",
            "/tmp/output.mp4",
            {
                "overwrite_output": True,
                "capture_stdout": True,
                "capture_stderr": True,
            },
        )
    ]


def test_convert_codec_reraises_ffmpeg_error(tracker_module):
    """Ошибка ffmpeg должна пробрасываться вызывающему коду."""

    tracker_module.ffmpeg.run_error = b"broken"

    with pytest.raises(tracker_module.ffmpeg.Error):
        tracker_module.Tracker.convert_codec(Path("/tmp/input.mp4"), Path("/tmp/output.mp4"))


def test_process_video_returns_immediately_without_output_directory(build_tracker, tmp_path, fake_cv2):
    """Без выходной директории обработка видео должна завершаться без побочных эффектов."""

    tracker = build_tracker(tmp_path)
    screen_video = IterableVideo([np.zeros((2, 2, 3), dtype=np.uint8)], fps=30.0, width=2, height=2)
    camera_video = IterableVideo([np.zeros((2, 2, 3), dtype=np.uint8)], fps=24.0, width=2, height=2)

    tracker.process_video(screen_video, camera_video, None)

    assert fake_cv2.writers == []


def test_process_video_writes_processed_frames_and_converts_outputs(
    build_tracker,
    tracker_module,
    tmp_path,
):
    """Обработка пары видео должна сохранять кадры и запускать перекодирование."""

    tracker = build_tracker(tmp_path)
    out_dir = tmp_path / "results" / "rec-1"
    camera_frames = [np.full((2, 2, 3), 1, dtype=np.uint8), np.full((2, 2, 3), 2, dtype=np.uint8)]
    screen_frames = [
        np.full((2, 2, 3), 10, dtype=np.uint8),
        np.full((2, 2, 3), 11, dtype=np.uint8),
        np.full((2, 2, 3), 12, dtype=np.uint8),
    ]
    camera_video = IterableVideo(camera_frames, fps=24.0, width=2, height=2)
    screen_video = IterableVideo(screen_frames, fps=60.0, width=2, height=2)
    estimate_calls: list[np.ndarray] = []
    camera_calls: list[tuple[np.ndarray, bool]] = []
    screen_calls: list[np.ndarray] = []
    convert_calls: list[tuple[Path, Path]] = []

    tracker.gaze_estimator.estimate = lambda frame: (
        estimate_calls.append(frame.copy()) or [np.array([0.1, 0.2, 0.3])],
        [((0, 0), (1, 1))],
        [(0, 0)],
        [((0, 0, 1, 1), (1, 1, 2, 2))],
    )
    tracker.process_camera_frame = lambda frame, _gaze_info, draw_bbox=False: (
        camera_calls.append((frame.copy(), draw_bbox)) or (frame + 100)
    )
    tracker.process_screen_frame = lambda frame, _gaze_info: screen_calls.append(frame.copy()) or (frame + 50)
    tracker.convert_codec = lambda input_path, output_path: convert_calls.append((input_path, output_path))

    tracker.process_video(screen_video, camera_video, out_dir)

    camera_writer, screen_writer = tracker_module.cv2.writers
    assert out_dir.is_dir()
    assert len(estimate_calls) == 2
    assert [draw_bbox for _, draw_bbox in camera_calls] == [True, True]
    assert np.array_equal(camera_calls[0][0], camera_frames[0])
    assert np.array_equal(camera_calls[1][0], camera_frames[1])
    assert len(screen_calls) == 2
    assert np.array_equal(screen_calls[0], screen_frames[0])
    assert np.array_equal(screen_calls[1], screen_frames[1])
    assert camera_writer.path == str(out_dir / "camera_raw.mp4")
    assert camera_writer.fps == 24.0
    assert camera_writer.size == (2, 2)
    assert screen_writer.path == str(out_dir / "screen_raw.mp4")
    assert screen_writer.fps == 60.0
    assert screen_writer.size == (2, 2)
    assert np.array_equal(camera_writer.frames[0], camera_frames[0] + 100)
    assert np.array_equal(screen_writer.frames[1], screen_frames[1] + 50)
    assert camera_writer.released is True
    assert screen_writer.released is True
    assert convert_calls == [
        (out_dir / "camera_raw.mp4", out_dir / "camera.mp4"),
        (out_dir / "screen_raw.mp4", out_dir / "screen.mp4"),
    ]


def test_process_video_releases_writers_when_processing_fails(
    build_tracker,
    tracker_module,
    tmp_path,
):
    """Даже при ошибке обработки объекты записи видео должны освобождаться."""

    tracker = build_tracker(tmp_path)
    out_dir = tmp_path / "results" / "rec-2"
    camera_video = IterableVideo([np.zeros((2, 2, 3), dtype=np.uint8)], fps=24.0, width=2, height=2)
    screen_video = IterableVideo([np.zeros((2, 2, 3), dtype=np.uint8)], fps=30.0, width=2, height=2)

    def raise_processing_error(_frame):
        raise RuntimeError("boom")

    tracker.gaze_estimator.estimate = raise_processing_error

    with pytest.raises(RuntimeError, match="boom"):
        tracker.process_video(screen_video, camera_video, out_dir)

    camera_writer, screen_writer = tracker_module.cv2.writers
    assert camera_writer.released is True
    assert screen_writer.released is True


def test_process_job_builds_result_and_closes_videos(build_tracker, tracker_module, tmp_path):
    """Успешная обработка задания должна вернуть результат и закрыть оба видео."""

    tracker = build_tracker(tmp_path)
    process_calls: list[tuple[object, object, Path]] = []

    class FakeVideo:
        created: list["FakeVideo"] = []

        def __init__(self, path: str) -> None:
            self.path = path
            self.closed = False
            FakeVideo.created.append(self)

        def close(self) -> None:
            self.closed = True

    tracker_module.Video = FakeVideo
    tracker.process_video = lambda screen_video, webcam_video, out_dir: process_calls.append(
        (screen_video, webcam_video, out_dir)
    )

    result = tracker.process_job(
        {
            "recording_id": "rec-42",
            "path_screen": "incoming/screen.mp4",
            "path_webcam": "incoming/webcam.mp4",
        }
    )

    assert [video.path for video in FakeVideo.created] == [
        "/data/incoming/screen.mp4",
        "/data/incoming/webcam.mp4",
    ]
    assert process_calls == [
        (FakeVideo.created[0], FakeVideo.created[1], (tmp_path / "results" / "rec-42").resolve())
    ]
    assert all(video.closed for video in FakeVideo.created)
    assert result == {
        "recording_id": "rec-42",
        "intervals": [],
        "path_processed_webcam": "results/rec-42/camera.mp4",
        "path_processed_screen": "results/rec-42/screen.mp4",
    }


def test_process_job_raises_key_error_when_paths_are_missing(build_tracker, tmp_path):
    """Задание без обязательных путей должно отвергаться до открытия видео."""

    tracker = build_tracker(tmp_path)

    with pytest.raises(KeyError, match="payload must contain both"):
        tracker.process_job({"recording_id": "rec-42", "path_screen": "incoming/screen.mp4"})


def test_process_job_closes_opened_videos_when_processing_fails(build_tracker, tracker_module, tmp_path):
    """Даже при ошибке обработки уже открытые видео должны быть закрыты."""

    tracker = build_tracker(tmp_path)

    class FakeVideo:
        created: list["FakeVideo"] = []

        def __init__(self, path: str) -> None:
            self.path = path
            self.closed = False
            FakeVideo.created.append(self)

        def close(self) -> None:
            self.closed = True

    def raise_processing_error(_screen_video, _webcam_video, _out_dir):
        raise RuntimeError("broken pipeline")

    tracker_module.Video = FakeVideo
    tracker.process_video = raise_processing_error

    with pytest.raises(RuntimeError, match="broken pipeline"):
        tracker.process_job(
            {
                "recording_id": "rec-42",
                "path_screen": "incoming/screen.mp4",
                "path_webcam": "incoming/webcam.mp4",
            }
        )

    assert all(video.closed for video in FakeVideo.created)
