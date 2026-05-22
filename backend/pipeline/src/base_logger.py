import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

_log_dir = Path(__file__).parent.parent / "logs"
_log_dir.mkdir(exist_ok=True)


class _NewRelicHandler(logging.Handler):
    """Forwards log records to the New Relic Logs API."""

    _URL = "https://log-api.newrelic.com/log/v1"

    def __init__(self) -> None:
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        api_key = os.getenv("NEW_RELIC_LICENSE_KEY", "")
        if not api_key:
            return
        payload = [
            {
                "logs": [
                    {
                        "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                        "message": self.format(record),
                        "attributes": {
                            "level": record.levelname,
                            "logger": record.name,
                            "service": "chess-pipeline",
                        },
                    }
                ]
            }
        ]
        try:
            requests.post(
                self._URL,
                headers={"Api-Key": api_key, "Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=5,
            )
        except Exception:
            pass 


_fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger("chess_pipeline")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _fh = logging.FileHandler(_log_dir / "chess_pipeline.log")
    _fh.setFormatter(_fmt)
    _sh = logging.StreamHandler()
    _sh.setFormatter(_fmt)
    _nr = _NewRelicHandler()
    _nr.setFormatter(_fmt)
    logger.addHandler(_fh)
    logger.addHandler(_sh)
    logger.addHandler(_nr)
    logger.propagate = False