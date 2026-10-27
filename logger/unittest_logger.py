import tempfile
import threading
import unittest
from pathlib import Path

from logger import (
    ConsoleAppender,
    DefaultFormatter,
    FileAppender,
    LogLevel,
    Logger,
    LoggerManager,
    MemoryAppender,
    SimpleFormatter,
)


class LoggingSystemTests(unittest.TestCase):
    def setUp(self):
        LoggerManager.reset()

    def test_logger_rejects_invalid_initial_level(self):
        with self.assertRaises(ValueError):
            Logger("app", level=True)

    def test_logger_rejects_empty_name(self):
        with self.assertRaises(ValueError):
            Logger(" ")

    def test_logger_manager_reuses_named_logger(self):
        manager = LoggerManager.get_instance()
        self.assertIs(manager.get_logger("payments"), manager.get_logger("payments"))

    def test_logger_threshold_skips_lazy_message(self):
        logger = Logger("app", level=LogLevel.INFO)
        called = []
        logger.debug(lambda: called.append(True))
        self.assertEqual(called, [])

    def test_appender_thresholds_are_independent(self):
        logger = Logger("app", level=LogLevel.DEBUG)
        info_appender = MemoryAppender(LogLevel.INFO, SimpleFormatter())
        error_appender = MemoryAppender(LogLevel.ERROR, SimpleFormatter())
        logger.add_appender(info_appender)
        logger.add_appender(error_appender)

        logger.info("started")
        logger.error("failed")

        self.assertEqual(info_appender.lines, ["INFO: started", "ERROR: failed"])
        self.assertEqual(error_appender.lines, ["ERROR: failed"])

    def test_one_failing_appender_does_not_stop_next(self):
        class FailingAppender(MemoryAppender):
            def _write(self, formatted):
                raise RuntimeError("expected test error")

        logger = Logger("app", level=LogLevel.DEBUG)
        logger.add_appender(FailingAppender(LogLevel.DEBUG, SimpleFormatter()))
        working = MemoryAppender(LogLevel.DEBUG, SimpleFormatter())
        logger.add_appender(working)

        logger.error("still logged")
        self.assertEqual(working.lines, ["ERROR: still logged"])

    def test_file_appender_context_manager_closes_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "app.log"
            with FileAppender(str(path), LogLevel.DEBUG, SimpleFormatter()) as appender:
                appender.append(
                    type("Message", (), {"level": LogLevel.INFO, "message": "hello"})()
                )
            self.assertTrue(appender.file.closed)
            self.assertEqual(path.read_text(encoding="utf-8"), "INFO: hello\n")

    def test_concurrent_logger_creation_returns_same_instance(self):
        manager = LoggerManager.get_instance()
        results = []
        barrier = threading.Barrier(8)

        def worker():
            barrier.wait()
            results.append(manager.get_logger("shared"))

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(results), 8)
        self.assertTrue(all(item is results[0] for item in results))


if __name__ == "__main__":
    unittest.main()
