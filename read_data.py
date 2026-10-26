import polars as pl
import polars.selectors as cs
import os, re, json, ast
from pathlib import Path
import json

# from libs.read_gsheet import SheetMapping

def read_data(file_path, coef_path):

    ### READ RAW DATA
    folder = Path(file_path)

    df = (
        pl.concat(
            [pl.read_csv(file, separator=";") for file in folder.glob("*.csv")],
            how="vertical",
        )
    )

    df_filtered = (
        df
        .filter(pl.col('Minutes') > 900)
        .unique()
    )

    with open("raw_data/metrics.json", "r") as f:
        all_metrics = json.load(f)

    base_metrics = all_metrics["metrics"]

    metrics_90 = ["Poss Lost/90","Poss Won/90","Sprints/90", "Dist/90",]
    standardize_p90 = [
            pl.when(
                pl.col(metric) != 0
            )
            .then(
                pl.col(metric)
                / 90 
                * pl.col('Minutes')
            )
            .otherwise(None)
            .round(0)
            .alias(metric)
            for metric in metrics_90
        ]
    df_p90_std = (
        df_filtered
        .with_columns(standardize_p90)
    )

    keep_cols = ['Division', 'Club', 'Unique ID', 'Player', 'Position', 'Best Pos', 'Age', 'Salary', 'Transfer Value']
    COLUMN_MAPPING = {
        "Poss Won/90": "Poss Won",
        "Poss Lost/90": "Poss Lost",
        "Sprints/90": "Sprints",
        "Dist/90": "Dist",
    }

    df_join = (
        df_p90_std
        .group_by("Unique ID")
        .agg(
            count=pl.len(),
            **{col: pl.col(col).first() for col in keep_cols if col != "Unique ID"},
            **{
                col: pl.col(col).sum()
                for col in df.columns
                if col not in keep_cols
            }
        )
        .sort("Unique ID")
        .rename(COLUMN_MAPPING)
        .sort(["Division", "Club"])
    )

    ### READ RAW COEFFICIENT
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

    output_path = 'output'
    os.makedirs(output_path, exist_ok=True)

    # df_percentile.write_csv("df_percentile.csv", separator=";")
    df_join.write_csv(f"{output_path}/df_join.csv", separator=";")

    return df_join, df_coef


if __name__ == '__main__':
    
    file_path = 'raw_data/career/Wimbledon'
    coef_path = "raw_data/coef/opta_ranking.json"
    df = read_data(file_path, coef_path)
