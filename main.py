from pathlib import Path
from datetime import date
from prefect import flow
from data_transforms import ChessDataTransforms

@flow
def main():
    chess_transforms = ChessDataTransforms()
    chess_transforms.clean_data()

if __name__ == "__main__":
    main()
    file_to_remove = Path(f"initial_chess_data_{date.today().isoformat()}.parquet")
    print(f'Removing {file_to_remove}')
    file_to_remove.unlink(missing_ok=True)

