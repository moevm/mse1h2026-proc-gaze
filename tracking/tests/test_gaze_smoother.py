from __future__ import annotations

import numpy as np

from src.gaze_smoother import GazeSmoother


def test_gaze_smoother_uses_previous_point():
    """EMA smoother должен использовать предыдущее значение после первого update."""

    smoother = GazeSmoother(alpha=0.25)

    first = smoother.update(np.array([0.0, 0.0]))
    second = smoother.update(np.array([4.0, 8.0]))

    assert np.allclose(first, [0.0, 0.0])
    assert np.allclose(second, [1.0, 2.0])
    assert np.allclose(smoother.prev_point, second)
