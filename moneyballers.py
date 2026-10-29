import polars as pl
import polars.selectors as cs
import os, re, json, ast
import pandas as pd
from pathlib import Path

with open("raw_data/metrics.json", "r") as f:
    all_metrics = json.load(f)

base_metrics = all_metrics["basis"]

class Moneyballers:
    def __init__(self, df):
        self.df = df.clone()

    def entertainers(self):
        entertainers = self.df[base_metrics]
        hitung_metrik = (
            [
                (self.df["Svt/90"] + self.df["Pens Saved/90"])
                .alias('gk_index'),
                (self.df["Svt/90"] + self.df["Pens Saved/90"])
                .alias('defensive_index'),
                (self.df["PsP/90"] + self.df["Drb/90"])
                .alias('progressive_index'),
                (self.df["OP-KP/90"] + self.df["Shots/90"])
                .alias('shooting_index'),
                ((self.df["Poss Lost/90"] + self.df["Off/90"]) * (-1))
                .alias('frustration_index')
            ]
        )

        entertainers = (
            entertainers
            .with_columns(hitung_metrik)
        )

        entertainers = entertainers.with_columns(
            pl.when(pl.col("Best Pos") == "GK")
            .then(
                (pl.col("gk_index") + pl.col("gk_index") + pl.col("gk_index")
                + pl.col("frustration_index") + pl.col("defensive_index")) / 5
            )

            .when(pl.col("Best Pos") == "D (C)")
            .then(
                (pl.col("frustration_index") + pl.col("defensive_index") + pl.col("defensive_index")
                + pl.col("progressive_index") + pl.col("shooting_index")) / 5
            )

            .when(pl.col("Best Pos").is_in(['WB (L)', 'WB (R)', 'D (R)', 'D (L)']))
            .then(
                (pl.col("frustration_index") + pl.col("defensive_index") + pl.col("progressive_index")
                + pl.col("progressive_index") + pl.col("shooting_index")) / 5
            )

            .when(pl.col("Best Pos") == "DM")
            .then(
                (pl.col("frustration_index") + pl.col("defensive_index") + pl.col("progressive_index")
                + pl.col("progressive_index") + pl.col("shooting_index")) / 5
            )

            .when(pl.col("Best Pos") == "M (C)")
            .then(
                pl.max_horizontal([
                    (pl.col("frustration_index") + pl.col("defensive_index") + pl.col("progressive_index")
                    + pl.col("progressive_index") + pl.col("shooting_index")) / 5,

                    (pl.col("frustration_index") + pl.col("progressive_index") + pl.col("progressive_index")
                    + pl.col("shooting_index") + pl.col("shooting_index")) / 5
                ])
            )

            .when(pl.col("Best Pos") == "AM (C)")
            .then(
                (pl.col("frustration_index") + pl.col("progressive_index") + pl.col("progressive_index")
                + pl.col("shooting_index") + pl.col("shooting_index")) / 5
            )

            .when(pl.col("Best Pos").is_in(['AM (R)', 'AM (L)', 'M (R)', 'M (L)']))
            .then(
                (pl.col("frustration_index") + pl.col("progressive_index") + pl.col("progressive_index")
                + pl.col("shooting_index") + pl.col("shooting_index")) / 5
            )

            .when(pl.col("Best Pos") == "ST (C)")
            .then(
                (pl.col("frustration_index") + pl.col("progressive_index") + pl.col("progressive_index")
                + pl.col("shooting_index") + pl.col("shooting_index")) / 5
            )
            .otherwise(None)
            .round(2)
            .alias("X-factor")
        )

        entertainers = entertainers.with_columns(
            [
                (
                    (
                        pl.col(col)
                        .rank(method="average")
                        .over("Best Pos")
                        * 100
                        / pl.len().over("Best Pos")
                    ).round(0)
                    .alias('X-factor rank')
                )
                for col in ['X-factor']
            ]
        )
        
        return entertainers


    def effort(self):
        effort = self.df[base_metrics]
        hitung_metrik = (
            [
                ((self.df["Sprints/90"] + self.df["Distance/90"]) / 2)
                .round(2)
                .alias('running_index'),
                ((self.df["Pres A/90"] + self.df["Tck A/90"] + self.df["Hdrs A/90"]) / 3)
                .round(2)
                .alias('engagement_index'),
            ]
        )

        effort = (
            effort
            .with_columns(hitung_metrik)
        )

        effort = (
            effort
            .with_columns(
                ((pl.col("running_index") + pl.col("engagement_index")) / 2)
                .round(2)
                .alias('Effort score'),
            )
        )

        effort = effort.with_columns(
            [
                (
                    (
                        pl.col(col)
                        .rank(method="average")
                        .over("Best Pos")
                        * 100
                        / pl.len().over("Best Pos")
                    ).round(0)
                    .alias('Effort rank')
                )
                for col in ['Effort score']
            ]
        )

        return effort


    def control(self):
        control = self.df[base_metrics]
        hitung_metrik = (
            [
                (((self.df["Pressure Index"] + 4*self.df["Poss Won/90"]) / 5) * (1 - self.df["Loss Rate"] / 100))
                .round(2)
                .alias('Defend'),
                (((self.df["Creation Index"] + 2*self.df["Poss Won/90"] + 2*self.df["Pressure Index"]) / 5) * (1 - self.df["Loss Rate"] / 100))
                .round(2)
                .alias('Support'),
                (((self.df["Scoring Index"] + self.df["Pressure Index"] + 3*self.df["Creation Index"]) / 5) * (1 - self.df["Loss Rate"] / 100))
                .round(2)
                .alias('Create'),
                (((3*self.df["Scoring Index"] + self.df["Pressure Index"] + self.df["Creation Index"]) / 5) * (1 - self.df["Loss Rate"] / 100))
                .round(2)
                .alias('Score'),
            ]
        )

        control = (
            control
            .with_columns(hitung_metrik)
        )

        control = control.with_columns(
            pl.when(pl.col("Best Pos").is_in(["GK", "D (C)", "DM"]))
            .then(pl.col("Defend"))

            .when(pl.col("Best Pos").is_in(['WB (L)', 'WB (R)', 'D (R)', 'D (L)']))
            .then(pl.col("Support"))

            .when(pl.col("Best Pos").is_in(['M (C)']))
            .then(
                pl.max_horizontal([
                    pl.col("Support"), 
                    pl.col("Create"), 
                    pl.col("Score")
                ])
            )

            .otherwise(
                pl.max_horizontal([
                    pl.col("Create"),
                    pl.col("Score")
                ])
            )

            .alias("Best Score")
        )

        nilai_dicari = control["Best Score"]

        kolom_cari = ["Defend", "Support", "Create","Score"]

        control = (
            control.with_columns(
                pl.coalesce([
                    pl.when(pl.col(kol) == pl.col("Best Score"))
                    .then(pl.lit(kol))
                    .otherwise(None)
                    for kol in kolom_cari
                ]).alias("Function")
            )
        )

        control = control.with_columns(
            [
                (
                    (
                        pl.col(col)
                        .rank(method="average")
                        .over("Best Pos")
                        * 100
                        / pl.len().over("Best Pos")
                    ).round(0)
                    .alias('Function rank')
                )
                for col in ['Best Score']
            ]
        )

        return control


    def dirty_reactive_cheat(self):
        # ['ST (C)', 'M (R)', 'AM (C)', 'D (L)', 'WB (L)', 'M (C)', 'M (L)', 'GK', 'D (R)', 'WB (R)', 'AM (L)', 'D (C)', 'AM (R)', 'DM']
        dirty_reactive_cheat = self.df[base_metrics + ["Dirty Index", "Reactive Index", "Cheat Index"]]

        dirty_reactive_cheat = dirty_reactive_cheat.with_columns(
            pl.when(pl.col("Best Pos") == "D (C)")
            .then(
                (pl.col("Dirty Index") + 2*pl.col("Reactive Index")) / 3
            )
            .when(pl.col("Best Pos").is_in(('M (R)', 'AM (C)', 'D (L)', 'WB (L)', 'M (C)', 'M (L)', 'D (R)', 'WB (R)', 'DM')))
            .then(
                (pl.col("Dirty Index") + pl.col("Reactive Index") + pl.col("Cheat Index")) / 3
            )
            .otherwise(
                (pl.col("Dirty Index") + 2*pl.col("Cheat Index")) / 3
            )
            .round(2)
            .alias("Dirty Reactive Cheat")
        )

        dirty_reactive_cheat = dirty_reactive_cheat.with_columns(
            [
                (
                    (
                        pl.col(col)
                        .rank(method="average")
                        .over("Best Pos")
                        * 100
                        / pl.len().over("Best Pos")
                    ).round(0)
                    .alias('DRC rank')
                )
                for col in ['Dirty Reactive Cheat']
            ]
        )

        return dirty_reactive_cheat
    
    def moneyballers(self):
        result = pd.DataFrame({
            "entertainers": self.entertainers(),
            "effort": self.effort(),
            "control": self.control(),
            "dirty_reactive_cheat": self.dirty_reactive_cheat()
        })


if __name__ == '__main__':
    

    from weighting import prep_data, league_weight
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

    mb = Moneyballers(df)
    result = mb.moneyballers()
    print(result)
    