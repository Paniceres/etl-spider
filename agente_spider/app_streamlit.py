import streamlit as st
import pandas as pd
import json
import asyncio
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime

# --- PASO 1: Asegurar que core_logic.py sea importable ---
# Esta sección busca la carpeta 'src' y la añade al path de Python
try:
    APP_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Fallback si __file__ no está definido (p. ej., en algunos notebooks interactivos)
    APP_ROOT_DIR = os.getcwd()

SRC_DIR = os.path.join(APP_ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

# --- Importar Lógica Core con Fallback a Dummies ---
CORE_LOGIC_LOADED = False
try:
    # Importar tanto la función como la clase logger para poder instanciarla
    from core_logic import run_spider, StyledLogger
    CORE_LOGIC_LOADED = True
    print("INFO (streamlit): core_logic.py cargado exitosamente.")
except ImportError as e:
    print(f"ERROR (streamlit): No se pudo importar de 'src/core_logic.py': {e}")
    # Definir una función y clase dummy para que la app no se rompa si core_logic falla
    def run_spider(config, logger_instance): # Debe aceptar logger_instance
        logger_instance.error("Ejecutando en modo simulación (core_logic.py no cargado).")
        time.sleep(2) # Simular trabajo
        return pd.DataFrame([{'nombre_negocio': 'Error al cargar core_logic.py', 'url_gmaps': 'simulacion'}])
    
    class StyledLogger: # Dummy Logger
        def __init__(self, *args, **kwargs): pass
        def info(self, msg): print(f"DUMMY_INFO: {msg}")
        def error(self, msg, exc_info=False): print(f"DUMMY_ERROR: {msg}")
        def warning(self, msg): print(f"DUMMY_WARN: {msg}")
        def success(self, msg): print(f"DUMMY_SUCCESS: {msg}")
        def section(self, title): print(f"DUMMY_SECTION: {str(title).upper()}")
        def subsection(self, title): print(f"DUMMY_SUBSECTION: {str(title)}")

# --- Configuración de Rutas y Logging ---
CONFIG_DIR = os.path.join(APP_ROOT_DIR, 'config')
DATA_DIR = os.path.join(APP_ROOT_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Crear una única instancia de logger para toda la app de UI
# Esta instancia se creará con la clase real (StyledLogger) o la dummy si la importación falló
ui_log_file = os.path.join(LOGS_DIR, "streamlit_ui.log")
ui_logger = StyledLogger(logger_name="StreamlitUI", log_file_path=ui_log_file, level=logging.INFO)

# --- Funciones de Ayuda ---
@st.cache_data # Cachear para no recargar en cada rerun de la UI
def load_cities_from_json(file_path):
    """Carga los datos de ciudades desde un archivo JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Usar st.warning en la sidebar porque es donde se llama
        st.sidebar.warning(f"No se pudo cargar: '{os.path.basename(file_path)}'")
        ui_logger.error(f"Error cargando {file_path}: {e}")
        return {}

@st.cache_data # Cachear también las keywords
def load_keywords_from_csv(city_name):
    """Carga las keywords para una ciudad desde su archivo CSV."""
    keywords_file = os.path.join(CONFIG_DIR, f"keywords_{city_name.lower()}.csv")
    if os.path.exists(keywords_file):
        try:
            with open(keywords_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            st.error(f"Error al leer keywords para {city_name}: {e}")
            return ""
    return "" # Devuelve string vacío si no existe el archivo

def save_keywords_to_csv(city_name, keywords_str):
    """Guarda las keywords editadas al archivo CSV correspondiente."""
    keywords_file = os.path.join(CONFIG_DIR, f"keywords_{city_name.lower()}.csv")
    try:
        with open(keywords_file, "w", encoding='utf-8') as f:
            f.write(keywords_str)
        # Limpiar el caché para esta función y para la de carga
        load_keywords_from_csv.clear()
        st.cache_data.clear() # Limpiar todo el caché de st como medida simple
        return True
    except Exception as e:
        st.error(f"Error al guardar keywords para {city_name}: {e}")
        return False

def run_async_in_sync(async_func, *args, **kwargs):
    """Crea un nuevo bucle de eventos para ejecutar una función async desde un contexto síncrono."""
    # Esta es la forma recomendada para integrar asyncio con frameworks síncronos como Streamlit
    # Comprobar si ya existe un bucle de eventos corriendo (relevante para algunos entornos)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # 'There is no current event loop...'
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Ejecutar la corutina en el bucle
    return loop.run_until_complete(async_func(*args, **kwargs))

# --- UI Principal ---
st.set_page_config(page_title="Agente Spider", layout="wide")

st.title("🚀✨ Agente Spider - Generador de CSVs Crudos")
st.markdown("Configura y ejecuta tareas de scraping para generar leads desde Google Maps.")

if not CORE_LOGIC_LOADED:
    st.error("¡ADVERTENCIA CRÍTICA! El módulo 'core_logic.py' no pudo cargar. Solo funcionará en modo simulación.")

# --- Inicializar Session State ---
if 'last_scraping_results' not in st.session_state:
    st.session_state.last_scraping_results = None
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False

# --- Sidebar ---
with st.sidebar:
    st.header("🕷️ Configuración de Scraping")
    
    cities_file_path = os.path.join(CONFIG_DIR, "cities.json")
    all_cities_data = load_cities_from_json(cities_file_path)
    city_options = list(all_cities_data.keys())
    
    selected_cities = st.multiselect(
        "Seleccionar Ciudad(es) a Procesar", 
        options=city_options,
        disabled=st.session_state.scraping_in_progress
    )

    keywords_config = {}
    if selected_cities:
        with st.expander("Configurar Keywords", expanded=True):
            for city in selected_cities:
                keywords_config[city] = st.text_area(
                    f"Keywords para {city}",
                    value=load_keywords_from_csv(city),
                    height=100,
                    key=f"keywords_{city}", # Usar key simple
                    disabled=st.session_state.scraping_in_progress
                )
                if st.button(f"Guardar para {city}", key=f"save_{city}"):
                    if save_keywords_to_csv(city, keywords_config[city]):
                        st.success(f"Keywords guardadas para {city}.")
                        st.rerun() # Recargar para que se vea reflejado si hay cambios

    depth = st.slider("Profundidad (conceptual)", 1, 10, 1, disabled=st.session_state.scraping_in_progress)
    extract_emails = st.checkbox("¿Extraer Emails?", value=False, disabled=st.session_state.scraping_in_progress, help="Depende de la lógica en core_logic.")

    if st.button("🚀 Iniciar Scraping", type="primary", use_container_width=True, disabled=st.session_state.scraping_in_progress):
        if not selected_cities:
            st.warning("Por favor, selecciona al menos una ciudad.")
        elif not CORE_LOGIC_LOADED:
            st.error("La lógica de scraping real no está disponible.")
        else:
            # Aquí no se ejecuta la lógica, solo se pone el flag para hacerlo en el script principal
            st.session_state.scraping_in_progress = True
            # Guardar la configuración en session_state para que la use el bloque de ejecución
            st.session_state.config_for_run = {
                "cities": selected_cities,
                "keywords": keywords_config,
                "depth": depth,
                "extract_emails": extract_emails
            }
            st.rerun()

# --- Lógica de Ejecución y Área Principal ---
if st.session_state.scraping_in_progress:
    with st.spinner("Scraping en progreso... Esto puede tardar varios minutos."):
        results_df = None  # Inicializar variable
        try:
            # Recuperar la configuración guardada en session_state
            final_config = st.session_state.config_for_run
            
            # Poblar las keywords desde el diccionario de text_areas
            for city in final_config["cities"]:
                final_config["keywords"][city] = [line.strip() for line in keywords_config[city].splitlines() if line.strip()]

            # Crear una instancia del logger para PASARLA a la función de core_logic
            core_log_path = os.path.join(LOGS_DIR, 'spider_core.log')
            core_logger_for_run = StyledLogger(logger_name=f"CoreRun-{datetime.now().strftime('%H%M%S')}", log_file_path=core_log_path)
            
            ui_logger.info(f"Iniciando scraping con config: {final_config}")

            # Llamar al wrapper, pasándole la función, la config Y la instancia del logger
            # CAMBIO: La llamada a la lógica asíncrona se envuelve en la función síncrona
            # run_spider en core_logic ahora es SÍNCRONA, por lo que se llama directamente.
            results_df = run_spider(final_config, core_logger_for_run)
            
            st.session_state.last_scraping_results = results_df 
            st.success("¡Scraping completado!")
            st.balloons()
        except Exception as e:
            st.error(f"Ocurrió un error crítico durante el scraping: {e}")
            ui_logger.error(f"Error crítico en run_spider: {e}", exc_info=True)
            st.session_state.last_scraping_results = None
        finally:
            # Terminar el estado de progreso y re-renderizar para mostrar resultados
            st.session_state.scraping_in_progress = False
            # No es necesario st.rerun() aquí, Streamlit lo hará al salir del 'with'
    # Forzar un rerun final para limpiar el spinner y mostrar la sección de resultados
    st.rerun()

# Pestañas para mostrar resultados y logs
tab_resultados, tab_logs = st.tabs(["📊 Resultados", "📜 Logs"])

with tab_resultados:
    st.header("Resultados del Scraping")

    # Mostrar los últimos resultados del scraping si existen
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
        # Asegurarse de que el directorio RAW_DATA_DIR existe
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
    if os.path.exists(log_file_core):
        try:
            with open(log_file_core, "r", encoding='utf-8', errors='ignore') as f:
                log_content = "".join(f.readlines()[-500:])
            st.code(log_content, language='log')
        except Exception as e:
            st.error(f"Error al leer el archivo de log: {e}")
    else:
        st.info("El archivo de log principal no se ha creado aún.")