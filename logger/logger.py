from typing import Optional, Dict, List
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
    def is_valid(level) -> bool:
        return isinstance(level, int) and not isinstance(level, bool) and level in LogLevel.NAMES

    @staticmethod
    def name_of(level: int) -> str:
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
        return (f"{time_str} [{LogLevel.name_of(msg.level)}] "
                f"{msg.logger_name} ({msg.thread_name}) - {msg.message}")


class SimpleFormatter(LogFormatter):
    def format(self, msg: LogMessage) -> str:
        return f"{LogLevel.name_of(msg.level)}: {msg.message}"


# ---------- Appenders (Template Method) ----------

class LogAppender:
    def __init__(self, threshold: int, formatter: LogFormatter):
        if not LogLevel.is_valid(threshold):
            raise ValueError("invalid threshold level.")
        if not isinstance(formatter, LogFormatter):
            raise TypeError("Expected a LogFormatter instance")
        self.threshold = threshold
        self.formatter = formatter

    def append(self, msg: LogMessage) -> None:
        # template method: filtering lives here, subclasses only write
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

    def _write(self, formatted: str) -> None:
        with self.lock:                      # protects the shared file handle
            self.file.write(formatted + "\n")
            self.file.flush()

    def close(self) -> None:
        with self.lock:
            self.file.close()


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

class Logger:
    def __init__(self, name: str, level: int = LogLevel.INFO):
        self.name = name
        self.level = level
        self.appenders: List[LogAppender] = []
        self.lock = threading.Lock()

    def set_level(self, level: int) -> None:
        if not LogLevel.is_valid(level):
            raise ValueError("invalid log level.")
        self.level = level

    def add_appender(self, appender: LogAppender) -> None:
        if not isinstance(appender, LogAppender):
            raise TypeError("Expected a LogAppender instance")
        with self.lock:
            # copy-on-write: build a new list, readers keep using the old one
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

        if level < self.level:               # cheap early exit, nothing is built
            return

        if callable(message):                # lazy message, only built when enabled
            message = message()
        msg = LogMessage(level, self.name, str(message))

        for appender in self.appenders:      # iterates a snapshot, no lock needed
            try:
                appender.append(msg)
            except Exception as e:           # one bad appender must not stop others
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
                if cls._instance is None:    # double-checked locking
                    cls._instance = LoggerManager()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        # drops the singleton, mainly so tests start clean
        with cls._instance_lock:
            cls._instance = None

    def get_logger(self, name: str) -> Logger:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("logger name is empty or invalid.")
        with self.lock:
            if name not in self.loggers:
                self.loggers[name] = Logger(name)
            return self.loggers[name]
