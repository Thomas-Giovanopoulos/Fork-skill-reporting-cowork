"""Logging JSON structuré — reprise verbatim de ``mcp-o2s-server/logging_config.py``.

Identique à dessein : les deux serveurs doivent produire des lignes de même
forme pour être lisibles dans le même agrégateur.
"""

import json
import logging
import sys


class _JSONFormatter(logging.Formatter):
    """Formatte chaque log en une ligne JSON — compatible avec les agrégateurs
    de logs (Azure Monitor, Grafana Loki, etc.)."""

    _SKIP = frozenset({
        "msg", "args", "levelno", "pathname", "filename", "module",
        "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "taskName", "message",
    })

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
        }
        entry.update({k: v for k, v in record.__dict__.items() if k not in self._SKIP})
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Configure le logging JSON sur stderr.

    Args:
        level: Niveau de log (INFO, WARNING, ERROR, DEBUG).
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_JSONFormatter())

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers = [handler]

    # Silence les logs verbeux des bibliothèques tierces
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
