from __future__ import annotations

import numpy as np
import pytest

from src.gaze_estimator import GazeEstimator


@pytest.fixture(scope="module")
def estimator():
    """Один экземпляр GazeEstimator на весь модуль (загрузка моделей дорогая)."""
    return GazeEstimator(precision_mode=0, threshold=0.5)


def test_estimate_returns_four_lists(estimator):
    """estimate должен возвращать кортеж из четырёх списков."""

    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    result = estimator.estimate(frame)

    assert isinstance(result, tuple)
    assert len(result) == 4
    gaze_vecs, pupils, offsets, eye_bboxes = result
    assert isinstance(gaze_vecs, list)
    assert isinstance(pupils, list)
    assert isinstance(offsets, list)
    assert isinstance(eye_bboxes, list)


def test_estimate_empty_frame_returns_no_faces(estimator):
    """На чёрном кадре не должно обнаруживаться лиц."""

    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    gaze_vecs, pupils, offsets, eye_bboxes = estimator.estimate(frame)

    assert len(gaze_vecs) == 0
    assert len(pupils) == 0


def test_estimate_preserves_input_frame(estimator):
    """estimate не должен модифицировать входной кадр."""

    frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    original = frame.copy()

    estimator.estimate(frame)

    assert np.array_equal(frame, original)


def test_estimate_different_frame_sizes(estimator):
    """estimate должен работать с кадрами разных размеров."""

    for size in [(50, 50), (200, 300), (720, 1280)]:
        frame = np.zeros((*size, 3), dtype=np.uint8)
        result = estimator.estimate(frame)
        assert len(result) == 4


def test_preprocess_image_output_shape():
    """preprocess_image должен возвращать тензор с правильной формой."""

    image = np.random.randint(0, 255, (100, 80, 3), dtype=np.uint8)

    result = GazeEstimator.preprocess_image(image, (64, 64))

    assert result.shape == (1, 3, 64, 64)


def test_preprocess_image_dtype():
    """preprocess_image должен сохранять числовой тип."""

    image = np.zeros((50, 50, 3), dtype=np.uint8)

    result = GazeEstimator.preprocess_image(image, (32, 32))

    assert result.dtype == np.uint8
