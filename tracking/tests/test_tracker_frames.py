from __future__ import annotations

import numpy as np


class DummyProjection:
    """Простая обертка для координат точки взгляда."""

    def __init__(self, coords: list[float]) -> None:
        self._coords = np.array(coords, dtype=float)

    def cpu(self) -> "DummyProjection":
        return self

    def numpy(self) -> np.ndarray:
        return self._coords


def test_draw_points_draws_every_point(tracker_module, fake_cv2):
    """Для каждой точки должен вызываться метод рисования окружности."""

    image = np.zeros((3, 3, 3), dtype=np.uint8)

    result = tracker_module.Tracker.draw_points(image, [(1, 2), (3, 4)])

    assert result is image
    assert fake_cv2.circles == [
        ((1, 2), 2, (0, 0, 255), 2),
        ((3, 4), 2, (0, 0, 255), 2),
    ]


def test_process_camera_frame_draws_bboxes_points_and_arrow(build_tracker, tmp_path, fake_cv2):
    """Обработка кадра камеры должна рисовать рамки, зрачки и направление взгляда."""

    tracker = build_tracker(tmp_path)
    frame = np.zeros((80, 80, 3), dtype=np.uint8)

    result = tracker.process_camera_frame(
        frame,
        (
            [np.array([0.4, -0.2, 0.0])],
            [((10, 20), (30, 40))],
            [(5, 7)],
            [((1, 2, 3, 4), (6, 7, 8, 9))],
        ),
        draw_bbox=True,
    )

    assert result is not frame
    assert fake_cv2.rectangles == [
        ((6, 9), (8, 11), (255, 0, 0), 2),
        ((11, 14), (13, 16), (255, 0, 0), 2),
    ]
    assert fake_cv2.circles == [
        ((15, 27), 2, (0, 0, 255), 2),
        ((35, 47), 2, (0, 0, 255), 2),
    ]
    assert fake_cv2.arrows == [
        ((25, 37), (35, 32), (255, 0, 0), 2),
    ]


def test_process_camera_frame_draws_only_arrow_without_bbox(build_tracker, tmp_path, fake_cv2):
    """Без флага draw_bbox на кадре должна рисоваться только стрелка взгляда."""

    tracker = build_tracker(tmp_path)
    frame = np.zeros((40, 40, 3), dtype=np.uint8)

    tracker.process_camera_frame(
        frame,
        (
            [np.array([0.2, 0.4, 0.0])],
            [((4, 6), (8, 10))],
            [(1, 2)],
            [((0, 0, 1, 1), (2, 2, 3, 3))],
        ),
        draw_bbox=False,
    )

    assert fake_cv2.rectangles == []
    assert fake_cv2.circles == []
    assert fake_cv2.arrows == [
        ((7, 10), (12, 20), (255, 0, 0), 2),
    ]


def test_process_screen_frame_draws_projected_point(build_tracker, tmp_path):
    """Проекция взгляда на экран должна превращаться в точку для отрисовки."""

    tracker = build_tracker(tmp_path)
    screen = np.zeros((4, 4, 3), dtype=np.uint8)
    expected = np.full_like(screen, 9)
    seen_points: list[tuple[int, int]] = []

    tracker.gaze_mapper.project = lambda _gaze_vec: DummyProjection([7.9, 3.2, 0.0])
    tracker.draw_points = lambda image, points: seen_points.extend(points) or expected

    result = tracker.process_screen_frame(screen, ([np.array([1.0, 2.0, 3.0])], [], [], []))

    assert seen_points == [(7, 3)]
    assert np.array_equal(result, expected)


def test_process_screen_frame_returns_original_without_gaze(build_tracker, tmp_path):
    """Если взгляд не найден, должен возвращаться исходный кадр экрана."""

    tracker = build_tracker(tmp_path)
    screen = np.zeros((3, 3, 3), dtype=np.uint8)

    result = tracker.process_screen_frame(screen, ([], [], [], []))

    assert result is screen


def test_process_screen_frame_returns_original_for_nan_projection(build_tracker, tmp_path):
    """Если проекция невалидна, трекер не должен рисовать точку на экране."""

    tracker = build_tracker(tmp_path)
    screen = np.zeros((3, 3, 3), dtype=np.uint8)
    tracker.gaze_mapper.project = lambda _gaze_vec: DummyProjection([np.nan, np.nan, np.nan])

    result = tracker.process_screen_frame(screen, ([np.array([1.0, 0.0, 0.0])], [], [], []))

    assert result is screen
