# --- Imports ---
import duckdb
import io
import os
from pathlib import Path
from typing import Literal

import modal
import polars as pl
from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableConfig
from langchain_core.utils.uuid import uuid7
from langchain_modal import ModalSandbox
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from linkup import LinkupClient
from slack_sdk import WebClient

from backend.agent.prompts import get_input_message, get_research_instructions
from backend.agent.queries import ANALYSIS_SQL
from backend.pipeline.src.base_logger import logger

PLAYER_USERNAME = "chesswizinterm"
_PIPELINE_DATA_DIR = Path(__file__).parent.parent / "pipeline" / "data"

load_dotenv(Path(__file__).parent.parent.parent / "secrets.env")

gemini_api_key = os.getenv("GOOGLE_API_KEY") or ""
linkup_api_key = os.getenv("LINKUP_API_KEY") or ""
slack_token = os.getenv("SLACK_API_KEY") or ""
slack_channel = os.getenv("SLACK_CHANNEL_ID") or ""

slack_client = WebClient(token=slack_token)
linkup_client = LinkupClient(api_key=linkup_api_key)
gemini_model = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", google_api_key=gemini_api_key)

_modal_sandbox: modal.Sandbox | None = None
_backend: ModalSandbox | None = None


def get_latest_parquet() -> Path:
    """Return the most recent cleaned_chess_data_*.parquet in the pipeline data dir."""
    candidates = sorted(_PIPELINE_DATA_DIR.glob("cleaned_chess_data_*.parquet"))
    logger.debug(f"Found {len(candidates)} parquet candidate(s) in {_PIPELINE_DATA_DIR}")
    if not candidates:
        raise FileNotFoundError(
            f"No cleaned parquet files found in {_PIPELINE_DATA_DIR}. "
            "Run the pipeline first."
        )
    selected = candidates[-1]
    logger.info(f"Using parquet file: {selected}")
    return selected


def upload_data(parquet_path: Path) -> None:
    assert _modal_sandbox is not None, "Modal sandbox not initialized"
    logger.info(f"Uploading data from {parquet_path} to Modal sandbox")
    _modal_sandbox.filesystem.make_directory("/home/modal/data", create_parents=True)

    raw_buf = io.BytesIO()
    raw_df = pl.read_parquet(parquet_path)
    raw_df.write_ndjson(raw_buf)
    _modal_sandbox.filesystem.write_bytes(raw_buf.getvalue(), "/home/modal/data/chess_data.ndjson")
    logger.info(f"Uploaded {len(raw_df)} raw move records to /home/modal/data/chess_data.ndjson")

    analyzed_buf = io.BytesIO()
    conn = duckdb.connect()
    analyzed_df = conn.from_parquet(str(parquet_path)).query("t", ANALYSIS_SQL).pl()
    analyzed_df.write_ndjson(analyzed_buf)
    _modal_sandbox.filesystem.write_bytes(analyzed_buf.getvalue(), "/home/modal/data/chess_analysis.ndjson")
    logger.info(f"Uploaded {len(analyzed_df)} analyzed move records to /home/modal/data/chess_analysis.ndjson")


@tool(parse_docstring=True)
def slack_send_message(text: str, file_path: str | None = None) -> str:
    """Send message, optionally including attachments such as images.

    Args:
        text: (str) text content of the message
        file_path: (str) file path of attachment in the filesystem.
    """
    if not file_path:
        slack_client.chat_postMessage(channel=slack_channel, text=text)
        logger.info("Slack message sent")
    else:
        assert _backend is not None, "Modal backend not initialized"
        fp = _backend.download_files([file_path])
        slack_client.files_upload_v2(
            channel=slack_channel,
            content=fp[0].content,
            initial_comment=text,
        )
        logger.info(f"Slack file uploaded: {file_path}")
    return "Message sent."

@tool(parse_docstring=True)
def internet_search(
    query: str,
    depth: Literal["fast", "standard"] = "standard",
    output_type: Literal["searchResults", "sourcedAnswer", "structured"] = "sourcedAnswer",
    include_images: bool = False,
    include_inline_citations: bool = False,
):
    """Search the internet for information.

    Use this to look up chess opening names from move notation, understand
    chess concepts, resolve DuckDB syntax questions, or find any information
    not present in the dataset.

    Args:
        query: The search query string.
        depth: Search depth, either 'fast' or 'standard'. Use 'standard' for complex topics.
        output_type: Output format, either 'sourcedAnswer' or 'searchResults'.
        include_images: Whether to include images in results.
        include_inline_citations: Whether to include inline citations.
    """
    logger.debug(f"Internet search: {query!r} (depth={depth})")
    return linkup_client.search(query=query, depth=depth, output_type=output_type)

def main(parquet_path: Path | None = None) -> None:
    global _modal_sandbox, _backend

    logger.info("Starting chess agent run")
    resolved_path = parquet_path or get_latest_parquet()

    logger.info("Creating Modal sandbox")
    app = modal.App.lookup("chess-app", create_if_missing=True)
    _modal_sandbox = modal.Sandbox.create(app=app, timeout=3600)
    _backend = ModalSandbox(sandbox=_modal_sandbox)

    upload_data(resolved_path)

    logger.info("Initializing deep agent")
    agent = create_deep_agent(
        model=gemini_model,
        tools=[internet_search, slack_send_message],
        system_prompt=get_research_instructions(PLAYER_USERNAME),
        backend=_backend,
        checkpointer=InMemorySaver(),
    )

    config: RunnableConfig = {"configurable": {"thread_id": str(uuid7())}}

    try:
        for step in agent.stream(
            {"messages": [get_input_message(PLAYER_USERNAME)]},
            config,
            stream_mode="updates",
        ):
            for node_name, update in step.items():
                if update and (messages := update.get("messages")) and isinstance(messages, list):
                    logger.debug(f"Agent step from node '{node_name}': {len(messages)} message(s)")
                    for message in messages:
                        content = message.content if isinstance(message.content, str) else str(message.content)
                        preview = content[:200].replace("\n", " ") + ("\u2026" if len(content) > 200 else "")
                        logger.info(f"[{node_name}] {type(message).__name__}: {preview}")
                        message.pretty_print()
    finally:
        logger.info("Terminating Modal sandbox")
        _modal_sandbox.terminate()


if __name__ == "__main__":
    main()


