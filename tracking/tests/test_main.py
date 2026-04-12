from __future__ import annotations

import contextlib
import importlib
import sys
import types

import pytest


class FakeMapper:
    """Заглушка маппера взгляда для проверки конфигурации при старте."""

    def __init__(self) -> None:
        self.eval_called = False
        self.to_calls: list[object] = []

    def eval(self) -> None:
        self.eval_called = True

    def to(self, device: object) -> None:
        self.to_calls.append(device)


class FakeTracker:
    """Заглушка Tracker для тестов main.py."""

    def __init__(self) -> None:
        self.gaze_mapper = FakeMapper()
        self.messages: list[dict] = []
        self.result: object = {"recording_id": "default", "intervals": []}

    def process_job(self, message: dict):
        self.messages.append(message)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class FakeFastStream:
    """Упрощенный объект приложения FastStream."""

    def __init__(self, broker) -> None:
        self.broker = broker
        self.startup_handlers: list[object] = []
        self.ran = False

    def on_startup(self, func):
        self.startup_handlers.append(func)
        return func

    async def run(self) -> None:
        self.ran = True


class FakeBroker:
    """Заглушка брокера RabbitMQ."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.published: list[tuple[dict, object]] = []
        self.subscriptions: list[tuple[object, object]] = []
        self.started = False

    def subscriber(self, queue):
        def decorator(func):
            self.subscriptions.append((queue, func))
            return func

        return decorator

    async def publish(self, message: dict, queue) -> None:
        self.published.append((message, queue))

    async def start(self) -> None:
        self.started = True


class FakeQueue:
    """Заглушка описания очереди."""

    def __init__(self, name: str, durable: bool = True) -> None:
        self.name = name
        self.durable = durable


@pytest.fixture
def main_module(monkeypatch, tracking_root):
    """Импортирует main.py с подмененными внешними зависимостями."""

    monkeypatch.syspath_prepend(str(tracking_root))
    monkeypatch.setenv("AMQP_URL", "amqp://guest:guest@localhost/")

    fake_src = types.ModuleType("src")
    fake_src.__path__ = [str(tracking_root / "src")]

    fake_tracker_module = types.ModuleType("src.tracker")
    fake_tracker_module.Tracker = FakeTracker

    fake_torch = types.ModuleType("torch")
    fake_torch.cuda = types.SimpleNamespace(is_available=lambda: False)
    fake_torch.device = lambda name: name
    fake_torch.no_grad = lambda: contextlib.nullcontext()

    fake_faststream = types.ModuleType("faststream")
    fake_faststream.FastStream = FakeFastStream

    fake_faststream_rabbit = types.ModuleType("faststream.rabbit")
    fake_faststream_rabbit.RabbitBroker = FakeBroker
    fake_faststream_rabbit.RabbitQueue = FakeQueue

    monkeypatch.setitem(sys.modules, "src", fake_src)
    monkeypatch.setitem(sys.modules, "src.tracker", fake_tracker_module)
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "faststream", fake_faststream)
    monkeypatch.setitem(sys.modules, "faststream.rabbit", fake_faststream_rabbit)
    sys.modules.pop("main", None)
    importlib.invalidate_caches()
    module = importlib.import_module("main")

    async def immediate_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    module.asyncio.to_thread = immediate_to_thread
    return module


@pytest.mark.asyncio
async def test_on_startup_initializes_tracker_and_configures_mapper(main_module):
    """При старте сервис должен создать трекер и настроить маппер взгляда."""

    await main_module.on_startup()

    assert isinstance(main_module.tracker, FakeTracker)
    assert main_module.tracker.gaze_mapper.eval_called is True
    assert main_module.tracker.gaze_mapper.to_calls == [main_module.device]


@pytest.mark.asyncio
async def test_handle_job_publishes_processed_result(main_module):
    """Успешная обработка задания должна публиковать результат в очередь результатов."""

    await main_module.on_startup()
    main_module.tracker.result = {
        "recording_id": "rec-1",
        "intervals": [],
        "path_processed_webcam": "results/rec-1/camera.mp4",
    }

    await main_module.handle_job({"recording_id": "rec-1"})

    assert main_module.tracker.messages == [{"recording_id": "rec-1"}]
    assert main_module.broker.published == [
        (
            {
                "recording_id": "rec-1",
                "intervals": [],
                "path_processed_webcam": "results/rec-1/camera.mp4",
            },
            main_module.results_queue,
        )
    ]


@pytest.mark.asyncio
async def test_handle_job_publishes_fallback_result_on_error(main_module):
    """При ошибке обработки сервис должен публиковать минимальный результат без падения."""

    await main_module.on_startup()
    main_module.tracker.result = RuntimeError("boom")

    await main_module.handle_job({"recording_id": "rec-2"})

    assert main_module.broker.published == [
        (
            {
                "recording_id": "rec-2",
                "intervals": [],
            },
            main_module.results_queue,
        )
    ]
