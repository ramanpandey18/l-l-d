from typing import Optional, Dict, List, Callable, Union, Any
from datetime import datetime
import threading


class LogLevel:
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4
    FATAL = 5

    NAMES = {1: "DEBUG", 2: "INFO", 3: "WARN", 4: "ERROR", 5: "FATAL"}

    @staticmethod
    def is_valid(level: Any) -> bool:
        # bool is a subclass of int, so explicitly reject True and False.
        return isinstance(level, int) and not isinstance(level, bool) and level in LogLevel.NAMES

    @staticmethod
    def name_of(level: int) -> str:
        if not LogLevel.is_valid(level):
            raise ValueError("invalid log level.")
        return LogLevel.NAMES[level]


class LogMessage:
    def __init__(self, level: int, logger_name: str, message: str):
        self.level = level
        self.logger_name = logger_name
        self.message = message
        self.timestamp = datetime.now()
        self.thread_name = threading.current_thread().name


# ---------- Formatters (Strategy) ----------

class LogFormatter:
    def format(self, msg: LogMessage) -> str:
        raise NotImplementedError("subclasses must implement format")


class DefaultFormatter(LogFormatter):
    def format(self, msg: LogMessage) -> str:
        time_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"{time_str} [{LogLevel.name_of(msg.level)}] "
            f"{msg.logger_name} ({msg.thread_name}) - {msg.message}"
        )


class SimpleFormatter(LogFormatter):
    def format(self, msg: LogMessage) -> str:
        return f"{LogLevel.name_of(msg.level)}: {msg.message}"


# ---------- Appenders (Template Method style) ----------

class LogAppender:
    def __init__(self, threshold: int, formatter: LogFormatter):
        if not LogLevel.is_valid(threshold):
            raise ValueError("invalid threshold level.")
        if not isinstance(formatter, LogFormatter):
            raise TypeError("Expected a LogFormatter instance")
        self.threshold = threshold
        self.formatter = formatter

    def append(self, msg: LogMessage) -> None:
        # Common workflow: filter, format, then delegate destination-specific writing.
        if msg.level >= self.threshold:
            self._write(self.formatter.format(msg))

    def _write(self, formatted: str) -> None:
        raise NotImplementedError("subclasses must implement _write")


class ConsoleAppender(LogAppender):
    def _write(self, formatted: str) -> None:
        print(formatted)


class FileAppender(LogAppender):
    def __init__(self, path: str, threshold: int, formatter: LogFormatter):
        if not isinstance(path, str) or not path.strip():
            raise ValueError("file path is empty or invalid.")
        super().__init__(threshold, formatter)
        self.file = open(path, "a", encoding="utf-8")
        self.lock = threading.Lock()
        self._closed = False

    def _write(self, formatted: str) -> None:
        with self.lock:
            if self._closed:
                raise ValueError("I/O operation on closed log file.")
            self.file.write(formatted + "\n")
            self.file.flush()

    def close(self) -> None:
        with self.lock:
            if not self._closed:
                self.file.close()
                self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False


class MemoryAppender(LogAppender):
    """Keeps formatted lines in a list. Handy for tests and quick debugging."""

    def __init__(self, threshold: int, formatter: LogFormatter):
        super().__init__(threshold, formatter)
        self.lines: List[str] = []
        self.lock = threading.Lock()

    def _write(self, formatted: str) -> None:
        with self.lock:
            self.lines.append(formatted)


# ---------- Logger ----------

Message = Union[str, Callable[[], Any], Any]


class Logger:
    def __init__(self, name: str, level: int = LogLevel.INFO):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("logger name is empty or invalid.")
        if not LogLevel.is_valid(level):
            raise ValueError("invalid log level.")

        self.name = name
        self.level = level
        self.appenders: List[LogAppender] = []
        self.lock = threading.Lock()

    def set_level(self, level: int) -> None:
        if not LogLevel.is_valid(level):
            raise ValueError("invalid log level.")
        with self.lock:
            self.level = level

    def add_appender(self, appender: LogAppender) -> None:
        if not isinstance(appender, LogAppender):
            raise TypeError("Expected a LogAppender instance")
        with self.lock:
            # Copy-on-write: readers can safely retain an earlier list snapshot.
            self.appenders = self.appenders + [appender]

    def remove_appender(self, appender: LogAppender) -> bool:
        with self.lock:
            if appender not in self.appenders:
                return False
            self.appenders = [a for a in self.appenders if a is not appender]
            return True

    def log(self, level: int, message) -> None:
        if not LogLevel.is_valid(level):
            raise ValueError("invalid log level.")

        # Take a consistent snapshot of the threshold and appenders. Do not hold
        # the lock while evaluating a lazy message or writing to destinations.
        with self.lock:
            logger_level = self.level
            appenders_snapshot = self.appenders

        if level < logger_level:
            return

        if callable(message):
            message = message()

        msg = LogMessage(level, self.name, str(message))

        for appender in appenders_snapshot:
            try:
                appender.append(msg)
            except Exception as e:
                # A failing appender must not prevent other appenders from running.
                print(f"Appender {type(appender).__name__} failed: {e}")

    def debug(self, message) -> None:
        self.log(LogLevel.DEBUG, message)

    def info(self, message) -> None:
        self.log(LogLevel.INFO, message)

    def warn(self, message) -> None:
        self.log(LogLevel.WARN, message)

    def error(self, message) -> None:
        self.log(LogLevel.ERROR, message)

    def fatal(self, message) -> None:
        self.log(LogLevel.FATAL, message)


# ---------- LoggerManager (Singleton + Factory) ----------

class LoggerManager:
    _instance: Optional["LoggerManager"] = None
    _instance_lock = threading.Lock()

    def __init__(self):
        self.loggers: Dict[str, Logger] = {}
        self.lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "LoggerManager":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        # Intended mainly for tests. Existing references to the old manager/loggers
        # remain valid; this only clears the class-level singleton reference.
        with cls._instance_lock:
            cls._instance = None

    def get_logger(self, name: str) -> Logger:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("logger name is empty or invalid.")
        with self.lock:
            if name not in self.loggers:
                self.loggers[name] = Logger(name)
            return self.loggers[name]
