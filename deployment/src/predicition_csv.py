import streamlit as st
import pandas as pd
import os
from datetime import timedelta
import numpy as np

# Memanggil mesin dari prediction.py
from prediction import load_assets, run_prediction_logic, plot_forecast_plotly

@st.cache_data
@st.cache_data
def load_internal_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # List semua file sesuai yang lo upload
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
            temp_df['Kategori Produk'] = kat_name # Paksa kasih label kategori
            all_df.append(temp_df)
    
    if not all_df:
        return None
        
    df = pd.concat(all_df, ignore_index=True)
    df['Waktu Pesanan Dibuat'] = pd.to_datetime(df['Waktu Pesanan Dibuat'])
    df = df.sort_values(['Kategori Produk', 'Waktu Pesanan Dibuat'])

    # 1. Net_Sales (Target)
    df['Net_Sales'] = (df['Jumlah'] - df['Returned Quantity']).clip(lower=0)

    # 2. Feature Engineering (Sesuai list yang error tadi)
    df['day_sin'] = np.sin(2 * np.pi * df['Waktu Pesanan Dibuat'].dt.day / 31)
    df['day_cos'] = np.cos(2 * np.pi * df['Waktu Pesanan Dibuat'].dt.day / 31)
    
    df['log_demand'] = np.log1p(df['Net_Sales'])
    
    # Lags & Moving Average per Kategori
    df['lag_1'] = df.groupby('Kategori Produk')['log_demand'].shift(1).fillna(0)
    df['lag_7'] = df.groupby('Kategori Produk')['log_demand'].shift(7).fillna(0)
    df['lag_28'] = df.groupby('Kategori Produk')['log_demand'].shift(28).fillna(0)
    df['ma_7'] = df.groupby('Kategori Produk')['log_demand'].transform(lambda x: x.rolling(window=7).mean()).fillna(0)

    # 3. One-Hot Encoding (Sesuai Index error: Cat_Bathroom, Cat_Home, dll)
    # Kita buat manual biar urutannya presisi sesuai kemauan model
    kat_list = ['Bathroom', 'Home', 'Kitchen', 'Other', 'Storage', 'Tools']
    for k in kat_list:
        df[f'Cat_{k}'] = (df['Kategori Produk'] == k).astype(int)

    return df

def run_prediction_page():
    st.header("🔮 Sales Forecasting Dashboard")
    
    # 1. LOAD DATA INTERNAL
    df = load_internal_data()
    
    if df is None:
        st.error("❌ File 'data_from_DE.csv' tidak ditemukan. Harap cek folder src.")
        return

    # PERINGATAN STRUKTUR FILE
    with st.expander("⚠️ Baca Sebelum Prediksi (Persyaratan Data)"):
        st.write("Model Hybrid RNN-XGBoost memerlukan kolom berikut agar prediksi akurat:")
        st.code("Waktu Pesanan Dibuat, Kategori Produk, Jumlah, Returned Quantity")
        st.warning("Pastikan tidak ada data kosong (NaN) pada kolom di atas agar proses kalkulasi tidak terhenti.")

    # 2. LOAD MODEL ASSETS
    with st.spinner("Memuat model AI dan Scaler..."):
        assets = load_assets() 
    
    # 3. DETEKSI TANGGAL & JENDELA PREDIKSI
    # Gunakan 'Waktu Pesanan Dibuat'
    last_date = df['Waktu Pesanan Dibuat'].max()
    forecast_start = last_date + timedelta(days=1)
    forecast_end = last_date + timedelta(days=30)
    
    st.info(f"""
    📅 **Data Terakhir:** {last_date.strftime('%d %B %Y')}  
    🚀 **Jendela Prediksi:** {forecast_start.strftime('%d %B %Y')} s/d {forecast_end.strftime('%d %B %Y')}
    """)

    # 4. INPUT & EKSEKUSI
    # Samakan nama kolom kategori dengan dataset (Kategori Produk)
    cat_col = 'Kategori Produk' if 'Kategori Produk' in df.columns else 'Kategori'
    categories = df[cat_col].unique()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        kat_pilihan = st.selectbox("Pilih Kategori Produk:", categories)
    with col2:
        st.write("##") 
        btn_predict = st.button("Jalankan Prediksi", use_container_width=True)
    
    if btn_predict:
        try:
            with st.spinner(f"Sedang menganalisis pola harian untuk {kat_pilihan}..."):
                # Menjalankan logika hitungan rekursif
                forecast_vals = run_prediction_logic(kat_pilihan, df, assets)
                
                # Menampilkan Grafik Plotly
                fig = plot_forecast_plotly(kat_pilihan, df, forecast_vals)
                st.plotly_chart(fig, use_container_width=True)
                
                # Menampilkan Ringkasan
                total_unit = int(sum(forecast_vals))
                st.success(f"✅ Prediksi Selesai! Estimasi total permintaan {kat_pilihan}: **{total_unit} unit**.")
                
                # Tambahan: Metrik Harian
                avg_demand = round(sum(forecast_vals)/30, 2)
                st.metric("Rata-rata Permintaan Harian", f"{avg_demand} Unit/Hari")
                
        except Exception as e:
            st.error(f"Gagal memproses prediksi. Error: {e}")