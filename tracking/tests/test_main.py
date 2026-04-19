from __future__ import annotations

import os
from unittest.mock import AsyncMock, Mock, patch

import pytest

os.environ.setdefault("AMQP_URL", "amqp://guest:guest@localhost/")
os.environ.setdefault("DATA_DIR", "/tmp/tracker-test-main")

import main


@pytest.fixture(autouse=True)
def _patch_broker():
    """Подменяет брокер на мок — RabbitMQ недоступен в тестах."""
    main.broker.publish = AsyncMock()

    async def immediate_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    with patch.object(main.asyncio, "to_thread", side_effect=immediate_to_thread):
        yield


@pytest.mark.asyncio
async def test_on_startup_initializes_tracker():
    """При старте сервис должен создать трекер."""

    await main.on_startup()

    assert main.tracker is not None


@pytest.mark.asyncio
async def test_on_startup_configures_gaze_mapper():
    """При старте маппер взгляда должен быть переведён в eval режим."""

    await main.on_startup()

    assert main.tracker.gaze_mapper is not None


@pytest.mark.asyncio
async def test_handle_job_publishes_processed_result():
    """Успешная обработка задания должна публиковать результат в очередь результатов."""

    await main.on_startup()
    expected_result = {
        "recording_id": "rec-1",
        "intervals": [],
        "path_processed_webcam": "results/rec-1/camera.mp4",
    }
    main.tracker.process_job = Mock(return_value=expected_result)

    await main.handle_job({"recording_id": "rec-1"})

    main.tracker.process_job.assert_called_once_with({"recording_id": "rec-1"})
    main.broker.publish.assert_awaited_once()
    published = main.broker.publish.await_args[0][0]
    assert published == expected_result


@pytest.mark.asyncio
async def test_handle_job_publishes_fallback_result_on_error():
    """При ошибке обработки сервис должен публиковать минимальный результат без падения."""

    await main.on_startup()
    main.tracker.process_job = Mock(side_effect=RuntimeError("boom"))

    await main.handle_job({"recording_id": "rec-2"})

    main.broker.publish.assert_awaited_once()
    published = main.broker.publish.await_args[0][0]
    assert published["recording_id"] == "rec-2"
    assert published["intervals"] == []


@pytest.mark.asyncio
async def test_handle_job_fallback_without_recording_id():
    """При ошибке без recording_id в сообщении сервис не должен падать."""

    await main.on_startup()
    main.tracker.process_job = Mock(side_effect=RuntimeError("bad"))

    await main.handle_job({})

    main.broker.publish.assert_awaited_once()
    published = main.broker.publish.await_args[0][0]
    assert published["recording_id"] is None
    assert published["intervals"] == []


@pytest.mark.asyncio
async def test_handle_job_fallback_with_non_dict_message():
    """При некорректном формате сообщения сервис не должен падать."""

    await main.on_startup()
    main.tracker.process_job = Mock(side_effect=TypeError("not subscriptable"))

    await main.handle_job("not a dict")

    main.broker.publish.assert_awaited_once()
    published = main.broker.publish.await_args[0][0]
    assert published["intervals"] == []


@pytest.mark.asyncio
async def test_handle_job_publishes_to_results_queue():
    """Результат должен публиковаться именно в results_queue."""

    await main.on_startup()
    main.tracker.process_job = Mock(return_value={"recording_id": "q", "intervals": []})

    await main.handle_job({"recording_id": "q"})

    call_kwargs = main.broker.publish.await_args[1]
    assert call_kwargs["queue"] is main.results_queue
