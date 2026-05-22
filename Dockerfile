FROM python:3.11-slim

# System dependencies + Stockfish binary
RUN apt-get update \
    && apt-get install -y --no-install-recommends stockfish curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python dependencies (cached layer)
COPY backend/pyproject.toml ./backend/pyproject.toml
RUN uv pip install --system \
    chess \
    deepagents \
    duckdb \
    fastapi \
    langchain-google-genai \
    langchain-modal \
    langchain-ollama \
    langgraph \
    linkup-sdk \
    modal \
    polars \
    prefect \
    pyarrow \
    python-dateutil \
    python-dotenv \
    requests \
    slack-sdk \
    stockfish \
    tqdm

# Copy source code
COPY . .

# Stockfish binary path on Debian/Ubuntu
ENV STOCKFISH_PATH=/usr/games/stockfish

CMD ["python", "-m", "backend.pipeline.main"]
