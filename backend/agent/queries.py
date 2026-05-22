ANALYSIS_SQL = """
WITH move_analysis AS (
    SELECT
        Game_Number, Game_Link, Move_Number, Move,
        Evaluation.type AS Evaluation_Type,
        Evaluation.value AS Evaluation_Value,
        "WDL Stats", Start_Date, Start_Time, End_Date, End_Time,
        CASE WHEN Move_Number % 2 = 1 THEN White ELSE Black END AS Player_To_Move,
        CASE
            WHEN Move_Number % 2 = 1 THEN
                LAG(Evaluation.value, 1) OVER (PARTITION BY Game_Number ORDER BY Move_Number) - Evaluation.value
            ELSE
                Evaluation.value - LAG(Evaluation.value, 1) OVER (PARTITION BY Game_Number ORDER BY Move_Number)
        END AS CentiPawnLoss,
        LAG("WDL Stats"[-3], 1) OVER (PARTITION BY Game_Number ORDER BY Move_Number) AS W_before,
        LAG("WDL Stats"[-2], 1) OVER (PARTITION BY Game_Number ORDER BY Move_Number) AS D_before,
        "WDL Stats"[-3] AS W_after,
        "WDL Stats"[-2] AS D_after
    FROM t
),
before_after AS (
    SELECT
        Move_Number, Move, CentiPawnLoss, Game_Number,
        (W_before + 0.5 * D_before) / 1000 AS wp_before,
        1 - (W_after + 0.5 * D_after) / 1000 AS wp_after,
        Player_To_Move
    FROM move_analysis
),
accuracy_calcs AS (
    SELECT
        Move_Number, Move, CentiPawnLoss, Player_To_Move, Game_Number,
        wp_before - wp_after AS delta,
        GREATEST(0, LEAST(100,
            103.1668 * EXP(-0.04354 * (wp_before - wp_after) * 100) - 3.1669
        )) AS move_accuracy
    FROM before_after
)
SELECT
    Game_Number, Move_Number, Move, CentiPawnLoss, Player_To_Move, move_accuracy,
    ROUND(AVG(GREATEST(CentiPawnLoss, 0)) FILTER (WHERE Move_Number % 2 = 1) OVER (PARTITION BY Game_Number), 2) AS ACPL_White,
    ROUND(AVG(GREATEST(CentiPawnLoss, 0)) FILTER (WHERE Move_Number % 2 = 0) OVER (PARTITION BY Game_Number), 2) AS ACPL_Black,
    ROUND(AVG(move_accuracy) FILTER (WHERE Move_Number % 2 = 1) OVER (PARTITION BY Game_Number), 2) AS Game_Accuracy_White,
    ROUND(AVG(move_accuracy) FILTER (WHERE Move_Number % 2 = 0) OVER (PARTITION BY Game_Number), 2) AS Game_Accuracy_Black,
    CASE
        WHEN Move_Number BETWEEN 1 AND 10  THEN 'opening'
        WHEN Move_Number BETWEEN 11 AND 25 THEN 'middlegame'
        ELSE 'endgame'
    END AS game_phase
FROM accuracy_calcs
ORDER BY Game_Number, Move_Number
"""
