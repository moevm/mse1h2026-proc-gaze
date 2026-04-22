from __future__ import annotations

import numpy as np
import torch
import pytest

from src.gaze_mapper import GazeMapper


@pytest.fixture
def mapper():
    return GazeMapper()


def test_project_returns_3d_tensor(mapper):
    """project должен возвращать тензор из 3 координат."""

    gaze_vec = np.array([0.1, 0.2, 0.9])

    result = mapper.project(gaze_vec)

    assert result.shape == (3,)


def test_project_returns_finite_values(mapper):
    """project не должен возвращать NaN/Inf для нормального вектора."""

    gaze_vec = np.array([0.0, 0.0, 1.0])

    result = mapper.project(gaze_vec)

    assert torch.isfinite(result).all()


def test_project_different_vectors_give_different_results(mapper):
    """Разные векторы взгляда должны давать разные проекции."""

    r1 = mapper.project(np.array([0.5, 0.0, 0.5]))
    r2 = mapper.project(np.array([-0.5, 0.0, 0.5]))

    assert not torch.equal(r1, r2)
