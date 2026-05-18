import chess.pgn
import io
from stockfish import Stockfish
from pathlib import Path
from data_ops import ChessDataOps
import tqdm

CHESS_COLUMNS = [
    # "url",
    "pgn",
    # "time_control",
    # "end_time",
    # "rated",
    # "accuracies",
    # "tcn",
    # "uuid",
    # "initial_setup",
    # "fen",
    # "time_class",
    # "rules",
    # "white",
    # "black",
    # "eco"
]

stockfish_path = Path(r"C:\Users\Chris\stockfish\stockfish-windows-x86-64-avx2.exe")
stockfish = Stockfish(path = str(stockfish_path))
stockfish.set_depth(10)
chess_ops = ChessDataOps()

if __name__ == "__main__":
    chess_data_file_path = Path("chess_data.parquet")
    user_input = str(input("Ready for new data? y/n: "))
    if user_input == "y":
        chess_ops.save_data(chess_data_file_path)
    elif user_input == 'n':
        print("No new save needed!")
    else:
        print("Pick y or n")

    rel = chess_ops.get_rel_from_parquet(chess_data_file_path)
    url_not_null = rel.filter("url IS NOT NULL").select(*CHESS_COLUMNS)
    df = url_not_null.pl()
    for idx, i in tqdm.tqdm(enumerate(df.iter_rows())):
        pgn_string = i[0]
        print(f"Game: {idx}\nPGN: {pgn_string}")
        pgn = io.StringIO(pgn_string)
        game = chess.pgn.read_game(pgn)
        
        if game is None:
            print("Failed to parse PGN")
        else:
            board = game.board()
            for idx, move in enumerate(game.mainline_moves()):
                board.push(move)
                stockfish.set_fen_position(board.fen())
                eval_info = stockfish.get_evaluation()
                print(f"Index: {idx+1}")
                print(f"Move: {move}")
                print(f"Evaluation: {eval_info}\n")
