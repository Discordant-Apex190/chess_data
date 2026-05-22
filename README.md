# Chess Game Analysis Pipeline

A data engineering project that fetches, analyzes, and reports on my personal chess games from Chess.com.
Runs on a weekly schedule, evaluates every move with Stockfish, then uses an AI agent to generate and send a narrative report to Slack.

## What It Does

1. **Fetch** — pulls games from the Chess.com API (~2 years of history)
2. **Clean** — filters out games with missing PGN data
3. **Evaluate** — runs Stockfish (depth 18) on every move, capturing centipawn evals and WDL stats
4. **Analyze & Report** — an AI agent (Gemini via LangGraph) queries the data, searches the web for context, and sends a weekly report to Slack

## Pipeline Stages (Prefect Tasks)

| Task | Description |
|---|---|
| `fetch_chess_data` | Hits Chess.com API, saves raw parquet |
| `clean_chess_data` | Filters null PGNs, returns cleaned DataFrame |
| `run_stockfish_evals` | Stockfish eval on every move, saves cleaned parquet |
| `cleanup_initial_data` | Removes raw parquet after processing |
| `run_agent` | LangGraph agent generates report and posts to Slack |

Scheduled via Prefect cron: **every Monday at 9am**.

## Stack

- **Data**: Polars, DuckDB, Parquet
- **Chess**: python-chess, Stockfish
- **Orchestration**: Prefect (deployed via `main.serve()`)
- **Agent**: LangGraph + Gemini + Linkup (web search) + Modal (sandboxed code execution)
- **Notifications**: Slack SDK
- **Observability**: New Relic Logs
- **Deployment**: Docker on Coolify
- **API**: Chess.com Public API

## Local Setup

```bash
# Install dependencies
uv sync --project backend

# Run the pipeline immediately
uv run python -c "from backend.pipeline.main import main; main()"

# Or start the scheduled server (runs every Monday 9am)
uv run python -m backend.pipeline.main
```

## Environment Variables

Copy `secrets.env.example` to `secrets.env` and fill in:

```
GOOGLE_API_KEY=
LINKUP_API_KEY=
SLACK_API_KEY=
SLACK_CHANNEL_ID=
NEW_RELIC_LICENSE_KEY=
MODAL_API_KEY=
PREFECT_API_KEY=
PREFECT_API_URL=
STOCKFISH_PATH=        # defaults to C:\Users\Chris\stockfish\... locally, /usr/games/stockfish in Docker
```

## Deployment (Coolify)

1. New Resource → Applications → **Public Repository** → `https://github.com/Discordant-Apex190/chess_data`
2. Build Pack: `Dockerfile`
3. Add all environment variables above in Coolify's env settings
4. Deploy — the container registers the flow with Prefect Cloud and waits for the cron schedule

## Logging
I have dashboards setup in new relic to analyze logs that come in