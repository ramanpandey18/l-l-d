import threading

import pytest

from logger import (
    DefaultFormatter,
    FileAppender,
    LogLevel,
    Logger,
    LoggerManager,
    MemoryAppender,
    SimpleFormatter,
)


@pytest.fixture(autouse=True)
def reset_logger_manager():
    """Give each test a fresh LoggerManager singleton."""
    LoggerManager.reset()
    yield
    LoggerManager.reset()


def test_logger_rejects_invalid_initial_level():
    with pytest.raises(ValueError):
        Logger("app", level=True)


def test_logger_rejects_empty_name():
    with pytest.raises(ValueError):
        Logger(" ")


def test_logger_manager_reuses_named_logger():
    manager = LoggerManager.get_instance()

    assert manager.get_logger("payments") is manager.get_logger("payments")


def test_logger_threshold_skips_lazy_message():
    logger = Logger("app", level=LogLevel.INFO)
    called = []

    logger.debug(lambda: called.append(True))

    assert called == []


def test_appender_thresholds_are_independent():
    logger = Logger("app", level=LogLevel.DEBUG)
    info_appender = MemoryAppender(LogLevel.INFO, SimpleFormatter())
    error_appender = MemoryAppender(LogLevel.ERROR, SimpleFormatter())

    logger.add_appender(info_appender)
    logger.add_appender(error_appender)

    logger.info("started")
    logger.error("failed")

    assert info_appender.lines == [
        "INFO: started",
        "ERROR: failed",
    ]
    assert error_appender.lines == ["ERROR: failed"]


def test_one_failing_appender_does_not_stop_next():
    class FailingAppender(MemoryAppender):
        def _write(self, formatted):
            raise RuntimeError("expected test error")

    logger = Logger("app", level=LogLevel.DEBUG)
    logger.add_appender(FailingAppender(LogLevel.DEBUG, SimpleFormatter()))

    working = MemoryAppender(LogLevel.DEBUG, SimpleFormatter())
    logger.add_appender(working)

    logger.error("still logged")

    assert working.lines == ["ERROR: still logged"]


def test_file_appender_context_manager_closes_file(tmp_path):
    path = tmp_path / "app.log"

    with FileAppender(str(path), LogLevel.DEBUG, SimpleFormatter()) as appender:
        logger = Logger("app", level=LogLevel.DEBUG)
        logger.add_appender(appender)
        logger.info("hello")

    assert appender.file.closed
    assert path.read_text(encoding="utf-8") == "INFO: hello\n"


def test_concurrent_logger_creation_returns_same_instance():
    manager = LoggerManager.get_instance()
    results = []
    barrier = threading.Barrier(8)

    def worker():
        barrier.wait()
        results.append(manager.get_logger("shared"))

    threads = [
        threading.Thread(target=worker)
        for _ in range(8)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert len(results) == 8
    assert all(logger is results[0] for logger in results)
