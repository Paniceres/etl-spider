import streamlit as st
import pandas as pd
import json
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime

# --- PASO 1: Asegurar que core_logic.py sea importable ---
try:
    APP_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    APP_ROOT_DIR = os.getcwd()

SRC_DIR = os.path.join(APP_ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

# --- Importar Lógica Core con Fallback a Dummies ---
CORE_LOGIC_LOADED = False
try:
    from core_logic import run_spider, StyledLogger
    CORE_LOGIC_LOADED = True
    print("INFO (streamlit): core_logic.py cargado exitosamente.")
except ImportError as e:
    print(f"ERROR (streamlit): No se pudo importar de 'src/core_logic.py': {e}")
    # Definir dummies para que la app no se rompa
    def run_spider(config, logger_instance):
        logger_instance.error("Ejecutando en modo simulación (core_logic.py no cargado).")
        time.sleep(2)
        return pd.DataFrame([{'nombre_negocio': 'Error al cargar core_logic.py'}])
    
    class StyledLogger:
        def __init__(self, *args, **kwargs): pass
        def info(self, msg): print(f"DUMMY_INFO: {msg}")
        def error(self, msg, exc_info=False): print(f"DUMMY_ERROR: {msg}")
        def warning(self, msg): print(f"DUMMY_WARN: {msg}")
        def success(self, msg): print(f"DUMMY_SUCCESS: {msg}")
        def section(self, title): print(f"DUMMY_SECTION: {str(title).upper()}")

# --- Configuración de Rutas y Logging ---
CONFIG_DIR = os.path.join(APP_ROOT_DIR, 'config')
DATA_DIR = os.path.join(APP_ROOT_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

ui_log_file = os.path.join(LOGS_DIR, "streamlit_ui.log")
ui_logger = StyledLogger(logger_name="StreamlitUI", log_file_path=ui_log_file, level=logging.INFO)

# --- Funciones de Ayuda ---
@st.cache_data
def load_cities_from_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.sidebar.warning(f"No se pudo cargar: '{os.path.basename(file_path)}'")
        ui_logger.error(f"Error cargando {file_path}: {e}")
        return {}

@st.cache_data
def load_keywords_from_csv(city_name):
    keywords_file = os.path.join(CONFIG_DIR, f"keywords_{city_name.lower()}.csv")
    if os.path.exists(keywords_file):
        try:
            with open(keywords_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            st.error(f"Error al leer keywords para {city_name}: {e}")
            return ""
    return ""

def save_keywords_to_csv(city_name, keywords_str):
    keywords_file = os.path.join(CONFIG_DIR, f"keywords_{city_name.lower()}.csv")
    try:
        with open(keywords_file, "w", encoding='utf-8') as f:
            f.write(keywords_str)
        load_keywords_from_csv.clear()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al guardar keywords para {city_name}: {e}")
        return False

# --- UI Principal ---
st.set_page_config(page_title="Agente Spider", layout="wide")

st.title("🚀✨ Agente Spider - Generador de CSVs Crudos")
st.markdown("Configura y ejecuta tareas de scraping para generar leads desde Google Maps.")

if not CORE_LOGIC_LOADED:
    st.error("¡ADVERTENCIA CRÍTICA! El módulo 'core_logic.py' no pudo cargar. Solo funcionará en modo simulación.")

# --- Inicializar Session State ---
if 'scraping_results' not in st.session_state:
    st.session_state.scraping_results = None

# --- Sidebar ---
with st.sidebar:
    st.header("🕷️ Configuración de Scraping")
    
    cities_file_path = os.path.join(CONFIG_DIR, "cities.json")
    all_cities_data = load_cities_from_json(cities_file_path)
    city_options = list(all_cities_data.keys())
    
    selected_cities = st.multiselect("Seleccionar Ciudad(es) a Procesar", options=city_options)

    keywords_config = {}
    if selected_cities:
        with st.expander("Configurar Keywords", expanded=True):
            for city in selected_cities:
                keywords_config[city] = st.text_area(
                    f"Keywords para {city}", value=load_keywords_from_csv(city),
                    height=100, key=f"keywords_{city}"
                )
                if st.button(f"Guardar para {city}", key=f"save_{city}"):
                    if save_keywords_to_csv(city, keywords_config[city]):
                        st.success(f"Keywords guardadas para {city}.")
                        st.rerun()

    depth = st.slider("Profundidad (conceptual)", 1, 10, 1)
    extract_emails = st.checkbox("¿Extraer Emails?", value=True, help="Activa la búsqueda de emails en los sitios web de los negocios (puede tardar más).")

    # Botón de inicio se deshabilita si ya está en progreso
    if st.button("🚀 Iniciar Scraping", type="primary", use_container_width=True, disabled=st.session_state.get('scraping_in_progress', False)):
        if not selected_cities:
            st.warning("Por favor, selecciona al menos una ciudad.")
        elif not CORE_LOGIC_LOADED:
            st.error("La lógica de scraping real no está disponible.")
        else:
            # Construir la configuración en el momento del click
            final_config = {
                "cities": selected_cities,
                "keywords": {},
                "depth": depth,
                "extract_emails": extract_emails
            }
            for city in selected_cities:
                final_config["keywords"][city] = [line.strip() for line in keywords_config[city].splitlines() if line.strip()]
            
            ui_logger.info(f"Iniciando scraping con config: {final_config}")
            st.session_state.scraping_in_progress = True
            
            # Usamos st.spinner para el feedback visual
            with st.spinner("Scraping en progreso... Esto puede tardar varios minutos. Por favor, espera."):
                try:
                    # Crear la instancia del logger para PASARLA a la función de core_logic
                    core_log_path = os.path.join(LOGS_DIR, 'spider_core.log')
                    core_logger_for_run = StyledLogger(logger_name=f"CoreRun-{datetime.now().strftime('%H%M%S')}", log_file_path=core_log_path)
                    
                    # LLAMADA SÍNCRONA DIRECTA. Streamlit esperará aquí y mostrará el spinner.
                    results_df = run_spider(final_config, core_logger_for_run)
                    
                    st.session_state.last_scraping_results = results_df 
                    st.success("¡Scraping completado!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Ocurrió un error crítico durante el scraping: {e}")
                    ui_logger.error(f"Error crítico en run_spider: {e}", exc_info=True)
                    st.session_state.last_scraping_results = None
                finally:
                    # Al salir del 'with', el spinner desaparece y liberamos el estado
                    st.session_state.scraping_in_progress = False
            
            # Forzar un rerun final para asegurar que la UI se actualice con los resultados
            st.rerun()


# --- Área Principal ---
tab_resultados, tab_logs = st.tabs(["📊 Resultados", "📜 Logs"])

with tab_resultados:
    st.header("Resultados del Scraping")
    if st.session_state.scraping_in_progress:
        st.info("El scraping está en progreso. Los resultados se mostrarán aquí al finalizar.")
    
    if st.session_state.last_scraping_results is not None:
        st.subheader("Resultados de la Última Ejecución")
        if not st.session_state.last_scraping_results.empty:
            df_display = st.session_state.last_scraping_results
            st.dataframe(df_display)
            csv = df_display.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                "📥 Descargar CSV de Última Ejecución",
                data=csv,
                file_name=f"spider_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("La última ejecución de scraping no devolvió ningún lead.")
    
    st.markdown("---")
    st.subheader("Historial de Archivos CSV Crudos Generados")
    try:
        if os.path.exists(RAW_DATA_DIR):
            raw_files = sorted([f for f in os.listdir(RAW_DATA_DIR) if f.endswith(".csv")], reverse=True)
            if not raw_files:
                st.info("No hay archivos CSV crudos en la carpeta 'data/raw/'.")
            else:
                selected_file = st.selectbox("Seleccionar archivo para previsualizar:", raw_files, key="sb_raw_files")
                if selected_file:
                    file_path = os.path.join(RAW_DATA_DIR, selected_file)
                    try:
                        df_preview = pd.read_csv(file_path)
                        st.info(f"Archivo: {selected_file} | Filas: {len(df_preview)}")
                        st.dataframe(df_preview.head(100))
                        with open(file_path, "rb") as fp:
                            st.download_button(label=f"📥 Descargar {selected_file}", data=fp, file_name=selected_file, mime="text/csv", key=f"dl_{selected_file}")
                    except Exception as e:
                        st.error(f"Error al cargar '{selected_file}': {e}")
        else:
             st.warning(f"El directorio '{RAW_DATA_DIR}' no fue encontrado.")
    except Exception as e_list_dir:
        st.error(f"Error al listar archivos en '{RAW_DATA_DIR}': {e_list_dir}")

with tab_logs:
    st.header("Registros de Ejecución")
    log_file_core = os.path.join(LOGS_DIR, 'spider_core.log')
    st.subheader(f"Log del Core Logic (`{os.path.basename(log_file_core)}`)")
    if st.button("Recargar Logs"):
        st.rerun()
        
    if os.path.exists(log_file_core):
        try:
            with open(log_file_core, "r", encoding='utf-8', errors='ignore') as f:
                log_content = "".join(f.readlines()[-500:])
            st.code(log_content, language='log')
        except Exception as e:
            st.error(f"Error al leer el archivo de log: {e}")
    else:
        st.info("El archivo de log principal no se ha creado aún.")