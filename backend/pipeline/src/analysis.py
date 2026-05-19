import duckdb
from pathlib import Path

duckdb_conn = duckdb.connect()
file_path = Path('backend/pipeline/data/cleaned_chess_data_2026-05-19.parquet')


file_name = str(file_path)
rel = duckdb_conn.from_parquet(file_name)
data = rel.query("t", """
WITH move_analysis AS (
    SELECT 
        Game_Number,
        Game_Link,
        Move_Number,
        Move,
        Evaluation.type AS Evaluation_Type,
        Evaluation.value AS Evaluation_Value,
        "WDL Stats",
        Start_Date,
        Start_Time,
        End_Date,
        End_Time,
        CASE 
            WHEN Move_Number % 2 = 1 THEN White
            ELSE Black
        END AS Player_To_Move,
        CASE 
            WHEN Move_Number % 2 = 1 THEN 
                LAG(Evaluation.value, 1) OVER (
                    PARTITION BY Game_Number 
                    ORDER BY Move_Number
                ) - Evaluation.value
            ELSE 
                Evaluation.value - LAG(Evaluation.value, 1) OVER (
                    PARTITION BY Game_Number 
                    ORDER BY Move_Number
                )
        END AS CentiPawnLoss
    FROM t
)
SELECT 
    *,
    AVG(CentiPawnLoss) FILTER (
        WHERE Move_Number % 2 = 1 
        AND CentiPawnLoss > 0 
    ) OVER (PARTITION BY Game_Number) AS ACPL_White,
    
    AVG(CentiPawnLoss) FILTER (
        WHERE Move_Number % 2 = 0 
        AND CentiPawnLoss > 0
    ) OVER (PARTITION BY Game_Number) AS ACPL_Black
FROM move_analysis
ORDER BY Game_Number, Move_Number
""")
print(data)

