from tracemalloc import start
import requests as r
import polars as pl
import duckdb
from datetime import datetime, timedelta

def get_data(url: str):
    headers = {'User-Agent': 'Chess Data Project/1.0 Username: chesswizinterm Contact: chriseaton190@gmail.com'}
    response = r.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def iterate_games():
    current_date = datetime.today()
    starting_date = datetime.today() - timedelta(days = 760)
    for i in 
        current_iteration = starting_date
        year
        url = f"https://api.chess.com/pub/player/chesswizinterm/games/{year}/{month}"

    data = get_data(url)
    games = data.get("games", [])
    df = pl.from_dicts(games)
    return df

if __name__ == "__main__":
    all_data = iterate_games()
    # sql = duckdb.query('SELECT url FROM df')
    # print(sql)
    