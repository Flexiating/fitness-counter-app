import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock


_CONFIGURATION_LOCK = Lock()
_configured = False


def _configure_logging() -> None:
    global _configured
    if _configured:
        return
    with _CONFIGURATION_LOCK:
        if _configured:
            return

        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        root_logger.addHandler(console)

        try:
            log_path = Path("logs") / "app.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=2 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except OSError as exc:
            root_logger.warning("File logging is unavailable: %s", exc)

        _configured = True


def get_logger(name: str) -> logging.Logger:
    _configure_logging()
    return logging.getLogger(name)
