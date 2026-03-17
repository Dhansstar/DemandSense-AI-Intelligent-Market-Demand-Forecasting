import numpy as np
import streamlit as st
import pandas as pd
import os
from prediction import load_assets, run_prediction_logic, plot_forecast_plotly

# FUNGSI LOAD DATA (SUDAH BENER)
@st.cache_data
def load_internal_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    file_map = {
        'Kitchen': 'forecast_kitchen_data.csv',
        'Home': 'forecast_home_data.csv',
        'Bathroom': 'forecast_bathroom_data.csv',
        'Storage': 'forecast_storage_data.csv',
        'Tools': 'forecast_tools_data.csv',
        'Other': 'forecast_other_data.csv'
    }
    
    all_df = []
    
    for kat_name, file_name in file_map.items():
        path = os.path.join(base_dir, file_name)
        if os.path.exists(path):
            temp_df = pd.read_csv(path)
            # 1. Pastikan kolom tanggal beneran datetime
            temp_df['Waktu Pesanan Dibuat'] = pd.to_datetime(temp_df['Waktu Pesanan Dibuat'])
            
            # 2. AGGREGASI: Ini kunci biar hasilnya sama kayak notebook!
            # Kita jumlahkan per hari kalau ada tanggal yang duplikat di CSV
            temp_df = temp_df.groupby('Waktu Pesanan Dibuat').agg({
                'Jumlah': 'sum',
                'Returned Quantity': 'sum'
            }).reset_index()
            
            temp_df['Kategori Produk'] = kat_name 
            all_df.append(temp_df)
    
    if not all_df: return None
        
    df = pd.concat(all_df, ignore_index=True)
    df = df.sort_values(['Kategori Produk', 'Waktu Pesanan Dibuat'])

    # 3. Hitung Net_Sales
    df['Net_Sales'] = (df['Jumlah'] - df['Returned Quantity']).clip(lower=0)

    # 4. Feature Engineering (WAJIB SAMA DENGAN TRAINING)
    df['day_sin'] = np.sin(2 * np.pi * df['Waktu Pesanan Dibuat'].dt.day / 31)
    df['day_cos'] = np.cos(2 * np.pi * df['Waktu Pesanan Dibuat'].dt.day / 31)
    df['log_demand'] = np.log1p(df['Net_Sales'])
    
    # Lags & Moving Average (Per Kategori)
    df['lag_1'] = df.groupby('Kategori Produk')['log_demand'].shift(1).fillna(0)
    df['lag_7'] = df.groupby('Kategori Produk')['log_demand'].shift(7).fillna(0)
    df['lag_28'] = df.groupby('Kategori Produk')['log_demand'].shift(28).fillna(0)
    df['ma_7'] = df.groupby('Kategori Produk')['log_demand'].transform(lambda x: x.rolling(window=7).mean()).fillna(0)

    # 5. One-Hot Encoding (Model lo butuh kolom-kolom ini)
    kat_list = ['Bathroom', 'Home', 'Kitchen', 'Other', 'Storage', 'Tools']
    for k in kat_list:
        df[f'Cat_{k}'] = (df['Kategori Produk'] == k).astype(int)

    return df

# DISINI MASALAHNYA! Hapus 'df_internal' dari dalem kurung!
def run_product_forecast(): 
    st.header("📈 Forecast Penjualan & Rekomendasi Stok")
    st.info("Halaman ini menganalisis data internal untuk memberikan proyeksi kebutuhan stok 30 hari ke depan.")
    
    # PANGGIL DATA DISINI
    df_internal = load_internal_data()
    
    if df_internal is None:
        st.error("Gak ada data internal 'data_from_DE.csv' tong!")
        return

    # Load Model & Siapkan Data
    assets = load_assets()
    
    # Cek nama kolom kategori (biasanya 'Kategori Produk' di dataset lo)
    cat_col = 'Kategori Produk' if 'Kategori Produk' in df_internal.columns else 'Kategori'
    categories = df_internal[cat_col].unique()
    
    # List untuk menampung hasil perhitungan semua kategori
    all_results = {}
    stock_recommendations = []

    # PROSES PERHITUNGAN
    with st.spinner("Kalkulasi..."):
        for kat in categories:
            # Pastikan run_prediction_logic pake variabel df_internal yang baru di-load
            forecast_vals = run_prediction_logic(kat, df_internal, assets)
            total_unit = int(sum(forecast_vals))
            
            stock_recommendations.append({
                "Kategori": kat,
                "Kebutuhan Stok (30 Hari)": total_unit,
            })
            all_results[kat] = {
                "vals": forecast_vals,
                "total": total_unit
            }

    # TAMPILKAN TABEL RINGKASAN
    st.subheader("📋 Ringkasan Persiapan Stok")
    stock_df = pd.DataFrame(stock_recommendations)
    
    st.dataframe(
        stock_df.style.highlight_max(axis=0, subset=['Kebutuhan Stok (30 Hari)'], color='#ffebcc'),
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")

    # TAMPILKAN DETAIL GRAFIK PER KATEGORI
    st.subheader("📊 Detail Visualisasi Per Kategori")
    
    for kat in categories:
        with st.expander(f"Lihat Tren & Forecast: {kat}", expanded=False):
            data = all_results[kat]
            
            # Gambar Grafik Plotly
            fig = plot_forecast_plotly(kat, df_internal, data['vals'])
            st.plotly_chart(fig, use_container_width=True)
            
            c1, c2 = st.columns(2)
            c1.metric("Total Kebutuhan", f"{data['total']} Unit")
            c2.write(f"Saran: Siapkan minimal **{data['total']} unit** untuk kategori **{kat}**.")