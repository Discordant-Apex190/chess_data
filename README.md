# Chess Game Analysis Pipeline

A data engineering project that fetches, analyzes, and stores my personal chess games from Chess.com.
Uses Stockfish to evaluate positions and identify patterns in my play.

## What It Does

- Fetches chess games from Chess.com API (configurable date range, currently about 2 years)
- Evaluates every move using Stockfish at depth 10
- Stores enriched game data in Parquet format
- Tracks move-by-move evaluations (centipawn loss, mate threats)

## Goals

The main goal is to identify my bad habits and recurring mistakes:
- Which moves do I make too often in certain positions?
- Where do I consistently miss better alternatives?
- Opening/middlegame/endgame strengths and weaknesses
- Patterns in blunders and inaccuracies

Frontend coming eventually to visualize all this.

## Stack

- **Data**: Polars, DuckDB, Parquet
- **Chess**: python-chess, Stockfish
- **Orchestration**: Prefect
- **API**: Chess.com Public API


## Todo:
Centipawn Loss Math
For each move, calculate the difference between the evaluation before and after the move, from the moving player's perspective:
White's move (odd move numbers):
    CP_loss = eval_before - eval_after
Black's move (even move numbers):
    CP_loss = -eval_before - (-eval_after) = eval_after - eval_before

Per player across all games:
    ACPL_white = sum(all_white_cp_losses) / total_white_moves
    ACPL_black = sum(all_black_cp_losses) / total_black_moves