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

