import polars as pl
import polars.selectors as cs
import os, re, json, ast
from pathlib import Path

def league_weight(df_coef, reference_league):
    reference_coef = (
        df_coef
        .filter(pl.col("league") == reference_league)
        .item(0, "coef")
    )

    return df_coef.with_columns(
        (pl.col("coef") / reference_coef)
        .round(2)
        .alias("league_weight")
    )

def prep_data(df, df_coef):
    
    ### LOAD SOME JSON
    with open("raw_data/metrics.json", "r") as f:
        all_metrics = json.load(f)

    base_metrics = all_metrics["metrics"]
    exclude = all_metrics["basis"] + all_metrics["p90"]
    # rank_cols = all_metrics["rank_cols"]

    with open("raw_data/coef/opta_ranking.json", "r") as f:
        league = json.load(f)

    mapping = {}
    for group, leagues in league['non_league'].items():
        for league in leagues:
            mapping[league] = group

    ### LOAD DATA

    ### UBAH KE PER 90 MENIT
    metrics = [c for c in df.columns if c not in exclude]

    df_p90 = df.with_columns(
        (cs.numeric().exclude(exclude) / pl.col("Minutes") * 90 )
        .round(2)
        .name.suffix("/90")
    )
    df_p90 = df_p90.select(
        all_metrics["basis"] +
        [c for c in df_p90.columns if c.endswith("/90")]
    )

    ### HITUNG PERSENTIL UNTUK TIAP KATEGORI
    df_p90 = (
        df_p90
        .with_columns(
            pl.col("Division").alias("Original Division"),
            pl.col("Division").replace(mapping).alias("Division")
        )
        .join(
            df_coef.select(
                ["league", "league_weight"]
            ),
            left_on="Division", right_on='league',
            how="left"
        )
    )

    
    metrics_90 = [m for m in df_p90.columns if m.endswith("/90")]
    df_weighted = (
        df_p90
        .with_columns(
            [
                (pl.col(col) * pl.col("league_weight"))
                .round(2)
                .alias(f"{col}")
                for col in metrics_90
            ]
        )
    )

    ## EMGHITUNG BEBERAPA METRIK TAMBAHAN
    hitung_metrik = (
        [
            ## LOSS RATE
            pl.when(
                (pl.col('Pas A/90') > 0)
            )
            .then(
                (pl.col("Poss Lost/90") / pl.col("Pas A/90"))
                * 100
            )
            .otherwise(None)
            .round(2)
            .alias("Loss Rate"),

            ## CREATION INDEX
            pl.when(
                (pl.col('OP-KP/90') > 0)
            )
            .then(
                pl.col("xA/90")
                * (pl.col("xA/90") / pl.col("OP-KP/90"))
                * 100
            )
            .otherwise(None)
            .round(2)
            .alias("Creation Index"),

            ## SCORING INDEX
            pl.when(
                (pl.col('Shots/90') > 0)
            )
            .then(
                pl.col("Goals/90")
                * (pl.col("xG/90") / pl.col("Shots/90"))
                * 100
            )
            .otherwise(None)
            .round(2)
            .alias("Scoring Index"),

            ## PRESSURE INDEX
            pl.when(
                (pl.col('Pres A/90') > 0)
            )
            .then(
                pl.col("Pres C/90")
                * (pl.col("Pres C/90") / pl.col("Pres A/90"))
                * 100
            )
            .otherwise(None)
            .round(2)
            .alias("Pressure Index"),

            ## Dirty Index 
            pl.when(
                ((pl.col("Fouls Made/90") - pl.col("Off/90")) > 0)
            )
            .then(
                (pl.col("Fouls Made/90") - pl.col("Off/90"))
                * (1 - ((pl.col("Yel/90") + pl.col("Red cards/90")) / (pl.col("Fouls Made/90") - pl.col("Off/90"))))
                * 100
            )
            .otherwise(None)
            .round(2)
            .alias("Dirty Index"),

            ## Reactive Index 
            (
                (pl.col("Blk/90") + pl.col("Shts Blckd/90") + pl.col("Clearances/90") + pl.col("K Tck/90"))
                * (
                    (pl.col("Blk/90") + pl.col("Shts Blckd/90") + pl.col("Clearances/90") + pl.col("K Tck/90"))
                    - (pl.col("Blk/90") + pl.col("Shts Blckd/90") + pl.col("Clearances/90") + pl.col("Tck A/90") + pl.col("Pres A/90")) 
                )
                # * 100
            )
            .round(2)
            .alias("Reactive Index"),

            ## Cheat Index 
            (
                pl.col("Fouls Against/90")
                / (pl.col("Ps C/90") + pl.col("Fouls Against/90") + pl.col("Poss Lost/90") + pl.col("Shots/90")) 
                * 100
            )
            .round(2)
            .alias("Cheat Index"),


        ]
    )

    df_weighted = (
        df_weighted
        .with_columns(hitung_metrik)
    )

    metrics_index = [m for m in df_weighted.columns if m.endswith(" Index")] + ['Loss Rate']

    # n = df_metrik.height
    # inverse_cols = {"Loss%_adj"}  # bisa lebih dari satu
    cols_to_rank = metrics_90 + metrics_index
    df_percentile = df_weighted.with_columns(
        [
            (
                (
                    pl.col(col)
                    .rank(method="average")
                    .over("Best Pos")
                    * 100
                    / pl.len().over("Best Pos")
                ).round(0)
            )
            for col in cols_to_rank
        ]
    )

    output_path = 'output'
    os.makedirs(output_path, exist_ok=True)

    df_p90.write_csv(f"{output_path}/df_p90.csv", separator=";")
    df_weighted.write_csv(f"{output_path}/df_weighted.csv", separator=";")
    df_percentile.write_csv(f"{output_path}/df_percentile.csv", separator=";")

    return df_percentile



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
    # df_pemain = df.filter(pl.col("Player") == 'Joe Gelhardt')
    # calculate_custom_percentile(df_pemain, df_metrik=df, comparison='AM (C)')
