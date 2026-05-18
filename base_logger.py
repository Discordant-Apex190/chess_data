import logging
from pathlib import Path

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "chess_pipeline.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)