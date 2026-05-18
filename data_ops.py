import requests as r
import polars as pl
import duckdb
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path

class ChessDataOps():
    def __init__(self):
        self.username = "chesswizinterm"
        self.base_url = "https://api.chess.com/pub/player"
        self.headers = {
            'User-Agent': 'Chess Data Project/1.0 Username: chesswizinterm Contact: chriseaton190@gmail.com'
        }
        self.duckdb_conn = None
        self.days_back = 760

    def get_data(self, url: str) -> dict:
        headers = self.headers
        response = r.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def iterate_games(self) -> pl.DataFrame:
        current_date = datetime.today()
        starting_date = datetime.today() - timedelta(days = self.days_back)
        data_list = []
        while starting_date < current_date:
            starting_date_month = f"{starting_date.month:02d}"
            url = f"{self.base_url}/{self.username}/games/{starting_date.year}/{starting_date_month}"
            starting_date = starting_date + relativedelta(months=1)
            data = self.get_data(url)
            data_list.append(data)
        df = pl.DataFrame(data_list)
        return df

    def save_data(self, file_path: Path) -> None:
        all_data = self.iterate_games()
        unnested_data = all_data.explode("games").unnest()
        unnested_data.write_parquet(file_path)
        return None

    def get_rel_from_parquet(self, file_path: Path) -> duckdb.DuckDBPyRelation:
        if self.duckdb_conn is None:
            self.duckdb_conn = duckdb.connect()
        file_name = file_path.name
        rel = self.duckdb_conn.from_parquet(file_name)
        return rel


