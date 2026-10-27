import polars as pl
import polars.selectors as cs
import os, re, json, ast
from pathlib import Path

def entertainers(df):
    print('cek')

def effort(df):
    print('cek')

def control(df):
    print('cek')

def dirty_reactive_cheat(df):
    print('cek')


if __name__ == '__main__':
    
    file_path = 'raw_data/career/example'
    coef_path = 'raw_data/coef/opta_ranking.json'
    df = pl.read_csv('raw_data/career/example/top 5.csv', separator=';')
    
    Coef_file = Path(coef_path)
    with open(Coef_file, "r") as f:
        _coef = json.load(f)
    league_coef = _coef['league_coef']
    df_coef = pl.concat(
        [
            pl.DataFrame(
                [
                    {
                        "league": k,
                        "coef": v
                    }
                    for k, v in league_coef.items()
                ]
            )
        ],
        how="vertical"
    )
    
    df_coef = league_weight(df_coef, reference_league='Serie A')
    df = prep_data(df, df_coef)
    