"""Общие фикстуры и заглушки для модульных тестов сервиса трекинга."""

from __future__ import annotations

import contextlib
import importlib
import importlib.util
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np
import pytest


class FakeVideoWriter:
    """Заглушка объекта записи видео из OpenCV."""

    def __init__(self, path: str, fourcc: str, fps: float, size: tuple[int, int]) -> None:
        self.path = path
        self.fourcc = fourcc
        self.fps = fps
        self.size = size
        self.frames: list[np.ndarray] = []
        self.released = False

    def write(self, frame: np.ndarray) -> None:
        self.frames.append(np.array(frame, copy=True))

    def release(self) -> None:
        self.released = True


class FakeCapture:
    """Заглушка источника видео для тестов класса Video."""

    def __init__(
        self,
        cv2_module: "FakeCV2",
        frames: list[np.ndarray],
        *,
        fps: float = 30.0,
        width: int = 0,
        height: int = 0,
        opened: bool = True,
        frame_count: int | None = None,
        failed_positions: set[int] | None = None,
    ) -> None:
        self._cv2 = cv2_module
        self.frames = [np.array(frame, copy=True) for frame in frames]
        self.fps = fps
        self.width = width
        self.height = height
        self.opened = opened
        self.frame_count = len(self.frames) if frame_count is None else frame_count
        self.failed_positions = set() if failed_positions is None else set(failed_positions)
        self.position = 0
        self.released = False

    def isOpened(self) -> bool:
        return self.opened and not self.released

    def get(self, prop: int) -> float:
        if prop == self._cv2.CAP_PROP_FPS:
            return self.fps
        if prop == self._cv2.CAP_PROP_FRAME_COUNT:
            return self.frame_count
        if prop == self._cv2.CAP_PROP_FRAME_WIDTH:
            return self.width
        if prop == self._cv2.CAP_PROP_FRAME_HEIGHT:
            return self.height
        if prop == self._cv2.CAP_PROP_POS_FRAMES:
            return self.position
        return 0.0

    def set(self, prop: int, value: float) -> bool:
        if prop == self._cv2.CAP_PROP_POS_FRAMES:
            self.position = int(value)
        return True

    def read(self) -> tuple[bool, np.ndarray | None]:
        if self.released or self.position in self.failed_positions:
            return False, None
        if self.position >= len(self.frames):
            return False, None

        frame = np.array(self.frames[self.position], copy=True)
        self.position += 1
        return True, frame

    def release(self) -> None:
        self.released = True


class FakeCV2(types.ModuleType):
    """Упрощенная замена cv2 для тестов трекера."""

    def __init__(self) -> None:
        super().__init__("cv2")
        self.CAP_FFMPEG = 1900
        self.CAP_PROP_FPS = 5
        self.CAP_PROP_FRAME_COUNT = 7
        self.CAP_PROP_FRAME_WIDTH = 3
        self.CAP_PROP_FRAME_HEIGHT = 4
        self.CAP_PROP_POS_FRAMES = 1
        self.writers: list[FakeVideoWriter] = []
        self.circles: list[tuple[tuple[int, int], int, tuple[int, int, int], int]] = []
        self.rectangles: list[tuple[tuple[int, int], tuple[int, int], tuple[int, int, int], int]] = []
        self.arrows: list[tuple[tuple[int, int], tuple[int, int], tuple[int, int, int], int]] = []
        self._capture_specs: dict[str, dict[str, Any]] = {}
        self.created_captures: list[FakeCapture] = []

    def register_capture(
        self,
        path: str | Path,
        *,
        frames: list[np.ndarray],
        fps: float = 30.0,
        width: int | None = None,
        height: int | None = None,
        opened: bool = True,
        frame_count: int | None = None,
        failed_positions: set[int] | None = None,
    ) -> None:
        frame_list = [np.array(frame, copy=True) for frame in frames]
        inferred_height = frame_list[0].shape[0] if frame_list else 0
        inferred_width = frame_list[0].shape[1] if frame_list else 0
        self._capture_specs[str(path)] = {
            "frames": frame_list,
            "fps": fps,
            "width": inferred_width if width is None else width,
            "height": inferred_height if height is None else height,
            "opened": opened,
            "frame_count": frame_count,
            "failed_positions": failed_positions,
        }

    def circle(
        self,
        image: np.ndarray,
        center: tuple[int, int],
        radius: int,
        color: tuple[int, int, int],
        thickness: int,
    ) -> np.ndarray:
        self.circles.append((center, radius, color, thickness))
        return image

    def rectangle(
        self,
        image: np.ndarray,
        pt1: tuple[int, int],
        pt2: tuple[int, int],
        color: tuple[int, int, int],
        thickness: int,
    ) -> np.ndarray:
        self.rectangles.append((pt1, pt2, color, thickness))
        return image

    def arrowedLine(
        self,
        image: np.ndarray,
        pt1: tuple[int, int],
        pt2: tuple[int, int],
        color: tuple[int, int, int],
        thickness: int,
    ) -> np.ndarray:
        self.arrows.append((pt1, pt2, color, thickness))
        return image

    def VideoWriter_fourcc(self, *chars: str) -> str:
        return "".join(chars)

    def VideoWriter(self, path: str, fourcc: str, fps: float, size: tuple[int, int]) -> FakeVideoWriter:
        writer = FakeVideoWriter(path, fourcc, fps, size)
        self.writers.append(writer)
        return writer

    def VideoCapture(self, path: str | Path, *_args) -> FakeCapture:
        spec = self._capture_specs.get(str(path))
        if spec is None:
            capture = FakeCapture(self, [], opened=False)
        else:
            capture = FakeCapture(self, **spec)
        self.created_captures.append(capture)
        return capture


class FakeProjection:
    """Заглушка результата проекции взгляда."""

    def __init__(self, coords: list[float]) -> None:
        self._coords = np.array(coords, dtype=float)

    def cpu(self) -> "FakeProjection":
        return self

    def numpy(self) -> np.ndarray:
        return self._coords


class FakeFFmpegError(Exception):
    """Исключение для имитации ошибки ffmpeg."""

    def __init__(self, stderr: bytes | None = None) -> None:
        super().__init__("ffmpeg error")
        self.stderr = stderr


class FakeFFmpegStream:
    """Заглушка последовательности вызовов ffmpeg."""

    def __init__(self, owner: "FakeFFmpeg", input_path: str) -> None:
        self.owner = owner
        self.input_path = input_path
        self.output_path: str | None = None
        self.output_kwargs: dict[str, Any] = {}

    def output(self, output_path: str, **kwargs: Any) -> "FakeFFmpegStream":
        self.output_path = output_path
        self.output_kwargs = kwargs
        self.owner.output_calls.append((self.input_path, output_path, kwargs))
        return self

    def run(self, **kwargs: Any) -> None:
        self.owner.run_calls.append((self.input_path, self.output_path, kwargs))
        if self.owner.run_error is not None:
            raise self.owner.Error(self.owner.run_error)


class FakeFFmpeg(types.ModuleType):
    """Упрощенная замена ffmpeg для тестов."""

    def __init__(self) -> None:
        super().__init__("ffmpeg")
        self.Error = FakeFFmpegError
        self.input_calls: list[str] = []
        self.output_calls: list[tuple[str, str, dict[str, Any]]] = []
        self.run_calls: list[tuple[str, str | None, dict[str, Any]]] = []
        self.run_error: bytes | None = None

    def input(self, input_path: str) -> FakeFFmpegStream:
        self.input_calls.append(input_path)
        return FakeFFmpegStream(self, input_path)


@pytest.fixture
def tracking_root() -> Path:
    """Возвращает корневую директорию сервиса трекинга."""

    return Path(__file__).resolve().parents[1]


@pytest.fixture
def fake_cv2() -> FakeCV2:
    """Возвращает подмененный модуль cv2."""

    return FakeCV2()


@pytest.fixture
def tracker_module(
    monkeypatch: pytest.MonkeyPatch,
    tracking_root: Path,
    fake_cv2: FakeCV2,
):
    """Импортирует модуль трекера с подставленными зависимостями."""

    monkeypatch.syspath_prepend(str(tracking_root))

    fake_src = types.ModuleType("src")
    fake_src.__path__ = [str(tracking_root / "src")]

    fake_gaze_estimator = types.ModuleType("src.gaze_estimator")

    class FakeGazeEstimator:
        def __init__(self, precision_mode: int = 0, threshold: float = 0.5) -> None:
            self.precision_mode = precision_mode
            self.threshold = threshold

        def estimate(self, _frame: np.ndarray):
            return [], [], [], []

    fake_gaze_estimator.GazeEstimator = FakeGazeEstimator
    fake_gaze_estimator.Tuple = tuple
    fake_gaze_estimator.List = list
    fake_gaze_estimator.np = np
    fake_gaze_estimator.cv2 = fake_cv2

    fake_torch = types.SimpleNamespace(no_grad=lambda: contextlib.nullcontext())
    fake_gaze_mapper = types.ModuleType("src.gaze_mapper")

    class FakeGazeMapper:
        def project(self, _gaze_vec: np.ndarray) -> FakeProjection:
            return FakeProjection([0.0, 0.0, 0.0])

    fake_gaze_mapper.GazeMapper = FakeGazeMapper
    fake_gaze_mapper.torch = fake_torch

    fake_video = types.ModuleType("src.video")

    class PlaceholderVideo:
        def __init__(self, _path: str | Path) -> None:
            raise AssertionError("Тест должен явно подменить src.tracker.Video.")

    fake_video.Video = PlaceholderVideo

    fake_ffmpeg = FakeFFmpeg()

    monkeypatch.setitem(sys.modules, "src", fake_src)
    monkeypatch.setitem(sys.modules, "src.gaze_estimator", fake_gaze_estimator)
    monkeypatch.setitem(sys.modules, "src.gaze_mapper", fake_gaze_mapper)
    monkeypatch.setitem(sys.modules, "src.video", fake_video)
    monkeypatch.setitem(sys.modules, "ffmpeg", fake_ffmpeg)
    sys.modules.pop("src.tracker", None)
    importlib.invalidate_caches()
    module = importlib.import_module("src.tracker")
    module.cv2 = fake_cv2
    module.torch = fake_torch
    module.ffmpeg = fake_ffmpeg
    return module


@pytest.fixture
def build_tracker(
    monkeypatch: pytest.MonkeyPatch,
    tracker_module,
):
    """Создает экземпляр Tracker с временной директорией данных."""

    def factory(data_dir: Path, precision_mode: int = 0, threshold: float = 0.5):
        monkeypatch.setenv("DATA_DIR", str(data_dir))
        return tracker_module.Tracker(precision_mode, threshold)

    return factory


@pytest.fixture
def video_module(
    monkeypatch: pytest.MonkeyPatch,
    tracking_root: Path,
    fake_cv2: FakeCV2,
):
    """Загружает модуль Video из файла с подмененным cv2."""

    module_name = "tracking_video_under_test"
    module_path = tracking_root / "src" / "video.py"
    fake_src = types.ModuleType("src")
    fake_src.__path__ = [str(tracking_root / "src")]
    monkeypatch.syspath_prepend(str(tracking_root))
    monkeypatch.setitem(sys.modules, "src", fake_src)
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Не удалось подготовить модуль video для тестов.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
