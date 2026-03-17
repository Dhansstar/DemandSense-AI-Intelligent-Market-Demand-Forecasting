# 🛒 DemandSense AI: Intelligent Market Demand Forecasting
**Hybrid Deep Learning Ensemble Framework for E-Commerce Predictive Analytics**

<div align="center">

![DemandSense AI Logo](demandSenseAI_logo.jpeg)

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-Enabled-FF6F00?style=for-the-badge&logo=tensorflow)](https://www.tensorflow.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-Ensemble-blue?style=for-the-badge)](https://xgboost.ai/)
[![Airflow](https://img.shields.io/badge/Apache--Airflow-Automated-017CEE?style=for-the-badge&logo=apache-airflow)](https://airflow.apache.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)

</div>

---

## 📌 1. Project Overview
**DemandSense AI** adalah solusi analitik prediktif yang dirancang untuk mengatasi volatilitas permintaan di industri e-commerce Indonesia. Dengan memanfaatkan data transaksi dari Desember 2023 hingga November 2025, sistem ini mengintegrasikan **Automated Data Pipelines** dengan **Hybrid Machine Learning Models** untuk memprediksi kuantitas permintaan produk per kategori dalam satu bulan ke depan.

### Core Objectives:
* **Mitigasi Risiko:** Mencegah *Stockout* (kehilangan revenue) dan *Overstock* (biaya gudang berlebih).
* **Efisiensi Operasional:** Optimalisasi alokasi budget promosi dan perencanaan *supply chain* berbasis data.
* **Accuracy:** Memberikan estimasi volume penjualan dengan metriks **MAPE** dan **Volume Accuracy** yang tinggi.

---

## 📁 2. Repository Architecture & Filepath
Struktur folder dirancang untuk mendukung siklus hidup data (End-to-End Data Lifecycle):

```text
main/
├── ⚙️ Data Preprocessing/
│   ├── raw dataset/          # Raw e-commerce transaction (Dec 2023 - Nov 2025)
│   ├── analysis_dataset/     # Cleaned features for Exploratory Analysis
│   ├── modelling_dataset/    # Categorical-specific time-series datasets (Bathroom, Home, Kitchen, etc.)
│   ├── data_preprocessing.ipynb  # ETL Engine & Feature Engineering logic
│   ├── data_preprocessing_DAG.py # Airflow Automation for DB-to-Cloud pipeline
│   └── data_pipeline.png     # Visual flow of Automated ETL
|
├── 📊 Data Analysis/
│   ├── data_analysis.ipynb   # Demand pattern & driver identification
│   └── sales_dashboard.pbix  # Interactive Power BI Strategic Dashboard
|
├── 🤖 Data Modelling/
│   ├── data_modeling.ipynb   # Hybrid RNN + XGBoost Training Pipeline
│   ├── model_rnn.h5          # Deep Learning Temporal Feature Extractor
│   ├── xgb_vol.joblib        # Gradient Boosting for Volume Accuracy
│   └── *.joblib/*.h5         # Model artifacts (Scalers, Encoders, Extractors)
|
├── 🚀 deployment/
│   ├── src/                  # Streamlit App (EDA & Prediction Page)
│   ├── Dockerfile            # Containerization for cross-platform stability
│   └── requirements.txt      # Dependency manifest
|
└── demandSenseAI_logo.jpeg   # Project Identity
```

---

## 🔬 3. Methodology & Technical Stack

### 📡 A. Automated Data Engineering & Pipeline
Sistem ini mengintegrasikan **Apache Airflow** untuk menjamin data selalu *up-to-date* dan bersih sebelum masuk ke tahap modelling:
* **Database:** PostgreSQL sebagai *Single Source of Truth* untuk menyimpan 26,258 catatan pesanan.
* **Orchestration (`data_preprocessing_DAG.py`):** Mengotomasi proses loading data, pembersihan *missing values*, hingga upload dataset siap pakai secara terjadwal.
* **Analysis Scope:** Mengevaluasi faktor logistik (Shipping cost/method), pola pembelian (Weekday vs Weekend), dan dampak tingkat pengembalian produk (*Operational Factors*).

### ⚙️ B. Hybrid Deep Learning Ensemble Architecture
Gue merancang arsitektur model yang menggabungkan kekuatan **Temporal Awareness** dan **Gradient Boosting**:
* **RNN Feature Extractor (`model_rnn.h5`):** Digunakan untuk menangkap dependensi waktu jangka panjang dan fluktuasi musiman (*Seasonality*).
* **XGBoost Meta-Learner:** Output dari RNN dikombinasikan dengan fitur kategorikal melalui XGBoost untuk memprediksi **Volume Accuracy** dan menekan nilai **MAPE**.
* **Evaluation Metrics:** Fokus utama pada akurasi total volume prediksi terhadap volume aktual untuk menjamin efisiensi *Working Capital*.

---

## 🚀 4. Deployment & System Integration
Solusi ini dideploy menggunakan arsitektur modern untuk menjamin stabilitas dan aksesibilitas:

* **Framework:** **Streamlit** untuk UI interaktif yang mencakup halaman EDA (Exploratory Data Analysis) dan Prediction.
* **Containerization:** Menggunakan **Docker** untuk memastikan aplikasi berjalan konsisten di berbagai *environment* (Local, Cloud, atau HuggingFace).
* **Workflow Deployment:**
  1. Pengguna memilih kategori produk (misal: *Kitchen & Dining*).
  2. Model memproses input dan menghasilkan prediksi permintaan untuk 1 bulan ke depan.
  3. Visualisasi Power BI memberikan *insight* tambahan mengenai distribusi geografis dan pola transaksi.

---

## 📊 5. Project Output & Business Impact
* **Inventory Accuracy:** Meminimalkan risiko *Stockout* dan *Overstock* hingga level kategori terkecil (Bathroom, Kitchen, Tools, etc.).
* **Data-Driven Promotion:** Mengidentifikasi periode terbaik untuk aktivasi voucher/diskon berdasarkan pola demand historis.
* **Logistics Optimization:** Mengurangi biaya logistik dengan perencanaan distribusi yang lebih akurat sebelum lonjakan permintaan terjadi.

---

## 🔗 6. Reference & Live Access
* **Interactive App:** [HuggingFace ForecastingApp](https://forecastingapp-myproject.streamlit.app/)
* **Dataset Source:** [Indonesia E-Commerce Sales (Kaggle)](https://www.kaggle.com/datasets/bakitacos/indonesia-e-commerce-sales-and-shipping-20232025)
* **Strategy Slides:** [Presentation Deck](https://docs.google.com/presentation/d/1jSPtnN4fhYYo9X-LHmDsqbEbl2I3Py_hnNuDLsW3Z10/edit?usp=sharing)
* **Scientific Reference:** [Hybrid RNN-XGBoost Journal](https://jcasc.com/index.php/jcasc/article/view/3736)

---
**Author:** Risyadhana Syaifuddin | Data Science & ML Engineering Practitioner