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
