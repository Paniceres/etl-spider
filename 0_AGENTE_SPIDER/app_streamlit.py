import streamlit as st
import pandas as pd
import json

import logging
import os
import logging.handlers
from 0_AGENTE_SPIDER.src.core_logic import run_spider
# Define file paths
CONFIG_DIR = "0_agente_spider/config"
RAW_DATA_DIR = "0_AGENTE_SPIDER/data/raw" # Modified to point to the raw data directory
CITIES_FILE = os.path.join(CONFIG_DIR, "cities.json")

LOG_DIR = "0_AGENTE_SPIDER/data/logs"
LOG_FILE = os.path.join(LOG_DIR, "spider.log")

# Configure Streamlit logging
STREAMLIT_LOG_FILE = os.path.join(LOG_DIR, "streamlit.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler(STREAMLIT_LOG_FILE, maxBytes=1024 * 1024, backupCount=5)
    ]
)
def save_keywords(city, keywords):
    """Saves the keywords string to a city-specific CSV file."""
    keywords_file = os.path.join(CONFIG_DIR, f"keywords_{city}.csv")
    with open(keywords_file, "w") as f:
        f.write(keywords)

def main():
    """
    Main function to run the Streamlit application for the Spider agent.
    """
    st.set_page_config(layout="wide")

    # Ensure necessary directories exist
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    # --- Sidebar (Configuration for Scraping) ---
    st.sidebar.header("🕷️ Configuración de Scraping")

    # Load cities from cities.json
    cities = {}
    try:
        with open(CITIES_FILE, 'r') as f:
            cities = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        st.sidebar.warning(f"'{CITIES_FILE}' not found or is empty. Please add city data.")

    # Check if cities are loaded (excluding the example data if it exists and is the only entry)
    if not cities or (len(cities) == 1 and list(cities.keys())[0] == 'Example City'):
         st.sidebar.info(f"Please populate '{CITIES_FILE}' with your actual city data.")

    city_options = list(cities.keys())
    selected_cities = st.sidebar.multiselect("Seleccionar Ciudad(es) a Procesar", options=city_options)

 # Use session state to keep track of keyword text area values
 if 'keyword_values' not in st.session_state:
 st.session_state.keyword_values = {}

    # Text areas for keywords for selected cities
    with st.sidebar.expander("Configurar Keywords por Ciudad"):
 for city in selected_cities:
 # Load existing keywords if not already in session state
 if city not in st.session_state.keyword_values:
                keywords_file = os.path.join(CONFIG_DIR, f"keywords_{city}.csv")
                initial_keywords = ""
 if os.path.exists(keywords_file):
 with open(keywords_file, 'r') as f:
 try:
                            initial_keywords = f.read()
 except Exception as e:
 # Display error related to file reading in the main area
 st.error(f"Error al leer las palabras clave para {city} desde el archivo: {e}")
                st.session_state.keyword_values[city] = initial_keywords

            # Display the text area and update session state on change
 st.session_state.keyword_values[city] = st.text_area(f"Keywords para {city}", value=st.session_state.keyword_values.get(city, ""), height=100, key=f"keywords_{city}_text")

 if st.button(f"Guardar Keywords para {city}", key=f"save_button_{city}"):
 save_keywords(city, st.session_state.keyword_values[city])
 st.success(f"Palabras clave guardadas para {city}.")


 # Options for Scraping (Depth and Emails)
 depth = st.sidebar.slider("Profundidad de Búsqueda (depth)", min_value=1, max_value=20, value=5)
 extract_emails = st.sidebar.checkbox("¿Extraer Emails?", value=True)


 if st.sidebar.button("🚀 Iniciar Scraping"):
 if not selected_cities:
 st.sidebar.warning("Please select at least one city to start scraping.")
 else:
 config = {
 "cities": selected_cities,
 "keywords": {},
 }
            for city in selected_cities:
                # Get keywords from the text area state
                # st.session_state provides access to the current state of widgets
                keywords_key = f"keywords_{city}_text"
                if keywords_key in st.session_state:
                    # Split by lines and filter empty ones
                    config["keywords"][city] = [line.strip() for line in st.session_state[keywords_key].splitlines() if line.strip()]
                else:
                    # If session state is not available for some reason, try loading from file as a fallback
                    keywords_file = os.path.join(CONFIG_DIR, f"keywords_{city}.csv")
                    if os.path.exists(keywords_file):
 try:
 with open(keywords_file, 'r') as f: # Use \'r\' for reading text files
 config["keywords"][city] = [line.strip() for line in f if line.strip()] # Read line by line
 except Exception as e:
 st.error(f"Error reading keywords for {city} from file: {e}") # Use st.error in main area
 # Handle case where keywords are not in session state and file read failed
 if city not in config["keywords"]:
 config["keywords"][city] = [] # Ensure city has an empty keyword list if loading fails
            
            config["depth"] = depth
            config["extract_emails"] = extract_emails

 # Placeholder for displaying scraping status in main area
 scraping_status_placeholder = st.empty()
 with st.spinner("Scraping iniciado..."):
 try: # Wrap the scraping logic in try-except for better error reporting
 scraped_data = run_spider(config) # Call the scraping function
 st.success("Scraping completado!") # Success message
 except Exception as e: # Catch any exceptions during scraping
 st.error(f"Error durante el scraping: {e}") # Display error message in main area

 if 'scraped_data' in locals():
 if not scraped_data.empty:
                scraping_status_placeholder.success("Scraping completado!")
    # --- Main Area (Display Raw Data) ---

    tab_crudos, tab_logs = st.tabs(["Crudos", "Logs"])

    # List available raw CSV files
    with tab_crudos:
        st.header("Datos Crudos Generados")
        raw_files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith(".csv")]

        if not raw_files:
            st.info("No hay archivos CSV crudos generados aún.")
        else:
            selected_file = st.selectbox("Seleccionar archivo crudo para previsualizar:", raw_files)
            file_path = os.path.join(RAW_DATA_DIR, selected_file)
            try:
                df_raw = pd.read_csv(file_path)
                # Display summary of the DataFrame
                st.info(f"Archivo: {selected_file} | Filas: {df_raw.shape[0]} | Columnas: {df_raw.shape[1]}")
            except Exception as e:
                st.error(f"Error al cargar el archivo CSV '{selected_file}': {e}")
            st.dataframe(df_raw)
            st.download_button(label=f"Descargar {selected_file}", data=df_raw.to_csv(index=False), file_name=selected_file, mime="text/csv")

        # Display the scraped data after the run (if available)
        if 'scraped_data' in locals() and not scraped_data.empty:
            st.subheader("Últimos Datos Scrapeados (Preview)")
            st.dataframe(scraped_data)

    with tab_logs:
        st.header("Registros de Ejecución")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                log_content = f.read()
            st.text_area("Contenido del Log", log_content, height=400)
        else:
            st.info("Log file not found.")


if __name__ == "__main__":
    main()