import streamlit as st
from eda import run_eda
from prediction_forecast import run_product_forecast
from predicition_csv import run_prediction_page

st.set_page_config(page_title="Forecasting Dashboard", layout="wide")

def main():
    st.sidebar.title("🤖 AI Forecaster")
    menu = st.sidebar.radio("Menu:", ["Home", "EDA", "Forecast", "Upload CSV"])

    if menu == "Home":
        st.title("Selamat Datang")
    elif menu == "EDA":
        run_eda() # Load CSV ada di dalem sini
    elif menu == "Forecast":
        run_product_forecast() # Load CSV juga di dalem sini
    elif menu == "Upload CSV":
        run_prediction_page() # Upload di dalem sini

if __name__ == "__main__":
    main()