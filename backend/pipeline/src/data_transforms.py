import chess.pgn
import io
import os
from stockfish import Stockfish
from pathlib import Path
from backend.pipeline.src.data_ops import ChessDataOps
import polars as pl
from datetime import date
from backend.pipeline.src.base_logger import logger
import tqdm

class ChessDataTransforms():
    """
    A class representing data transformations for chess data

    Attributes:
        initial_chess_data (Path): The Path object for the initial chess data we are pulling
        cleaned_chess_data (Path): The Path object for the cleaned chess data
        stockfish (Stockfish): Initialize stockfish

    """
    def __init__(self, username: str = "chesswizinterm"):
        self.chess_ops = ChessDataOps(username = username)
        stockfish_path = Path(
            os.getenv("STOCKFISH_PATH", r"C:\Users\Chris\stockfish\stockfish-windows-x86-64-avx2.exe")
        )
        self._stockfish_depth = 18
        logger.info(f"Initializing Stockfish from {stockfish_path} at depth {self._stockfish_depth}")
        self.stockfish = Stockfish(path = str(stockfish_path))
        self.stockfish.set_depth(self._stockfish_depth)
        
        today = date.today().isoformat()
        _pipeline_dir = Path(__file__).parent.parent
        _data_dir = _pipeline_dir / "data"
        _data_dir.mkdir(parents=True, exist_ok=True)
        self.initial_chess_data = _data_dir / f"initial_chess_data_{today}.parquet"
        self.cleaned_chess_data = _data_dir / f"cleaned_chess_data_{today}.parquet"
    
    def fetch_raw_data(self) -> None:
        """
        Fetches raw chess data from chess.com and saves to parquet.
        Args:
            None
        Returns:
            None
        """
        logger.info(f"Fetching raw chess data for {self.chess_ops.username}")
        self.chess_ops.save_data(self.initial_chess_data)
        logger.info(f"Saved raw data to {self.initial_chess_data}")

    def clean_data(self) -> pl.DataFrame:
        """
        Cleans up the initial chess data. Requires fetch_raw_data() to have run first.
        Args:
            None
        Returns:
            df: Cleaned chess data with non-null PGNs
        """
        rel = self.chess_ops.get_rel_from_parquet(self.initial_chess_data)
        pgn_not_null = rel.filter("pgn IS NOT NULL").select("pgn")
        df = pgn_not_null.pl()
        logger.info(f"Cleaned data: {len(df)} games with valid PGN")
        return df

    def analyze_game(self, df: pl.DataFrame):
        for game_number, i in enumerate(df.iter_rows(), start=1):
            pgn_string = i[0]
            pgn = io.StringIO(pgn_string)
            game = chess.pgn.read_game(pgn)
            yield game

    def stockfish_evals(self, df: pl.DataFrame) -> Path:
        """
        Adds evals from stockfish and saves to parquet
        Args:
            None
        Returns:
            None
        """
        logger.info(f"Running Stockfish evals (depth={self._stockfish_depth})")
        game_data_list = []
        game_bar = tqdm.tqdm(enumerate(self.analyze_game(df), start=1), total=len(df), desc="Games", unit="game")
        for game_number, game in game_bar:
            if game is None:
                logger.warning(f"Failed to parse PGN for game {game_number}")
            else:
                board = game.board()
                headers = game.headers
                white = headers.get('White', '?')
                black = headers.get('Black', '?')
                game_bar.set_postfix(white=white, black=black)
                logger.debug(f"Evaluating game {game_number}: {white} vs {black}")
                total_moves = game.end().ply()
                for move_number, move in tqdm.tqdm(enumerate(game.mainline_moves(), start=1), total=total_moves, desc=f"G{game_number}", unit="mv", leave=False):
                    board.push(move)
                    self.stockfish.set_fen_position(board.fen())
                    wdl_stats = self.stockfish.get_wdl_stats()
                    eval_info = self.stockfish.get_evaluation()
                    if wdl_stats is None or eval_info is None:
                        logger.warning(f"Stockfish returned None for game {game_number}, move {move_number}")
                    game_info = {
                        "Game_Number": game_number,
                        "Game_Link": headers['Link'],
                        "Move_Number": move_number,
                        "Move": str(move),
                        "Evaluation": eval_info,
                        "WDL Stats": wdl_stats,
                        "White": headers['White'],
                        "Black": headers['Black'],
                        "Start_Date": headers['Date'],
                        'Start_Time': headers['StartTime'],
                        "End_Date": headers['EndDate'],
                        'End_Time': headers['EndTime']
                        
                    }
                    game_data_list.append(game_info)
                logger.info(f"Game {game_number} processed ({move_number} moves)")
        transformed_data = pl.DataFrame(game_data_list)
        transformed_data.write_parquet(file=self.cleaned_chess_data)
        logger.info(f"Saved {len(game_data_list)} move records to {self.cleaned_chess_data}")
        return self.cleaned_chess_data


