import chess.pgn
import io
from stockfish import Stockfish
from pathlib import Path
from backend.pipeline.src.data_ops import ChessDataOps
import polars as pl
from datetime import date
from backend.pipeline.src.base_logger import logger

chess_ops = ChessDataOps()
class ChessDataTransforms():
    """
    A class representing data transformations for chess data

    Attributes:
        initial_chess_data (Path): The Path object for the initial chess data we are pulling
        cleaned_chess_data (Path): The Path object for the cleaned chess data
        stockfish (Stockfish): Initialize stockfish

    """
    def __init__(self):
        stockfish_path = Path(r"C:\Users\Chris\stockfish\stockfish-windows-x86-64-avx2.exe")
        self.stockfish = Stockfish(path = str(stockfish_path))
        self.stockfish.set_depth(10)
        
        today = date.today().isoformat()
        _pipeline_dir = Path(__file__).parent.parent
        self.initial_chess_data = _pipeline_dir / "data" / f"initial_chess_data_{today}.parquet"
        self.cleaned_chess_data = _pipeline_dir / "data" / f"cleaned_chess_data_{today}.parquet"
    
    def clean_data(self) -> None:
        """
        Cleans up the initital chess data, and adds evals from stockfish
        Args:
            None
        Returns:
            None
        """
        
        chess_ops.save_data(self.initial_chess_data)
        rel = chess_ops.get_rel_from_parquet(self.initial_chess_data)
        pgn_not_null = rel.filter("pgn IS NOT NULL").select("pgn")
        df = pgn_not_null.pl()
        game_data_list = []
        for game_number, i in enumerate(df.iter_rows(), start=1):
            pgn_string = i[0]
            pgn = io.StringIO(pgn_string)
            game = chess.pgn.read_game(pgn)
            if game is None:
                logger.info("Failed to parse PGN")
            else:
                board = game.board()
                headers = game.headers
                for move_number, move in enumerate(game.mainline_moves(), start=1):
                    board.push(move)
                    self.stockfish.set_fen_position(board.fen())
                    eval_info = self.stockfish.get_evaluation()
                    wdl_stats =  self.stockfish.get_wdl_stats()
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
        transformed_data = pl.DataFrame(game_data_list)
        transformed_data.write_parquet(file = self.cleaned_chess_data)
        return None
        