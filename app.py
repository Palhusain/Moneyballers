import streamlit as st
import polars as pl
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import json
import math
from pathlib import Path

# from read_data import read_data
# from base_pizza import pizza_player
# from weighting import league_weight, prep_data, calculate_custom_percentile

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Football Radar",
    page_icon="⚽",
    layout="wide"
)

st.title("📊 Moneyball Player Dashboard")
# st.write("Klik salah satu baris pada tabel di bawah untuk melihat grafik radar pemain secara otomatis.")

# ===============================
# Load Data
# ===============================

uploaded_file = st.file_uploader(
    "Upload data CSV atau Excel",
    type=["csv", "xlsx"]
)

if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pl.read_csv(uploaded_file, separator=';')
    else:
        df = pl.read_excel(uploaded_file)

    st.write("Data berhasil dibaca")
    st.dataframe(df)

    # Sintaks analisis kamu yang sudah ada
    # dijalankan menggunakan df dari file upload

# base_folder = Path("raw_data/career")
# career_list = [
#     f.name
#     for f in base_folder.iterdir()
#     if f.is_dir()
# ]

# selected_career = st.sidebar.selectbox(
#     "Pilih Career",
#     career_list
# )

# @st.cache_data
# def load(folder):
#     return read_data(folder, 'raw_data/coef/opta_ranking.json')

# df, df_coef = load(base_folder / selected_career)

# with open("raw_data/metrics.json", "r") as f:
#     all_metrics = json.load(f)
# metrics = all_metrics['rank_cols']

# # ===============================
# # Sidebar
# # ===============================

# reference_league = st.sidebar.selectbox(
#     "Reference League",
#     df_coef["league"].sort().to_list(),
#     index=df_coef["league"].to_list().index("Premier League")  # default
# )

# leagues = (
#     df["Division"]
#     .unique()
#     .sort()
#     .to_list()
# )

# League = st.sidebar.selectbox(
#     "Division",
#     leagues
# )

# clubs = (
#     df
#     .filter(pl.col("Division") == League)
#     ["Club"]
#     .unique()
#     .sort()
#     .to_list()
# )

# club = st.sidebar.selectbox(
#     "Club",
#     clubs
# )

# players = (
#     df
#     .filter((pl.col("Club") == club) & (pl.col("Division") == League))
#     ["Player"]
#     .sort()
#     .to_list()
# )

# target = st.sidebar.selectbox(
#     "Player",
#     players
# )

# bestpos = (
#     df["Best Pos"]
#     .unique()
#     .sort()
#     .to_list()
# )

# comparison = st.sidebar.selectbox(
#     "Compare to",
#     bestpos
# )


# # ===============================
# # Data Process
# # ===============================

# df_coef = league_weight(
#     df_coef,
#     reference_league
# )

# df = prep_data(
#     df,
#     df_coef
# )

# csv = df.write_csv()

# st.sidebar.download_button(
#     label="📥 Download CSV",
#     data=csv,
#     file_name="hasil_prep_data.csv",
#     mime="text/csv",
# )

# # custom_rank = calculate_custom_percentile(
# #     target,
# #     df,
# #     comparison
# # )

# # if comparison == None:
# #     df_player = df.filter(pl.col("Player") == target)
# # else:
# #     df_player = custom_rank.filter(pl.col("Player") == target)

# df_player = df.filter(pl.col("Player") == target)

# player = df_player["Player"][0]
# club = df_player["Club"][0]
# best_pos = df_player["Best Pos"][0]
# position = df_player["Position"][0]
# age = df_player["Age"][0]
# minutes = df_player["Minutes"][0]
# salary = df_player["Salary"][0]
# value = df_player["Transfer Value"][0]


# # ===============================
# # Player Card
# # ===============================
# with st.container(border=True):

#     st.subheader(player)

#     st.write(
#         f"{position} | {age} years old | {club}"
#     )

#     col1, col2, col3 = st.columns(3)

#     col1.metric(
#         "Minutes",
#         f"{int(minutes):,}"
#     )

#     col2.metric(
#         "Salary",
#         salary
#     )

#     col3.metric(
#         "Value",
#         value
#     )

# # ===============================
# # Biodata
# # ===============================

# st.write(
#     "Compare with: ",
#     df_player["Best Pos"][0]
#     # comparison
# )

# if comparison == None:
#     fig = pizza_player(df_player)
# else:
#     fig = pizza_player(df_player)

# st.pyplot(fig)
# plt.close(fig)

# st.divider()

# st.subheader("Player Data")

# st.dataframe(df_player[metrics].to_pandas())

# # row = df_player[metrics].to_dicts()[0]

# # items = list(row.items())

# # half = (len(items) + 1) // 2

# # col1, col2 = st.columns(2)

# # with col1:
# #     for k, v in items[:half]:
# #         st.metric(k, v)

# # with col2:
# #     for k, v in items[half:]:
# #         st.metric(k, v)