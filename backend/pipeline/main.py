from pathlib import Path

import polars as pl
from dotenv import load_dotenv
from prefect import flow, task
from prefect.cache_policies import NO_CACHE

from backend.pipeline.src.base_logger import logger
from backend.pipeline.src.data_transforms import ChessDataTransforms
import backend.agent.agent_run as agent_run

load_dotenv(Path(__file__).parent.parent.parent / "secrets.env")


@task(cache_policy=NO_CACHE)
def fetch_chess_data(chess_transforms: ChessDataTransforms) -> None:
    logger.info("--- Stage 1: Fetching raw chess data ---")
    chess_transforms.fetch_raw_data()


@task(cache_policy=NO_CACHE)
def clean_chess_data(chess_transforms: ChessDataTransforms) -> pl.DataFrame:
    logger.info("--- Stage 2: Cleaning chess data ---")
    return chess_transforms.clean_data()


@task(cache_policy=NO_CACHE)
def run_stockfish_evals(chess_transforms: ChessDataTransforms, df: pl.DataFrame) -> Path:
    logger.info("--- Stage 3: Running Stockfish evaluations ---")
    return chess_transforms.stockfish_evals(df)


@task
def cleanup_initial_data(path: Path) -> None:
    logger.info(f"--- Stage 4: Removing raw data file {path} ---")
    path.unlink(missing_ok=True)


@task
def run_agent(parquet_path: Path) -> None:
    logger.info(f"--- Stage 5: Running agent on {parquet_path} ---")
    agent_run.main(parquet_path)


@flow
def main():
    """
    Main pipeline: fetch chess data, run Stockfish evals, then generate and
    send the weekly chess report via the agent.
    """
    chess_transforms = ChessDataTransforms()
    fetch_chess_data(chess_transforms)
    df = clean_chess_data(chess_transforms)
    parquet_path = run_stockfish_evals(chess_transforms, df)
    cleanup_initial_data(chess_transforms.initial_chess_data)
    run_agent(parquet_path)
    logger.info(f"Pipeline complete — {len(df)} games processed, report sent")


if __name__ == "__main__":
    main.serve(
        name="chess-weekly-report",
        cron="0 9 * * 1", 
    )

