import duckdb
from pathlib import Path

duckdb_conn = duckdb.connect()
file_path = Path('data\cleaned_chess_data_2026-05-18.parquet')


file_name = str(file_path)
rel = duckdb_conn.from_parquet(file_name)
rel.show()