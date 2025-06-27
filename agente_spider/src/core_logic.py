# 0_AGENTE_SPIDER/src/core_logic.py

import pandas as pd
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Se asume que 'spider-rs' ya está instalado correctamente
from spider_rs import Website

# --- NO CREAR UN LOGGER GLOBAL AQUÍ ---
# La instancia del logger se pasará como argumento a las funciones.

# --- CLASE DE LOGGER ESTILIZADO ---
# Esta clase se importará y se instanciará en app_streamlit.py
class StyledLogger:
    def __init__(self, logger_name='CoreLogic', log_file_path='spider_core.log', level=logging.INFO):
        self.logger = logging.getLogger(logger_name)
        
        # Evitar añadir handlers si ya existen (importante para Streamlit)
        if not self.logger.handlers: 
            self.logger.setLevel(level)
            self.logger.propagate = False 

            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

            try:
                log_dir = os.path.dirname(log_file_path)
                if log_dir: os.makedirs(log_dir, exist_ok=True)
                
                # Usar RotatingFileHandler para evitar que los logs crezcan indefinidamente
                fh = RotatingFileHandler(log_file_path, maxBytes=1024*1024, backupCount=3, encoding='utf-8')
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)
            except Exception as e:
                print(f"ERROR CRITICO (StyledLogger): No se pudo crear FileHandler para '{log_file_path}'. Error: {e}")
        
        # Estilos para los logs
        self.SECTION_SEPARATOR = "=" * 70
        self.SUB_SECTION_SEPARATOR = "-" * 50
        self.SUCCESS_ART = "[OK]"
        self.ERROR_ART = "[FAIL]"
        self.WARNING_ART = "[WARN]"
        self.INFO_ART = "[INFO]"

    def _log(self, level, message, art=""):
        self.logger.log(level, f"{art} {message}".strip())

    def section(self, title): self._log(logging.INFO, f"\n{self.SECTION_SEPARATOR}\n{str(title).upper()}\n{self.SECTION_SEPARATOR}", art="")
    def subsection(self, title): self._log(logging.INFO, f"\n{self.SUB_SECTION_SEPARATOR}\n{str(title)}\n{self.SUB_SECTION_SEPARATOR}", art="")
    def info(self, message): self._log(logging.INFO, message, self.INFO_ART)
    def success(self, message): self._log(logging.INFO, message, self.SUCCESS_ART)
    def warning(self, message): self._log(logging.WARNING, message, self.WARNING_ART)
    def error(self, message, exc_info=False):
        self._log(logging.ERROR, message, self.ERROR_ART)
        if exc_info: self.logger.exception("Detalles de la excepción:")


# --- CLASE 1: Suscripción para la Página de BÚSQUEDA ---
class SearchPageSubscription:
    def __init__(self, detail_urls_list: list, logger_instance: StyledLogger):
        self.detail_urls_list = detail_urls_list
        self.logger = logger_instance
        self.logger.info("SearchPageSubscription creada.")

    async def __call__(self, page):
        if page.status_code != 200:
            self.logger.warning(f"Página de búsqueda {page.url} devolvió status {page.status_code}.")
            return

        try:
            soup = BeautifulSoup(page.text, 'html.parser')
            link_elements = soup.select('a[href*="/maps/place/"]') 
            
            found_count = 0
            for link_element in link_elements:
                relative_url = link_element.get('href')
                if relative_url:
                    absolute_url = urljoin("https://www.google.com", relative_url)
                    if absolute_url not in self.detail_urls_list:
                        self.detail_urls_list.append(absolute_url)
                        found_count += 1
            
            if found_count > 0:
                self.logger.info(f"Encontradas {found_count} nuevas URLs de detalle en {page.url}")

        except Exception as e:
            self.logger.error(f"Error parseando la página de búsqueda {page.url}: {e}", exc_info=True)


# --- CLASE 2: Suscripción para la Página de DETALLE ---
class DetailPageSubscription:
    def __init__(self, collected_items_list: list, logger_instance: StyledLogger):
        self.collected_items = collected_items_list
        self.logger = logger_instance
        self.parsing_rules = {
            "nombre_negocio": "h1", # El h1 principal suele ser el nombre
            "direccion": "button[data-item-id='address'] div.Io6YTe",
            "telefono": "button[data-item-id^='phone:tel:'] div.Io6YTe",
            "sitio_web": "a[data-item-id='authority'] div.Io6YTe",
            "categoria": "button[jsaction*='category']",
        }
        self.logger.info("DetailPageSubscription creada.")

    async def __call__(self, page):
        if page.status_code != 200:
            self.logger.warning(f"Página de detalle {page.url} devolvió status {page.status_code}.")
            return
        try:
            soup = BeautifulSoup(page.text, 'html.parser')
            extracted_data = {}
            
            for key, selector in self.parsing_rules.items():
                element = soup.select_one(selector)
                extracted_data[key] = element.get_text(strip=True) if element else None
            
            extracted_data['url_gmaps'] = page.url

            if extracted_data.get("nombre_negocio"):
                self.collected_items.append(extracted_data)
                self.logger.success(f"Item recolectado: '{extracted_data['nombre_negocio']}'")
            else:
                self.logger.warning(f"No se extrajo nombre de negocio de {page.url}")

        except Exception as e:
            self.logger.error(f"Error parseando la página de detalle {page.url}: {e}", exc_info=True)

# --- Funciones de Ayuda ---
def generate_search_urls(cities: list, keywords_by_city: dict, logger_instance: StyledLogger) -> list[str]:
    """Genera las URLs de BÚSQUEDA iniciales."""
    urls = []
    base_url = "https://www.google.com/maps/search/"
    for city in cities:
        for keyword in keywords_by_city.get(city, []):
            query = f"{keyword} en {city}"
            encoded_query = "+".join(query.split())
            urls.append(f"{base_url}{encoded_query}")
    logger_instance.info(f"Generadas {len(urls)} URLs de búsqueda iniciales.")
    return urls

# --- Función Principal Asíncrona `run_spider` ---
async def run_spider(config: dict, logger_instance: StyledLogger) -> pd.DataFrame:
    """
    Orquesta el proceso de scraping en dos fases. Acepta una instancia de logger.
    """
    logger_instance.info(f"Iniciando run_spider con config: {config}")
    
    # FASE 1: OBTENER URLs DE DETALLE
    logger_instance.section("FASE 1: Recolectando URLs de Negocios")
    search_urls = generate_search_urls(config.get('cities', []), config.get('keywords', {}), logger_instance)
    if not search_urls:
        logger_instance.warning("No se generaron URLs de búsqueda. Finalizando.")
        return pd.DataFrame()

    detail_urls_to_scrape = []
    search_subscription = SearchPageSubscription(detail_urls_to_scrape, logger_instance)
    
    search_tasks = [Website(url, False).crawl(search_subscription) for url in search_urls]
    
    logger_instance.info(f"Ejecutando {len(search_tasks)} tareas de búsqueda...")
    await asyncio.gather(*search_tasks)
    logger_instance.success(f"Fase 1 completada. URLs de detalle únicas encontradas: {len(detail_urls_to_scrape)}")

    if not detail_urls_to_scrape:
        logger_instance.warning("No se encontraron URLs de detalle. No se puede proceder a la Fase 2.")
        return pd.DataFrame()

    # FASE 2: SCRAPEAR DATOS DE LAS URLs DE DETALLE
    logger_instance.section("FASE 2: Extrayendo Datos de los Negocios")
    final_collected_items = []
    detail_subscription = DetailPageSubscription(final_collected_items, logger_instance)

    # Limitar el número de URLs a scrapear en la fase de detalle para pruebas rápidas
    # Puedes comentar esta línea para procesar todo
    detail_urls_to_scrape = detail_urls_to_scrape[:50] 
    logger_instance.info(f"Procesando las primeras {len(detail_urls_to_scrape)} URLs de detalle.")
    
    detail_tasks = [Website(url, False).crawl(detail_subscription) for url in detail_urls_to_scrape]

    logger_instance.info(f"Ejecutando {len(detail_tasks)} tareas de extracción de detalles...")
    await asyncio.gather(*detail_tasks)
    logger_instance.success(f"Fase 2 completada. Items finales recolectados: {len(final_collected_items)}")

    df_results = pd.DataFrame(final_collected_items)
    
    # La responsabilidad de guardar el archivo ahora recae en quien llama a esta función (app_streamlit.py),
    # pero mantenemos un log para indicar que la data está lista.
    if not df_results.empty:
        logger_instance.info(f"Proceso de scraping finalizado. Se devuelven {len(df_results)} registros.")
    else:
        logger_instance.info("No se recolectaron datos finales.")

    return df_results