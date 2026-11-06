import streamlit as st
import polars as pl
import json
import math
from pathlib import Path

from read_data import read_data
from weighting import league_weight, prep_data
from moneyballers import Moneyballers
from percent_chart import tampilkan_tabel_index

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Football Radar",
    page_icon="⚽",
    layout="wide"
)

st.title("📊 Moneyball Player Dashboard")
# st.write("Klik salah satu baris pada tabel di bawah untuk melihat grafik radar pemain secara otomatis.")

st.set_page_config(
    page_title="Moneyballers",
    layout="wide"
)

with open("raw_data/metrics.json", "r") as f:
    all_metrics = json.load(f)

# =========================
# SIDEBAR: UPLOAD DATA
# =========================

with st.sidebar:
    st.header("Upload Data")

    uploaded_file = st.file_uploader(
        "Upload CSV atau Excel",
        type=["csv", "xlsx"]
    )

    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            df = pl.read_csv(
                uploaded_file,
                separator=";"
            )
        else:
            df = pl.read_excel(uploaded_file)

        st.success("Data berhasil dibaca")

# =========================
# PROSES OLAH DAN TAMPILKAN DATA
# =========================

if uploaded_file is not None:
    coef_path = 'raw_data/coef/opta_ranking.json'
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

    metode = {
        "Entertainers": mb.entertainers(), 
        "Grafters": mb.effort(), 
        "Controllers": mb.control(), 
        "Sh*thousers": mb.dirty_reactive_cheat(),
        "All Metode": mb.moneyballers()
    }

    pilihan = st.pills(
        "Pilih Metode",
        list(metode.keys()),
        default="All Metode",
        selection_mode="single"
    )

    if pilihan:
        basis_metode = all_metrics["Index"][pilihan]
        base_data = all_metrics["Index"]['base']

        tabel = metode[pilihan].select(
            base_data + basis_metode
        )

        styled_table = tampilkan_tabel_index(tabel, basis_metode)

        event = st.dataframe(
            styled_table,
            # use_container_width=True,
            width='content',
            hide_index=True,
            # height=500,
            on_select="rerun",
            selection_mode="single-row"
        )

