import datetime
import json
from collections.abc import Callable, Iterator
from threading import Lock
from typing import TYPE_CHECKING, Any

from .enums import LogLevel
from .file_manager import FileManager

if TYPE_CHECKING:
    from .settings import Settings


class Logger:
    def __init__(
        self,
        log_file_path: str,
        settings: "Settings",
        ff_console_log_enable: bool = True,
    ):
        self.log_file_path = log_file_path
        self.publish_log: Callable[[str], Any] | None = None
        self.settings = settings
        self.ff_console_log_enable = ff_console_log_enable
        self._file_lock = Lock()

    def _should_log(self, level: LogLevel) -> bool:
        try:
            minimal_level = LogLevel(self.settings.PU_MIN_LOG_LEVEL)
        except ValueError:
            minimal_level = LogLevel.DEBUG
        return level.get_int_level() >= minimal_level.get_int_level()
    
    def _log(self, level: LogLevel, message: str, file_only: bool = False) -> None:
        if not self._should_log(level):
            return
            
        log_entry = {
            'level': level.value,
            'text': message,
            'create_datetime': datetime.datetime.now(datetime.UTC).isoformat(),
        }
        
        if self.ff_console_log_enable:
            print(log_entry)
        
        with self._file_lock:
            FileManager.append_ndjson_with_limit(
                self.log_file_path, log_entry, self.settings.PU_MAX_LOG_LENGTH
            )
        
        if not file_only and self.publish_log is not None:
            try:
                self.publish_log(json.dumps([log_entry]))
            except Exception:
                pass

    def debug(self, message: str, file_only: bool = False) -> None:
        self._log(LogLevel.DEBUG, message, file_only)
    
    def info(self, message: str, file_only: bool = False) -> None:
        self._log(LogLevel.INFO, message, file_only)
    
    def warning(self, message: str, file_only: bool = False) -> None:
        self._log(LogLevel.WARNING, message, file_only)
    
    def error(self, message: str, file_only: bool = False) -> None:
        self._log(LogLevel.ERROR, message, file_only)
    
    def critical(self, message: str, file_only: bool = False) -> None:
        self._log(LogLevel.CRITICAL, message, file_only)
    
    def get_full_log(self) -> list[dict[str, Any]]:
        return list(self.iter_log())

    def iter_log(self) -> Iterator[dict[str, Any]]:
        return FileManager.iter_ndjson(self.log_file_path)

    def reset_log(self) -> None:
        with self._file_lock, open(self.log_file_path, "w", encoding="utf-8"):
            pass
