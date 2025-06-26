# 0_AGENTE_SPIDER/app_streamlit.py
import streamlit as st
import pandas as pd
import json
import asyncio
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime

# --- Añadir src al PYTHONPATH para importar core_logic ---
APP_ROOT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.join(APP_ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

# --- Importar Lógica Core con Fallback a Dummies ---
CORE_LOGIC_LOADED = False
try:
    from core_logic import run_spider
    CORE_LOGIC_LOADED = True
    print("INFO (streamlit): core_logic.py cargado exitosamente.")
except ImportError as e:
    print(f"ERROR (streamlit): No se pudo importar de 'src/core_logic.py': {e}")
    # Definir una función dummy para que la app no se rompa
    async def run_spider(config):
        st.error("La lógica de scraping real no se pudo cargar. Ejecutando en modo simulación.")
        await asyncio.sleep(2)
        return pd.DataFrame([{'nombre_negocio': 'Error al cargar core_logic.py'}])

# --- Configuración de Rutas y Logging ---
CONFIG_DIR = os.path.join(APP_ROOT_DIR, 'config')
RAW_DATA_DIR = os.path.join(APP_ROOT_DIR, 'data', 'raw')
LOGS_DIR = os.path.join(APP_ROOT_DIR, 'data', 'logs')
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Configurar un logger específico para la UI de Streamlit
ui_log_file = os.path.join(LOGS_DIR, "streamlit_ui.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(ui_log_file, maxBytes=512*1024, backupCount=3)
    ]
)
ui_logger = logging.getLogger("StreamlitUI")

# --- Funciones de Ayuda ---
@st.cache_data # Cachear para no recargar en cada rerun
def load_cities_from_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        st.sidebar.error(f"No se pudo cargar '{os.path.basename(file_path)}'.")
        return {}

def load_keywords_from_csv(city_name):
    keywords_file = os.path.join(CONFIG_DIR, f"keywords_{city_name.lower()}.csv")
    if os.path.exists(keywords_file):
        with open(keywords_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "" # Devuelve string vacío si no existe

def save_keywords_to_csv(city_name, keywords_str):
    keywords_file = os.path.join(CONFIG_DIR, f"keywords_{city_name.lower()}.csv")
    try:
        with open(keywords_file, "w", encoding='utf-8') as f:
            f.write(keywords_str)
        return True
    except Exception as e:
        st.error(f"Error al guardar keywords para {city_name}: {e}")
        return False

# --- Función Wrapper para llamar a la lógica asíncrona ---
def run_async_task(async_func, *args, **kwargs):
    """Ejecuta una función asíncrona desde un contexto síncrono."""
    try:
        # Intenta obtener el bucle de eventos existente, crea uno nuevo si no hay
        loop = asyncio.get_running_loop()
    except RuntimeError:  # 'There is no current event loop...'
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(async_func(*args, **kwargs))


# --- UI Principal ---
st.set_page_config(page_title="Agente Spider", layout="wide")

st.title("🚀✨ Agente Spider - Generador de CSVs Crudos")
st.markdown("Configura y ejecuta tareas de scraping para generar leads.")

# Inicializar session_state
if 'scraping_results' not in st.session_state:
    st.session_state.scraping_results = None

# --- Sidebar ---
with st.sidebar:
    st.header("🕷️ Configuración de Scraping")
    
    cities_file_path = os.path.join(CONFIG_DIR, "cities.json")
    all_cities_data = load_cities_from_json(cities_file_path)
    city_options = list(all_cities_data.keys())
    
    selected_cities = st.multiselect("Seleccionar Ciudad(es)", options=city_options)

    # Text areas para keywords
    keywords_config = {}
    if selected_cities:
        with st.expander("Configurar Keywords", expanded=True):
            for city in selected_cities:
                keywords_config[city] = st.text_area(
                    f"Keywords para {city}",
                    value=load_keywords_from_csv(city),
                    height=100,
                    key=f"keywords_{city}"
                )
                if st.button(f"Guardar para {city}", key=f"save_{city}"):
                    if save_keywords_to_csv(city, keywords_config[city]):
                        st.success(f"Keywords guardadas para {city}.")

    depth = st.slider("Profundidad de Búsqueda", 1, 10, 1)
    extract_emails = st.checkbox("¿Extraer Emails?", value=False) # Desactivado por defecto para spider

    if st.button("🚀 Iniciar Scraping", type="primary", use_container_width=True):
        if not selected_cities:
            st.warning("Por favor, selecciona al menos una ciudad.")
        elif not CORE_LOGIC_LOADED:
            st.error("La lógica de scraping no está disponible. Revisa los logs de la consola.")
        else:
            # Construir el diccionario de configuración para `run_spider`
            final_config = {
                "cities": selected_cities,
                "keywords": {},
                "depth": depth,
                "extract_emails": extract_emails
            }
            for city, keywords_str in keywords_config.items():
                final_config["keywords"][city] = [line.strip() for line in keywords_str.splitlines() if line.strip()]

            ui_logger.info(f"Iniciando scraping con config: {final_config}")
            with st.spinner("Scraping en progreso... Esto puede tardar varios minutos."):
                try:
                    # Usar el wrapper para llamar a la función asíncrona
                    results_df = run_async_task(run_spider, final_config)
                    st.session_state.scraping_results = results_df # Guardar resultados en session_state
                    st.success("¡Scraping completado!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Ocurrió un error crítico durante el scraping: {e}")
                    ui_logger.error(f"Error crítico en run_spider: {e}", exc_info=True)
                    st.session_state.scraping_results = None # Limpiar resultados en caso de error

# --- Área Principal ---
tab_resultados, tab_logs = st.tabs(["📊 Resultados de Scraping", "📜 Logs"])

with tab_resultados:
    st.header("Resultados")

    # Mostrar los últimos resultados del scraping
    if st.session_state.scraping_results is not None:
        st.subheader("Resultados de la Última Ejecución")
        if not st.session_state.scraping_results.empty:
            st.dataframe(st.session_state.scraping_results)
            csv = st.session_state.scraping_results.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                "📥 Descargar CSV de Última Ejecución",
                data=csv,
                file_name=f"spider_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("La última ejecución de scraping no devolvió ningún lead.")
    
    st.markdown("---")
    st.subheader("Archivos CSV Crudos Generados Previamente")
    
    try:
        raw_files = sorted([f for f in os.listdir(RAW_DATA_DIR) if f.endswith(".csv")], reverse=True)
        if not raw_files:
            st.info("No hay archivos CSV crudos en la carpeta 'data/raw/'.")
        else:
            selected_file = st.selectbox("Seleccionar archivo para previsualizar:", raw_files)
            if selected_file:
                file_path = os.path.join(RAW_DATA_DIR, selected_file)
                try:
                    df_preview = pd.read_csv(file_path)
                    st.info(f"Archivo: {selected_file} | Filas: {len(df_preview)}")
                    st.dataframe(df_preview.head(100)) # Mostrar primeras 100 filas
                    
                    with open(file_path, "rb") as fp:
                        st.download_button(label=f"📥 Descargar {selected_file}", data=fp, file_name=selected_file, mime="text/csv")
                except Exception as e:
                    st.error(f"Error al cargar '{selected_file}': {e}")
    except FileNotFoundError:
        st.warning(f"El directorio '{RAW_DATA_DIR}' no fue encontrado.")

with tab_logs:
    st.header("Registros de Ejecución")
    
    log_file_to_show = os.path.join(LOGS_DIR, 'spider_core.log') # Mostrar el log del core logic
    st.info(f"Mostrando últimas 500 líneas de: {log_file_to_show}")
    
    if os.path.exists(log_file_to_show):
        try:
            with open(log_file_to_show, "r", encoding='utf-8', errors='ignore') as f:
                log_content = "".join(f.readlines()[-500:]) # Leer últimas 500 líneas
            st.code(log_content, language='log')
        except Exception as e:
            st.error(f"Error al leer el archivo de log: {e}")
    else:
        st.info("El archivo de log principal ('spider_core.log') no se ha creado aún.")