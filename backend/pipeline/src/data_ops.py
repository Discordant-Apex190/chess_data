from typing import Any
import requests as r
import polars as pl
import duckdb
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path
from backend.pipeline.src.base_logger import logger


class ChessDataOps():
    """
    A class representing data operations for chess data

    Attributes:
        username (str): The username we are pulling data for
        base_url (str): The base url for chess.com player data
        headers (str): The headers for the chess.com api
        duckdb_conn (str): Initialization of a duckdb connection
        days_back (int): The number of days we want to look back and get data from

    """

    def __init__(self, username: str = "chesswizinterm"):
        self.username = username
        self.base_url = "https://api.chess.com/pub/player"
        self.headers = {
            'User-Agent': 'Chess Data Project/1.0 Username: chesswizinterm Contact: chriseaton190@gmail.com'
        }
        self.duckdb_conn = None
        self.days_back = 760
    
    def get_data(self, url: str) -> Any:
        logger.debug(f"GET {url}")
        headers = self.headers
        response = r.get(url, headers=headers)
        response.raise_for_status()
        return response

    def iterate_games(self) -> pl.DataFrame:
        """
        Gets data from all games within a specific timeperiod
        Args:
            None
        Returns:
            df: All game data in a DataFrame format
        """
        current_date = datetime.today()
        starting_date = datetime.today() - timedelta(days = self.days_back)
        logger.info(f"Fetching games for {self.username} from {starting_date.strftime('%Y-%m')} to {current_date.strftime('%Y-%m')}")
        data_list = []
        while starting_date < current_date:
            starting_date_month = f"{starting_date.month:02d}"
            url = f"{self.base_url}/{self.username}/games/{starting_date.year}/{starting_date_month}"
            try:
                data = self.get_data(url).json()
                data_list.append(data)
                logger.debug(f"Fetched {starting_date.year}-{starting_date_month}: {len(data.get('games', []))} games")
            except r.exceptions.HTTPError as e:
                logger.warning(f"Failed to fetch {starting_date.year}-{starting_date_month}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error for {starting_date.year}-{starting_date_month}: {e}")
            starting_date = starting_date + relativedelta(months=1)

        df = pl.DataFrame(data_list)
        logger.info(f"Collected {len(data_list)} months of game data for {self.username}")
        return df

    def save_data(self, file_path: Path) -> None:
        """
        Saves initial chess data in a parquet file
        Args:
            file_path: The Path object where you want the parquet file to be saved at
        Returns:
            None
        """
        logger.info(f"Saving raw game data to {file_path}")
        all_data = self.iterate_games()
        unnested_data = all_data.explode("games").unnest()
        unnested_data.write_parquet(file_path)
        logger.info(f"Saved {len(unnested_data)} raw game records to {file_path}")
        return None

    def get_rel_from_parquet(self, file_path: Path) -> duckdb.DuckDBPyRelation:
        """
        Returns rel for the given duckdb
        Args:
            file_path: The Path object where you want to get data
        Returns:
            rel: Relationship object from duckdb, a nice base to build queries from
        """
        if self.duckdb_conn is None:
            logger.debug("Creating new DuckDB connection")
            self.duckdb_conn = duckdb.connect()
        file_name = str(file_path)
        logger.debug(f"Loading parquet relation from {file_name}")
        rel = self.duckdb_conn.from_parquet(file_name)
        return rel


