import streamlit as st
import pandas as pd
import os

# Define file paths based on the provided structure
CONFIG_DIR = "0_agente_spider/config"
# Modified to point to the raw data directory
RAW_DATA_DIR = "0_agente_spider/data/raw" # Modified to point to the raw data directory
PARAMETERS_FILE = os.path.join(CONFIG_DIR, "parameters_default.json")

# Ensure the raw data directory exists
os.makedirs(RAW_DATA_DIR, exist_ok=True)


def main():
    """
    Main function to run the Streamlit application for the Spider agent.
    """
    st.set_page_config(layout="wide")

    # --- Sidebar (Configuration for Scraping) ---
    st.sidebar.header("Configuración del Spider")

    # TODO: Add st.multiselect for "Seleccionar Ciudad(es)"
    # TODO: Add st.text_area and button for "Keywords para X"
    # TODO: Add st.slider or st.number_input for "depth"
    # TODO: Add st.checkbox for "¿Extraer Emails?"

    # TODO: Add st.button for "🚀 Iniciar Scraping"

    # --- Main Area (Display Raw Data) ---
    st.title("🕷️ Agente Spider GOSOM")

    # This agent focuses only on generating raw data.
    # Consolidation, chunking, and detailed statistics are handled by the Central ETL process.
    st.header("Datos Crudos Generados")

    # List available raw CSV files
    raw_files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith(".csv")]

    if not raw_files:
        st.info("No hay archivos CSV crudos generados aún.")
    else:
        selected_file = st.selectbox("Seleccionar archivo crudo para previsualizar:", raw_files)
        file_path = os.path.join(RAW_DATA_DIR, selected_file)
        df_raw = pd.read_csv(file_path)

        st.dataframe(df_raw)
        st.download_button(label=f"Descargar {selected_file}", data=df_raw.to_csv(index=False), file_name=selected_file, mime="text/csv")


if __name__ == "__main__":
    main()