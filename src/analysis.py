import duckdb
from pathlib import Path

duckdb_conn = duckdb.connect()
file_path = Path('data\cleaned_chess_data_2026-05-18.parquet')


file_name = str(file_path)
rel = duckdb_conn.from_parquet(file_name)
data = rel.query("t", """
SELECT 
    Game_Number,
    Game_Link,
    Move_Number,
    Move,
    Evaluation,
    White,
    Black,
    Start_Date,
    Start_Time,
    End_Date,
    End_Time,
    --Will create a lag to calc some centipawn info LAG()
FROM t 
WHERE Game_Number = 1
""")
print(data)