from pathlib import Path
from datetime import date
from prefect import flow
from backend.pipeline.src.data_transforms import ChessDataTransforms
from backend.pipeline.src.base_logger import logger

@flow
def main():
    """
    Main pipeline to run the flow of my chess data
    """
    
    chess_transforms = ChessDataTransforms()
    chess_transforms.stockfish_evals()

if __name__ == "__main__":
    main()
    file_to_remove = Path(__file__).parent / "data" / f"initial_chess_data_{date.today().isoformat()}.parquet"
    logger.info(f'Removing {file_to_remove}')
    file_to_remove.unlink(missing_ok=True)

