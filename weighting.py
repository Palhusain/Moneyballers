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

    ## EMGHITUNG BEBERAPA METRIK TAMBAHAN
    # hitung_metrik = (
    #     [
    #         ## MEGHITUNG PERSENTASE EXPECTED GOALS PREVENTED (xGP%/90)
    #         pl.when(
    #             (pl.col("xGP") + pl.col("Goals Allowed")) != 0
    #         )
    #         .then(
    #             pl.col("xGP")
    #             / (pl.col("xGP") + pl.col("Goals Allowed"))
    #             * 100
    #         )
    #         .otherwise(None)
    #         .round(2)
    #         .alias("xGP%"),

    #         ## MEGHITUNG PERSENTASE TEKEL SUKSES (Tackle%/90)
    #         pl.when(
    #             pl.col("Tck A") != 0
    #         )
    #         .then(
    #             pl.col("Tck C")
    #             / pl.col("Tck A")
    #             * 100
    #         )
    #         .otherwise(None)
    #         .round(2)
    #         .alias("Tackle%"),

    #         ## MEGHITUNG PERSENTASE DUEL UDARA SUKSES (Tackle%/90)
    #         pl.when(
    #             pl.col("Hdrs A") != 0
    #         )
    #         .then(
    #             pl.col("Hdrs")
    #             / pl.col("Hdrs A")
    #             * 100
    #         )
    #         .otherwise(None)
    #         .round(2)
    #         .alias("Hdrs%"),

    #         ## MEGHITUNG LOSS RATE (LossRate)
    #         pl.when(
    #             pl.col("Pas A") != 0
    #         )
    #         .then(
    #             pl.col("Poss Lost/90")
    #             / pl.sum_horizontal("Ps C", "Poss Lost/90", 'Fouls Against', 'Shots')
    #             * 100
    #         )
    #         .otherwise(None)
    #         .round(2)
    #         .alias("Loss%"),

    #         ## MEGHITUNG PERSENTASE UMPAN SUKSES (Pass%/90)
    #         pl.when(
    #             pl.col("Pas A") != 0
    #         )
    #         .then(
    #             pl.col("Ps C")
    #             / pl.col("Pas A")
    #             * 100
    #         )
    #         .otherwise(None)
    #         .round(2)
    #         .alias("Pass%"),

    #         ## MEGHITUNG PERSENTASE UMPAN PROGRESIF (Prog%/90)
    #         pl.when(
    #             pl.col("Ps C") != 0
    #         )
    #         .then(
    #             pl.col("PsP")
    #             / pl.col("Ps C")
    #             * 100
    #         )
    #         .otherwise(None)
    #         .round(2)
    #         .alias("Prog%"),

    #         ## MEGHITUNG PERSENTASE UMPAN SILANG (Cross%/90)
    #         pl.when(
    #             pl.col("Cr A") != 0
    #         )
    #         .then(
    #             pl.col("Cr C")
    #             / pl.col("Cr A")
    #             * 100
    #         )
    #         .otherwise(None)
    #         .round(2)
    #         .alias("Cross%"),

    #         ## MEGHITUNG PERSENTASE TEMBAKAN (Shoot%/90)
    #         pl.when(
    #             pl.col("Shots") != 0
    #         )
    #         .then(
    #             pl.col("ShT")
    #             / pl.col("Shots")
    #             * 100
    #         )
    #         .otherwise(None)
    #         .round(2)
    #         .alias("Shoot%"),
    #     ]
    # )

    # df_metrik = (
    #     df_p90
    #     .with_columns(hitung_metrik)
    # )

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

    # n = df_metrik.height
    # inverse_cols = {"Loss%_adj"}  # bisa lebih dari satu
    # cols_to_rank = [m for m in df_metrik.columns if m.endswith("%")] + [m for m in df_metrik.columns if m.endswith("_adj")]
    # df_percentile = df_metrik.with_columns(
    #     [
    #         (
    #             lambda rank_expr: (
    #                 pl.when(pl.col(col).is_null())
    #                 .then(0)
    #                 .otherwise(
    #                     100 - rank_expr if col in inverse_cols else rank_expr
    #                 )
    #                 .alias(f"{col}_rank")
    #             )
    #         )(
    #             (
    #                 pl.col(col)
    #                 .rank(method="average")
    #                 .over("Best Pos")
    #                 * 100
    #                 / pl.len().over("Best Pos")
    #             ).round(0)
    #         )
    #         for col in cols_to_rank
    #     ]
    # ).drop(metrics)

    output_path = 'output'
    os.makedirs(output_path, exist_ok=True)

    df_p90.write_csv(f"{output_path}/df_p90.csv", separator=";")
    df_weighted.write_csv(f"{output_path}/df_weighted.csv", separator=";")
    # df_percentile.write_csv(f"{output_path}/df_percentile.csv", separator=";")

    return df_weighted

def calculate_custom_percentile(df_player, df_metrik, comparison):
    with open("raw_data/metrics.json", "r") as f:
        all_metrics = json.load(f)

    rank_cols = all_metrics["rank_cols"]

    compare_df = df_metrik.filter(
        pl.col("Best Pos") == comparison
    )

    result = {}

    for col in rank_cols:
        value = df_player[col]
        values = compare_df[col].drop_nulls()

        if value is None or len(values) == 0:
            result[f"{col}_rank"] = 0
        else:
            result[f"{col}_rank"] = round(
                (values <= value).sum()
                / len(values)
                * 100
            )

    return result


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
