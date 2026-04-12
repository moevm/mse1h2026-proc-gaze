from __future__ import annotations

import pytest


def test_resolve_path_keeps_paths_inside_data_dir(build_tracker, tmp_path):
    """Преобразование относительного пути должно оставлять файл внутри DATA_DIR."""

    tracker = build_tracker(tmp_path)

    resolved = tracker._resolve_path("videos/screen.mp4")

    assert resolved == (tmp_path / "videos" / "screen.mp4").resolve()


@pytest.mark.parametrize("bad_path", ["/tmp/screen.mp4", "../screen.mp4", "nested/../../screen.mp4"])
def test_resolve_path_rejects_escaping_paths(build_tracker, tmp_path, bad_path: str):
    """Пути с выходом за пределы DATA_DIR должны отвергаться."""

    tracker = build_tracker(tmp_path)

    with pytest.raises(ValueError, match="Invalid path"):
        tracker._resolve_path(bad_path)


def test_to_relative_path_returns_path_inside_data_dir(build_tracker, tmp_path):
    """Путь внутри DATA_DIR должен преобразовываться к относительному виду."""

    tracker = build_tracker(tmp_path)

    result = tracker._to_relative_path(tmp_path / "results" / "rec-1" / "camera.mp4")

    assert result == "results/rec-1/camera.mp4"


def test_to_relative_path_rejects_path_outside_data_dir(build_tracker, tmp_path):
    """Путь вне DATA_DIR не должен преобразовываться к относительному."""

    tracker = build_tracker(tmp_path)

    with pytest.raises(ValueError):
        tracker._to_relative_path(tmp_path.parent / "camera.mp4")
