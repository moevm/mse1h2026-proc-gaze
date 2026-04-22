from __future__ import annotations

import numpy as np


def test_draw_points_draws_every_point(tracker):
    """Для каждой точки должен вызываться метод рисования окружности."""

    image = np.zeros((10, 10, 3), dtype=np.uint8)

    result = tracker.draw_points(image, [(1, 2), (3, 4)])

    assert result is image
    assert image[2, 1].tolist() == [0, 0, 255]
    assert image[4, 3].tolist() == [0, 0, 255]


def test_draw_points_empty_list(tracker):
    """Пустой список точек не должен менять изображение."""

    image = np.zeros((10, 10, 3), dtype=np.uint8)
    original = image.copy()

    result = tracker.draw_points(image, [])

    assert result is image
    assert np.array_equal(image, original)


def test_process_camera_frame_draws_bboxes_points_and_arrow(tracker):
    """Обработка кадра камеры должна рисовать рамки, зрачки и направление взгляда."""

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
    diff = np.any(result != 0, axis=-1)
    assert diff.any()


def test_process_camera_frame_empty_gaze(tracker):
    """Пустой gaze_info не должен ничего рисовать."""

    frame = np.zeros((20, 20, 3), dtype=np.uint8)

    result = tracker.process_camera_frame(frame, ([], [], [], []))

    assert np.array_equal(result, frame)


def test_process_camera_frame_multiple_faces(tracker):
    """Несколько лиц — рисуется стрелка для каждого."""

    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    result = tracker.process_camera_frame(
        frame,
        (
            [np.array([0.3, 0.1, 0.0]), np.array([-0.2, 0.5, 0.0])],
            [((10, 20), (30, 40)), ((50, 60), (70, 80))],
            [(0, 0), (0, 0)],
            [((0, 0, 1, 1), (2, 2, 3, 3)), ((4, 4, 5, 5), (6, 6, 7, 7))],
        ),
        draw_bbox=False,
    )

    assert np.any(result != 0)


def test_process_camera_frame_does_not_modify_original(tracker):
    """Оригинальный кадр не должен изменяться."""

    frame = np.full((40, 40, 3), 128, dtype=np.uint8)
    original = frame.copy()

    tracker.process_camera_frame(
        frame,
        (
            [np.array([0.4, -0.2, 0.0])],
            [((10, 20), (30, 40))],
            [(5, 7)],
            [((1, 2, 3, 4), (6, 7, 8, 9))],
        ),
        draw_bbox=True,
    )

    assert np.array_equal(frame, original)


def test_process_screen_frame_returns_original_without_gaze(tracker):
    """Если взгляд не найден, должен возвращаться исходный кадр экрана."""

    screen = np.zeros((3, 3, 3), dtype=np.uint8)

    result = tracker.process_screen_frame(screen, ([], [], [], []))

    assert result is screen
