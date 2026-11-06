import polars as pl
import pandas as pd

def tampilkan_tabel_index(df, kolom):

    kolom_index = kolom

    # Hitung percentile rank setiap kolom
    persentil = df.select([
        (
            pl.col(c).rank(method="average")
            / pl.col(c).count()
            * 100
        ).alias(c)
        for c in kolom_index
    ])

    pdf = df.to_pandas()
    pct = persentil.to_pandas()

    def warna(value):
        if pd.isna(value):
            return ""

        if value <= 20:
            return "color: #FF4D4D; font-weight: bold"
        elif value <= 40:
            return "color: #FFA500; font-weight: bold"
        elif value <= 60:
            return "color: #D6B800; font-weight: bold"
        elif value <= 80:
            return "color: #8BC34A; font-weight: bold"
        else:
            return "color: #00C853; font-weight: bold"

    def styling(_):
        styles = pdf.copy().astype(object)
        styles[:] = ""

        for col in kolom_index:
            styles[col] = pct[col].apply(
                lambda x: warna(x) if x is not None else ""
            )

        return styles

    styled = pdf.style.apply(styling, axis=None)

    styled = styled.format({
        col: "{:.0f}"
        for col in kolom_index
    })

    return styled
