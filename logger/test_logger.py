import threading

import pytest
from logger import (
    LogLevel, LogMessage, LogFormatter, DefaultFormatter, SimpleFormatter,
    LogAppender, ConsoleAppender, FileAppender, MemoryAppender,
    Logger, LoggerManager,
)


@pytest.fixture(autouse=True)
def fresh_manager():
    LoggerManager.reset()
    yield
    LoggerManager.reset()


def make_memory_appender(threshold=LogLevel.DEBUG):
    return MemoryAppender(threshold, SimpleFormatter())


class BadAppender(LogAppender):
    def _write(self, formatted):
        raise RuntimeError("disk on fire")


# ---------- LogLevel ----------

def test_level_ordering():
    assert LogLevel.DEBUG < LogLevel.INFO < LogLevel.WARN < LogLevel.ERROR < LogLevel.FATAL


def test_level_is_valid_true_for_all_levels():
    for level in (LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR, LogLevel.FATAL):
        assert LogLevel.is_valid(level) is True


def test_level_is_valid_false_for_bad_values():
    assert LogLevel.is_valid(0) is False
    assert LogLevel.is_valid(6) is False
    assert LogLevel.is_valid("INFO") is False
    assert LogLevel.is_valid(None) is False
    assert LogLevel.is_valid(True) is False


def test_level_name_of():
    assert LogLevel.name_of(LogLevel.WARN) == "WARN"
    assert LogLevel.name_of(LogLevel.FATAL) == "FATAL"


# ---------- LogMessage ----------

def test_log_message_fields():
    msg = LogMessage(LogLevel.INFO, "svc", "hello")

    assert msg.level == LogLevel.INFO
    assert msg.logger_name == "svc"
    assert msg.message == "hello"
    assert msg.timestamp is not None
    assert msg.thread_name == threading.current_thread().name


def test_log_message_captures_creating_thread_name():
    captured = {}

    def attempt():
        captured["msg"] = LogMessage(LogLevel.INFO, "svc", "hi")

    t = threading.Thread(target=attempt, name="worker-7")
    t.start()
    t.join()

    assert captured["msg"].thread_name == "worker-7"


# ---------- Formatters ----------

def test_default_formatter_contains_all_parts():
    msg = LogMessage(LogLevel.ERROR, "PaymentService", "failed")

    out = DefaultFormatter().format(msg)

    assert "[ERROR]" in out
    assert "PaymentService" in out
    assert msg.thread_name in out
    assert out.endswith("- failed")


def test_simple_formatter_output():
    msg = LogMessage(LogLevel.WARN, "svc", "careful")

    assert SimpleFormatter().format(msg) == "WARN: careful"


def test_base_formatter_format_not_implemented():
    with pytest.raises(NotImplementedError):
        LogFormatter().format(LogMessage(LogLevel.INFO, "svc", "x"))


# ---------- LogAppender ----------

def test_appender_invalid_threshold_raises():
    with pytest.raises(ValueError):
        MemoryAppender(99, SimpleFormatter())


def test_appender_invalid_formatter_raises():
    with pytest.raises(TypeError):
        MemoryAppender(LogLevel.INFO, "not a formatter")  # type: ignore


def test_appender_drops_message_below_threshold():
    appender = make_memory_appender(threshold=LogLevel.ERROR)

    appender.append(LogMessage(LogLevel.WARN, "svc", "minor"))

    assert appender.lines == []


def test_appender_accepts_message_at_threshold():
    appender = make_memory_appender(threshold=LogLevel.ERROR)

    appender.append(LogMessage(LogLevel.ERROR, "svc", "bad"))

    assert appender.lines == ["ERROR: bad"]


def test_appender_accepts_message_above_threshold():
    appender = make_memory_appender(threshold=LogLevel.ERROR)

    appender.append(LogMessage(LogLevel.FATAL, "svc", "worse"))

    assert appender.lines == ["FATAL: worse"]


def test_base_appender_write_not_implemented():
    appender = LogAppender(LogLevel.DEBUG, SimpleFormatter())

    with pytest.raises(NotImplementedError):
        appender.append(LogMessage(LogLevel.INFO, "svc", "x"))


# ---------- ConsoleAppender ----------

def test_console_appender_prints_formatted_line(capsys):
    appender = ConsoleAppender(LogLevel.DEBUG, SimpleFormatter())

    appender.append(LogMessage(LogLevel.INFO, "svc", "to console"))

    assert capsys.readouterr().out == "INFO: to console\n"


def test_console_appender_respects_threshold(capsys):
    appender = ConsoleAppender(LogLevel.ERROR, SimpleFormatter())

    appender.append(LogMessage(LogLevel.INFO, "svc", "quiet"))

    assert capsys.readouterr().out == ""


# ---------- FileAppender ----------

def test_file_appender_writes_line(tmp_path):
    path = str(tmp_path / "app.log")
    appender = FileAppender(path, LogLevel.DEBUG, SimpleFormatter())

    appender.append(LogMessage(LogLevel.INFO, "svc", "to file"))
    appender.close()

    with open(path) as f:
        assert f.read() == "INFO: to file\n"


def test_file_appender_appends_not_overwrites(tmp_path):
    path = str(tmp_path / "app.log")

    first = FileAppender(path, LogLevel.DEBUG, SimpleFormatter())
    first.append(LogMessage(LogLevel.INFO, "svc", "one"))
    first.close()

    second = FileAppender(path, LogLevel.DEBUG, SimpleFormatter())
    second.append(LogMessage(LogLevel.INFO, "svc", "two"))
    second.close()

    with open(path) as f:
        assert f.read().splitlines() == ["INFO: one", "INFO: two"]


def test_file_appender_respects_threshold(tmp_path):
    path = str(tmp_path / "app.log")
    appender = FileAppender(path, LogLevel.ERROR, SimpleFormatter())

    appender.append(LogMessage(LogLevel.INFO, "svc", "skip me"))
    appender.append(LogMessage(LogLevel.ERROR, "svc", "keep me"))
    appender.close()

    with open(path) as f:
        assert f.read().splitlines() == ["ERROR: keep me"]


def test_file_appender_empty_path_raises():
    with pytest.raises(ValueError):
        FileAppender("", LogLevel.DEBUG, SimpleFormatter())


# ---------- Logger: levels ----------

def test_logger_default_level_is_info():
    assert Logger("svc").level == LogLevel.INFO


def test_logger_drops_message_below_logger_level():
    logger = Logger("svc")                       # INFO
    appender = make_memory_appender()
    logger.add_appender(appender)

    logger.debug("too detailed")

    assert appender.lines == []


def test_logger_passes_message_at_logger_level():
    logger = Logger("svc")
    appender = make_memory_appender()
    logger.add_appender(appender)

    logger.info("ok")

    assert appender.lines == ["INFO: ok"]


def test_logger_set_level_changes_filtering():
    logger = Logger("svc")
    appender = make_memory_appender()
    logger.add_appender(appender)

    logger.set_level(LogLevel.DEBUG)
    logger.debug("now visible")

    assert appender.lines == ["DEBUG: now visible"]


def test_logger_set_invalid_level_raises():
    logger = Logger("svc")

    with pytest.raises(ValueError):
        logger.set_level(42)


def test_logger_log_invalid_level_raises():
    logger = Logger("svc")

    with pytest.raises(ValueError):
        logger.log(42, "msg")


def test_logger_helper_methods_use_correct_levels():
    logger = Logger("svc", LogLevel.DEBUG)
    appender = make_memory_appender()
    logger.add_appender(appender)

    logger.debug("a")
    logger.info("b")
    logger.warn("c")
    logger.error("d")
    logger.fatal("e")

    assert appender.lines == ["DEBUG: a", "INFO: b", "WARN: c", "ERROR: d", "FATAL: e"]


# ---------- Logger: appenders ----------

def test_logger_with_no_appenders_does_not_crash():
    Logger("svc").info("nobody is listening")


def test_logger_sends_to_all_appenders():
    logger = Logger("svc")
    a1 = make_memory_appender()
    a2 = make_memory_appender()
    logger.add_appender(a1)
    logger.add_appender(a2)

    logger.info("hello")

    assert a1.lines == ["INFO: hello"]
    assert a2.lines == ["INFO: hello"]


def test_logger_each_appender_has_own_threshold():
    logger = Logger("svc", LogLevel.DEBUG)
    everything = make_memory_appender(LogLevel.DEBUG)
    errors_only = make_memory_appender(LogLevel.ERROR)
    logger.add_appender(everything)
    logger.add_appender(errors_only)

    logger.info("routine")
    logger.error("broken")

    assert everything.lines == ["INFO: routine", "ERROR: broken"]
    assert errors_only.lines == ["ERROR: broken"]


def test_logger_add_invalid_appender_raises():
    logger = Logger("svc")

    with pytest.raises(TypeError):
        logger.add_appender("not an appender")  # type: ignore


def test_logger_remove_appender_stops_delivery():
    logger = Logger("svc")
    appender = make_memory_appender()
    logger.add_appender(appender)

    assert logger.remove_appender(appender) is True
    logger.info("after removal")

    assert appender.lines == []


def test_logger_remove_unknown_appender_returns_false():
    logger = Logger("svc")

    assert logger.remove_appender(make_memory_appender()) is False


def test_failing_appender_does_not_block_other_appenders(capsys):
    logger = Logger("svc")
    good = make_memory_appender()
    logger.add_appender(BadAppender(LogLevel.DEBUG, SimpleFormatter()))
    logger.add_appender(good)

    logger.info("still delivered")

    assert good.lines == ["INFO: still delivered"]
    out = capsys.readouterr().out
    assert "BadAppender" in out
    assert "disk on fire" in out


# ---------- Logger: message handling ----------

def test_logger_converts_non_string_message():
    logger = Logger("svc")
    appender = make_memory_appender()
    logger.add_appender(appender)

    logger.info(404)

    assert appender.lines == ["INFO: 404"]


def test_logger_lazy_message_not_built_when_filtered():
    logger = Logger("svc")                       # INFO, so DEBUG is filtered
    calls = []

    def expensive():
        calls.append(1)
        return "costly"

    logger.debug(expensive)

    assert calls == []


def test_logger_lazy_message_built_when_enabled():
    logger = Logger("svc")
    appender = make_memory_appender()
    logger.add_appender(appender)
    calls = []

    def expensive():
        calls.append(1)
        return "costly"

    logger.info(expensive)

    assert calls == [1]
    assert appender.lines == ["INFO: costly"]


def test_logger_lazy_message_built_once_for_many_appenders():
    logger = Logger("svc")
    logger.add_appender(make_memory_appender())
    logger.add_appender(make_memory_appender())
    calls = []

    logger.info(lambda: calls.append(1) or "x")

    assert len(calls) == 1


# ---------- LoggerManager ----------

def test_manager_is_singleton():
    assert LoggerManager.get_instance() is LoggerManager.get_instance()


def test_manager_reset_gives_new_instance():
    first = LoggerManager.get_instance()

    LoggerManager.reset()

    assert LoggerManager.get_instance() is not first


def test_manager_same_name_returns_same_logger():
    manager = LoggerManager.get_instance()

    assert manager.get_logger("svc") is manager.get_logger("svc")


def test_manager_different_names_return_different_loggers():
    manager = LoggerManager.get_instance()

    assert manager.get_logger("a") is not manager.get_logger("b")


def test_manager_logger_has_correct_name_and_default_level():
    logger = LoggerManager.get_instance().get_logger("svc")

    assert logger.name == "svc"
    assert logger.level == LogLevel.INFO


def test_manager_empty_name_raises():
    with pytest.raises(ValueError):
        LoggerManager.get_instance().get_logger("")


def test_manager_whitespace_name_raises():
    with pytest.raises(ValueError):
        LoggerManager.get_instance().get_logger("   ")


def test_manager_non_string_name_raises():
    with pytest.raises(ValueError):
        LoggerManager.get_instance().get_logger(123)  # type: ignore


def test_manager_config_persists_across_lookups():
    LoggerManager.get_instance().get_logger("svc").set_level(LogLevel.ERROR)

    assert LoggerManager.get_instance().get_logger("svc").level == LogLevel.ERROR


# ---------- End to end ----------

def test_end_to_end_console_and_file(tmp_path, capsys):
    path = str(tmp_path / "app.log")
    logger = LoggerManager.get_instance().get_logger("PaymentService")
    logger.set_level(LogLevel.DEBUG)
    file_appender = FileAppender(path, LogLevel.ERROR, DefaultFormatter())
    logger.add_appender(ConsoleAppender(LogLevel.DEBUG, SimpleFormatter()))
    logger.add_appender(file_appender)

    logger.info("Payment started")
    logger.error("Payment failed")
    file_appender.close()

    console_lines = capsys.readouterr().out.splitlines()
    assert console_lines == ["INFO: Payment started", "ERROR: Payment failed"]

    with open(path) as f:
        file_lines = f.read().splitlines()
    assert len(file_lines) == 1
    assert "Payment failed" in file_lines[0]


# ---------- Concurrency ----------

def test_concurrent_get_logger_returns_single_instance():
    """Many threads ask for the SAME logger name at once. All must get the
    same object, and only one Logger should ever be created."""
    manager = LoggerManager.get_instance()
    results = []
    results_lock = threading.Lock()

    def attempt():
        logger = manager.get_logger("svc")
        with results_lock:
            results.append(logger)

    threads = [threading.Thread(target=attempt) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 50
    assert all(r is results[0] for r in results)
    assert len(manager.loggers) == 1


def test_concurrent_get_instance_returns_single_manager():
    results = []
    results_lock = threading.Lock()

    def attempt():
        m = LoggerManager.get_instance()
        with results_lock:
            results.append(m)

    threads = [threading.Thread(target=attempt) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(r is results[0] for r in results)


def test_concurrent_logging_no_lost_messages():
    """Many threads log at the same time. Every message must arrive exactly once."""
    logger = Logger("svc")
    appender = make_memory_appender()
    logger.add_appender(appender)

    def attempt(i):
        for j in range(20):
            logger.info(f"t{i}-m{j}")

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(appender.lines) == 200
    assert len(set(appender.lines)) == 200


def test_concurrent_add_appender_no_lost_appenders():
    """Many threads add appenders at once. Copy-on-write under a lock must
    not lose any of them."""
    logger = Logger("svc")

    def attempt():
        logger.add_appender(make_memory_appender())

    threads = [threading.Thread(target=attempt) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(logger.appenders) == 50


def test_concurrent_file_writes_lines_not_interleaved(tmp_path):
    """Many threads write to ONE file appender. Every line must be intact."""
    path = str(tmp_path / "app.log")
    logger = Logger("svc")
    file_appender = FileAppender(path, LogLevel.DEBUG, SimpleFormatter())
    logger.add_appender(file_appender)

    def attempt(i):
        for j in range(20):
            logger.info(f"thread-{i}-message-{j}")

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    file_appender.close()

    with open(path) as f:
        lines = f.read().splitlines()

    assert len(lines) == 200
    assert all(line.startswith("INFO: thread-") for line in lines)
    assert len(set(lines)) == 200


def test_logging_while_appenders_are_being_added():
    """Reading the appender list while another thread replaces it must not crash."""
    logger = Logger("svc")
    stop = threading.Event()
    errors = []

    def writer():
        try:
            while not stop.is_set():
                logger.info("msg")
        except Exception as e:
            errors.append(e)

    t = threading.Thread(target=writer)
    t.start()
    for _ in range(100):
        logger.add_appender(make_memory_appender())
    stop.set()
    t.join()

    assert errors == []
