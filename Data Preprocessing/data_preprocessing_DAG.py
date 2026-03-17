# Import database connectivity library
import psycopg2
from psycopg2.extras import execute_values

# Import data processing libraries
import pandas as pd
import numpy as np
import glob
import os

# Import date & time utilities libarires
import datetime as dt
import pendulum

# Import elasticsearch libraries
from elasticsearch import Elasticsearch
from elasticsearch import helpers

# Import airflow libraries
from airflow import DAG
from airflow.operators.python import PythonOperator

def loadToPostgre():
    # Establish connection to PostgreSQL database
    conn = psycopg2.connect(dbname="final_project", user="postgres", password="postgres")
    cursor = conn.cursor()

    # Datasets path
    folder_path = r".\dataset\RAW_PUBLIC_Dataset\RAW_PUBLIC"
    file_paths = glob.glob(os.path.join(folder_path, "*.xlsx"))

    # Read file
    for file in file_paths:
        # Read Excel
        df = pd.read_excel(file)

        # Add source file column
        df["source_file"] = os.path.basename(file)

        # Replace NaN with None for PostgreSQL
        df = df.where(pd.notnull(df), None)

        # Prepare columns dynamically
        columns = list(df.columns)
        values = [tuple(row) for row in df.to_numpy()]

        quoted_columns = [f'"{col}"' for col in columns]

        insert_query = f"""
            INSERT INTO table_orders ({','.join(quoted_columns)})
            VALUES %s
        """

        # Bulk insert
        execute_values(cursor, insert_query, values)
        conn.commit()

    # Close connection
    cursor.close()
    conn.close()

def fromPostgre():
    # Establish connection to PostgreSQL database
    conn = psycopg2.connect(dbname="final_project", user="postgres", password="postgres")
    
    # Load SQL query result to dataframe and save to CSV file
    data = pd.read_sql_query("SELECT * FROM table_orders;", conn)
    data.to_csv('raw_data_SQL.csv', index=False)

    # Close database connection
    conn.close()

def cleanData():
    # Read csv to dataframe
    df = pd.read_csv("raw_data_SQL.csv", low_memory=False)

    # Drop duplicate rows
    df = df.drop_duplicates()

    # Drop columns having almost completely missing values (above 20,000 except for 'Alasan Pembatalan') + useless columns
    cols_to_drop = [
        "Waktu Pengiriman Diatur",
        "Status Pembatalan/ Pengembalian",
        "No. Resi",
        "Antar ke counter/ pick-up",
        "Pesanan Harus Dikirimkan Sebelum (Menghindari keterlambatan)",
        "Waktu Pembayaran Dilakukan",
        "SKU Induk",
        "Nomor Referensi SKU",
        "Nama Variasi",
        "Harga Awal",
        "Harga Setelah Diskon",
        "Total Harga Produk",
        "Diskon Dari Penjual",
        "Diskon Dari Shopee",
        "Berat Produk",
        "Jumlah Produk di Pesan",
        "Voucher Ditanggung Penjual",
        "Cashback Koin",
        "Voucher Ditanggung Shopee",
        "Paket Diskon",
        "Paket Diskon (Diskon dari Shopee)",
        "Paket Diskon (Diskon dari Penjual)",
        "Potongan Koin Shopee",
        "Diskon Kartu Kredit",
        "Ongkos Kirim Pengembalian Barang",
        "Catatan dari Pembeli",
        "Catatan",
        "Username (Pembeli)",
        "Nama Penerima",
        "No. Telepon",
        "Alamat Pengiriman",
        "Waktu Pesanan Selesai",
        "order_id",
        "Kota/Kabupaten",
        "source_file"
    ]

    # Drop the selected columns
    df = df.drop(columns=cols_to_drop)

    # Convert to datetime datatype
    df['Waktu Pesanan Dibuat'] = pd.to_datetime(df['Waktu Pesanan Dibuat'])

    # Remove ' gr' and convert to integer
    df["Total Berat"] = df["Total Berat"].str.replace(" gr", "", regex=False).str.strip().astype(int)

    # Remove '.' separator and convert to integer
    df["Total Pembayaran"] = df["Total Pembayaran"].str.replace(".", "", regex=False).str.strip().astype(int)

    # Create mapping dictionary
    category_mapping = {
        # Kitchen & Dining
        "Mangkok Sambal / Saus": "Kitchen & Dining",
        "Nampan / Tray": "Kitchen & Dining",
        "Talenan": "Kitchen & Dining",
        "Saringan / Strainer": "Kitchen & Dining",
        "Botol / Gelas / Mug": "Kitchen & Dining",
        "Peralatan Makan": "Kitchen & Dining",
        "Mangkok": "Kitchen & Dining",
        "Piring": "Kitchen & Dining",
        "Pisau / Alat Potong": "Kitchen & Dining",
        "Teko / Jug": "Kitchen & Dining",
        "Baskom / Mangkok Besar": "Kitchen & Dining",
        "Cobek / Ulekan": "Kitchen & Dining",
        "Spatula": "Kitchen & Dining",
        "Pengolah Bumbu / Sayur": "Kitchen & Dining",

        # Food Storage & Packaging
        "Tempat Nasi": "Food Storage & Packaging",
        "Toples / Sealware": "Food Storage & Packaging",
        "Perlengkapan Packing": "Food Storage & Packaging",
        "Plastik / Wadah Plastik": "Food Storage & Packaging",
        "Lunch Box / Rantang": "Food Storage & Packaging",

        # Bathroom & Cleaning
        "Aksesoris Mandi": "Bathroom & Cleaning",
        "Peralatan Kamar Mandi": "Bathroom & Cleaning",
        "Tempat Sampah": "Bathroom & Cleaning",
        "Sapu / Pembersih Lantai": "Bathroom & Cleaning",
        "Sikat / Pembersih": "Bathroom & Cleaning",
        "Gayung": "Bathroom & Cleaning",

        # Home Organization & Living
        "Celengan": "Home Organization & Living",
        "Rak / Rak Serbaguna": "Home Organization & Living",
        "Keranjang": "Home Organization & Living",
        "Bangku / Kursi Kecil": "Home Organization & Living",
        "Gantungan Baju / Hanger": "Home Organization & Living",
        "Pot Tanaman / Bunga": "Home Organization & Living",

        # Tools & Accessories
        "Stempel / Alat Kantor": "Tools & Accessories",
        "Seal / Baut / Roof": "Tools & Accessories",
        "Aksesoris Pintu": "Tools & Accessories",
        "Perkakas": "Tools & Accessories",
        "Aksesoris ID Card": "Tools & Accessories",
        "Aksesoris Motor": "Tools & Accessories",

        # Other
        "Other": "Other"
    }

    # Create new grouped column
    df["product_category_grouped"] = df["product_category"].map(category_mapping)

    # Standardize 'Status Pesanan'
    df["Status Pesanan"] = df["Status Pesanan"].replace(to_replace=r"Pesanan diterima.*", value="Pesanan Diterima", regex=True)

    # Create Jenis Pembatalan
    df["Jenis Pembatalan"] = np.select(
        [
            df["Alasan Pembatalan"].str.contains("Dibatalkan oleh Pembeli", na=False),
            df["Alasan Pembatalan"].str.contains("Dibatalkan oleh Penjual", na=False),
            df["Alasan Pembatalan"].str.contains("Dibatalkan secara otomatis oleh sistem", na=False),
        ],
        [
            "Pembeli",
            "Penjual",
            "Sistem Otomatis"
        ],
        default=np.nan
    )

    # Extract raw cancellation reasons
    df["Alasan Pembatalan Clean"] = (
        df["Alasan Pembatalan"]
        .str.replace(r"Dibatalkan oleh Pembeli\. Alasan: ", "", regex=True)
        .str.replace(r"Dibatalkan oleh Penjual\. Alasan: ", "", regex=True)
        .str.replace(r"Dibatalkan secara otomatis oleh sistem\. Alasan: ", "", regex=True)
    )

    # Map the cancellation reasons
    reason_mapping = {
        # PEMBELI
        "Ubah Pesanan yang Ada": "Ubah Pesanan yang Ada",
        "Perlu mengubah pesanan": "Perlu mengubah pesanan",
        "Lainnya/ berubah pikiran": "Lainnya/ berubah pikiran",
        "Need to change delivery address": "Perlu mengubah alamat pengiriman",
        "Perlu mengubah alamat pengiriman": "Perlu mengubah alamat pengiriman",
        "Menemukan yang lebih murah": "Menemukan yang lebih murah",
        "Penjual tidak responsif terhadap pertanyaan Pembeli": "Penjual tidak responsif",
        "Proses pembayaran sulit": "Proses pembayaran sulit",
        "Perlu mengubah Voucher": "Perlu mengubah voucher",
        "Tidak ingin membeli lagi": "Tidak ingin membeli lagi",
        "Lainnya": "Lainnya",

        # PENJUAL
        "Produk habis": "Produk habis",

        # SISTEM OTOMATIS
        "Paket hilang di perjalanan. Kompensasi yang memenuhi syarat telah dikreditkan ke Saldo Penjual-mu.": "Paket hilang di perjalanan",
        "Penjual gagal mengirimkan pesanan tepat waktu": "Penjual gagal mengirimkan pesanan tepat waktu",
        "Pengiriman gagal": "Pengiriman gagal",
        "Penjual tidak mengatur pengiriman tepat waktu": "Penjual tidak mengatur pengiriman tepat waktu",
    }

    # Create new column with the mapped cancellation reason
    df["Alasan Pembatalan Final"] = df["Alasan Pembatalan Clean"].map(reason_mapping)
    df.loc[(df["Jenis Pembatalan"] == "Sistem Otomatis") & (df["Alasan Pembatalan Final"].isna()), "Alasan Pembatalan Final"] = "Lainnya"

    # Map the shipping methods to the shipping brands
    mapping_shipping = {
        'Reguler (Cashless)-SPX Standard': ('SPX', 'Reguler'),
        'Hemat Kargo-SPX Hemat': ('SPX', 'Hemat'),
        'Hemat Kargo-J&T Economy': ('J&T', 'Hemat'),
        'Instant (Versi Lama)-SPX Instant (Versi Lama)': ('SPX', 'Instant Delivery'),
        'Agen SPX Express': ('SPX', 'Pick Up Point'),
        'Instant (Versi Lama)-GrabExpress Instant (Versi Lama)': ('GrabExpress', 'Instant Delivery'),
        'Reguler (Cashless)-J&T Express': ('J&T', 'Reguler'),
        'Same Day-SPX Sameday': ('SPX', 'Same Day Delivery'),
        'Reguler (Cashless)-JNE Reguler': ('JNE', 'Reguler'),
        'Hemat Kargo': ('Platform Default', 'Hemat'),
        'Kargo-JNE Trucking (JTR)': ('JNE', 'Kargo'),
        'Kargo-J&T Cargo': ('J&T', 'Kargo'),
        'Next Day-JNE YES': ('JNE', 'Express'),
        'Instant (Versi Lama)': ('Platform Default', 'Instant Delivery'),
        'Same Day-GoSend Same Day': ('GoSend', 'Same Day Delivery'),
        'SPX Express Point': ('SPX', 'Pick Up Point'),
        'Instant (Versi Lama)-GoSend Instant (Versi Lama)': ('GoSend', 'Instant Delivery'),
        'Reguler (Cashless)': ('Platform Default', 'Reguler'),
        'GrabExpress Instant (Versi Lama)': ('GrabExpress', 'Instant Delivery'),
        'SPX Hemat': ('SPX', 'Hemat'),
        'SPX Standard': ('SPX', 'Reguler'),
        'J&T Cargo': ('J&T', 'Kargo'),
        'J&T Express': ('J&T', 'Express'),
        'GrabExpress Sameday': ('GrabExpress', 'Same Day Delivery'),
        'JNE Reguler': ('JNE', 'Reguler'),
        'GoSend Same Day': ('GoSend', 'Same Day Delivery'),
        'SPX Sameday': ('SPX', 'Same Day Delivery'),
        'Kargo': ('Platform Default', 'Kargo'),
        'Same Day': ('Platform Default', 'Same Day Delivery'),
        'Next Day': ('Platform Default', 'Express'),
        'Hemat Kargo-JNE Trucking (JTR)': ('JNE', 'Kargo'),
        'Hemat Kargo-J&T Cargo': ('J&T', 'Kargo'),
        'GoSend Instant (Versi Lama)': ('GoSend', 'Instant Delivery'),
        'SPX Instant (Versi Lama)': ('SPX', 'Instant Delivery'),
        'J&T Economy': ('J&T', 'Hemat'),
        'JNE Trucking (JTR)': ('JNE', 'Kargo'),
        'JNE YES': ('JNE', 'Express'),
        'Instant-SPX Instant': ('SPX', 'Instant Delivery'),
        'GrabExpress Instant': ('GrabExpress', 'Instant Delivery'),
        'Instant': ('Platform Default', 'Instant Delivery'),
        'Instant Prioritas-SPX Instant Prioritas': ('SPX', 'Instant Delivery'),
        'SPX Instant': ('SPX', 'Instant Delivery'),
        'GoSend Instant Prioritas': ('GoSend', 'Instant Delivery'),
        'SPX Instant Prioritas': ('SPX', 'Instant Delivery'),
        'Gosend Instant': ('GoSend', 'Instant Delivery')
    }

    # Create new column with the mapped shipping methods
    df[['Ekspedisi', 'Metode Pengiriman']] = df['Opsi Pengiriman'].map(mapping_shipping).apply(pd.Series)

    # Drop old columns
    df = df.drop(columns=["product_category", "Alasan Pembatalan", 'Alasan Pembatalan Clean', 'Opsi Pengiriman'])

    # Rename columns
    df = df.rename(columns={
        "product_category_grouped": "Kategori Produk",
        "Alasan Pembatalan Final": "Alasan Pembatalan",
        "Returned quantity": "Returned Quantity"
    })

    # Capitalize each province word
    df['Provinsi'] = df['Provinsi'].str.title()

    # Change unit into thousands
    cols = [
        "Total Diskon",
        "Ongkos Kirim Dibayar oleh Pembeli",
        "Estimasi Potongan Biaya Pengiriman",
        "Perkiraan Ongkos Kirim"
    ]
    df[cols] = df[cols] * 1000

    # Change weight unit from gr to kg
    df['Total Berat'] = df['Total Berat'] / 1000

    # Filter only for data that doesn't contain missing 'Waktu Pesanan Dibuat' values
    df = df[df["Waktu Pesanan Dibuat"].notnull()]

    # Mask for Batal and Selesai with missing return
    mask_batal = (df["Status Pesanan"] == "Batal") & df["Returned Quantity"].isna()
    mask_selesai = (df["Status Pesanan"] == "Selesai") & df["Returned Quantity"].isna()

    # Impute cancelled orders with coressponding Jumlah
    df.loc[mask_batal, "Returned Quantity"] = df.loc[mask_batal, "Jumlah"]

    # Impute completed orders with 0
    df.loc[mask_selesai, "Returned Quantity"] = 0

    # Convert to integer
    df["Returned Quantity"] = df["Returned Quantity"].astype(int)

    # Create new features for net quantity sold and is weekend boolean
    df["Jumlah Terjual Bersih"] = df["Jumlah"] - df["Returned Quantity"]
    df["Weekend"] = (df["Waktu Pesanan Dibuat"].dt.weekday >= 5).astype(int)

    # Save cleaned data to csv file
    df.to_csv("cleaned_data_analysis_SQL.csv", index=False, encoding="utf-8")

def preprocessForecasting():
    # Read csv to dataframe
    df = pd.read_csv("cleaned_data_analysis_SQL.csv")

    # Convert to datetime
    df['Waktu Pesanan Dibuat'] = pd.to_datetime(df['Waktu Pesanan Dibuat'])

    # Copy dataframe where 'Status Pesanan' is completed
    df_forecast = df[df["Status Pesanan"] == "Selesai"].copy()

    # Sort and set Waktu Pesanan Dibuat as index
    df_forecast = df_forecast.sort_values("Waktu Pesanan Dibuat")
    df_forecast = df_forecast.set_index("Waktu Pesanan Dibuat")

    # Initialize a list of for storing datafranes
    df_forecast_categories = {}

    # Create dataframes aggregated by daily frequency per product categories
    for cat in df_forecast["Kategori Produk"].unique():
        df_cat = df_forecast[df_forecast["Kategori Produk"] == cat].resample("D").agg({
            "Jumlah": "sum",
            "Returned Quantity": "sum",
            "Total Pembayaran": "sum",
            "Total Diskon": "sum",
            "Ongkos Kirim Dibayar oleh Pembeli": "sum",
            "Jumlah Terjual Bersih": "sum",
            "Weekend": "max"
        }).fillna(0)
        
        df_forecast_categories[cat] = df_cat

    # Create dataframe aggregated by daily frequency
    df_forecast = df_forecast.resample("D").agg({
        "Jumlah": "sum",
        "Returned Quantity": "sum",
        "Total Pembayaran": "sum",
        "Total Diskon": "sum",
        "Ongkos Kirim Dibayar oleh Pembeli": "sum",
        "Jumlah Terjual Bersih": "sum",
        "Weekend": "max"
    }).fillna(0)

    # Save ready-to-use forecasting dataframe to a new CSV file
    df_forecast.to_csv("forecast_data_SQL.csv", index=True, encoding="utf-8")
    df_forecast_categories["Kitchen & Dining"].to_csv("forecast_kitchen_data_SQL.csv", index=True, encoding="utf-8")
    df_forecast_categories["Food Storage & Packaging"].to_csv("forecast_storage_data_SQL.csv", index=True, encoding="utf-8")
    df_forecast_categories["Bathroom & Cleaning"].to_csv("forecast_bathroom_data_SQL.csv", index=True, encoding="utf-8")
    df_forecast_categories["Home Organization & Living"].to_csv("forecast_home_data_SQL.csv", index=True, encoding="utf-8")
    df_forecast_categories["Tools & Accessories"].to_csv("forecast_tools_data_SQL.csv", index=True, encoding="utf-8")
    df_forecast_categories["Other"].to_csv("forecast_other_data_SQL.csv", index=True, encoding="utf-8")

def postToElastic():
    # Initialize elasticsearch
    es = Elasticsearch("http://elasticsearch:9200")

    # Read csv to dataframe
    df = pd.read_csv("cleaned_data_analysis_SQL.csv")

    # Convert dataframe into json format
    actions = [
        {
            "_index": "cleaned_data",
            "_source": r.to_json()
        }
        for i, r in df.iterrows()
    ]

    # Bulk insert
    helpers.bulk(es, actions)

# Default arguments
default_args = {
    'owner': 'demandSenseAI',
    'start_date': dt.datetime(2026, 3, 1, 3, 0, tzinfo=pendulum.timezone("Asia/Jakarta")), # Start from 01 March 2026 03:00 AM
    'retries': 1,
    'retry_delay': dt.timedelta(seconds=30),
}

# Define DAG with interval of 30 minutes every monday 03:00-06:00 AM
with DAG('demandSenseAI_pipeline', default_args=default_args, schedule_interval = "0,30 3-6 * * 1", catchup=False) as dag:
    # Node to load data to PostGreSQL
    load_postgre = PythonOperator(task_id='load_to_postgre', python_callable=loadToPostgre)
    
    # Node to fetch data from PostGreSQL
    fetch_postgre = PythonOperator(task_id='fetch_from_postgre', python_callable=fromPostgre)

    # Node to clean data and save to CSV
    clean_data = PythonOperator(task_id='clean_data', python_callable=cleanData)

    # Node to prepare data for forecasting and save to CSV
    forecast_data = PythonOperator(task_id='forecast_data', python_callable=preprocessForecasting)

    # Node to load cleaned CSV and post to Elasticsearch
    post_to_elasticsearch = PythonOperator(task_id='post_to_elasticsearch', python_callable=postToElastic)

# Define pipeline
load_postgre >> fetch_postgre >> clean_data >> forecast_data >> post_to_elasticsearch