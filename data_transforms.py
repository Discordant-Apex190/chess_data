import chess.pgn
import io
from stockfish import Stockfish
from pathlib import Path
from data_ops import ChessDataOps
import tqdm
import polars as pl
from datetime import date

stockfish_path = Path(r"C:\Users\Chris\stockfish\stockfish-windows-x86-64-avx2.exe")
stockfish = Stockfish(path = str(stockfish_path))
stockfish.set_depth(10)
chess_ops = ChessDataOps()

class ChessDataTransforms():
    def __init__(self):
        today = date.today().isoformat()
        self.initial_chess_data = Path(f"data/initial_chess_data_{today}.parquet")
        self.cleaned_chess_data = Path(f"data/cleaned_chess_data_{today}.parquet")
    
    def clean_data(self) -> None:
        chess_ops.save_data(self.initial_chess_data)
        rel = chess_ops.get_rel_from_parquet(self.initial_chess_data)
        url_not_null = rel.filter("url IS NOT NULL").select("pgn")
        df = url_not_null.pl()
        game_data_list = []
        for game_number, i in tqdm.tqdm(enumerate(df.iter_rows(), start=1)):
            pgn_string = i[0]
            pgn = io.StringIO(pgn_string)
            game = chess.pgn.read_game(pgn)
            if game is None:
                print("Failed to parse PGN")
            else:
                board = game.board()
                headers = game.headers
                for move_number, move in enumerate(game.mainline_moves(), start=1):
                    board.push(move)
                    stockfish.set_fen_position(board.fen())
                    eval_info = stockfish.get_evaluation()
                    game_info = {
                        "Game_Number": game_number,
                        "Game_Link": headers['Link'],
                        "Move Number": move_number,
                        "Move": str(move),
                        "Evaluation": eval_info,
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
        