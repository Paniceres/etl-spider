# 0_AGENTE_SPIDER/src/core_logic.py

import pandas as pd
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from spider_rs import Website

# --- Clase StyledLogger (sin cambios) ---
class StyledLogger:
    def __init__(self, logger_name='CoreLogicLogger', log_file_path='spider_core.log', level=logging.INFO):
        self.logger = logging.getLogger(logger_name)
        if not self.logger.handlers: 
            self.logger.setLevel(level)
            self.logger.propagate = False 
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            try:
                log_dir = os.path.dirname(log_file_path)
                if log_dir: os.makedirs(log_dir, exist_ok=True)
                fh = RotatingFileHandler(log_file_path, maxBytes=1024*1024, backupCount=3, encoding='utf-8')
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)
            except Exception as e:
                print(f"ERROR CRITICO (StyledLogger): No se pudo crear FileHandler para '{log_file_path}'. Error: {e}")
        self.SECTION_SEPARATOR = "=" * 70; self.SUB_SECTION_SEPARATOR = "-" * 50; self.SUCCESS_ART = "[OK]"; self.ERROR_ART = "[FAIL]"; self.WARNING_ART = "[WARN]"; self.INFO_ART = "[INFO]"
    def _log(self, level, message, art=""): self.logger.log(level, f"{art} {message}".strip())
    def section(self, title): self._log(logging.INFO, f"\n{self.SECTION_SEPARATOR}\n{str(title).upper()}\n{self.SECTION_SEPARATOR}", art="")
    def subsection(self, title): self._log(logging.INFO, f"\n{self.SUB_SECTION_SEPARATOR}\n{str(title)}\n{self.SUB_SECTION_SEPARATOR}", art="")
    def info(self, message): self._log(logging.INFO, message, self.INFO_ART)
    def success(self, message): self._log(logging.INFO, message, self.SUCCESS_ART)
    def warning(self, message): self._log(logging.WARNING, message, self.WARNING_ART)
    def error(self, message, exc_info=False):
        self._log(logging.ERROR, message, self.ERROR_ART)
        if exc_info: self.logger.exception("Detalles de la excepción:")

# --- Clases de Suscripción (Ahora son síncronas) ---
class SearchPageSubscription:
    def __init__(self, detail_urls_list: list, logger_instance: StyledLogger):
        self.detail_urls_list = detail_urls_list
        self.logger = logger_instance
        self.logger.info("SearchPageSubscription creada.")
    
    def __call__(self, page): # quitamos 'async'
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
            if found_count > 0: self.logger.info(f"Encontradas {found_count} nuevas URLs de detalle en {page.url}")
        except Exception as e:
            self.logger.error(f"Error parseando página de búsqueda {page.url}: {e}", exc_info=True)

class DetailPageSubscription:
    def __init__(self, collected_items_list: list, logger_instance: StyledLogger):
        self.collected_items = collected_items_list
        self.logger = logger_instance
        self.parsing_rules = {"nombre_negocio": "h1", "direccion": "button[data-item-id='address'] div.Io6YTe", "telefono": "button[data-item-id^='phone:tel:'] div.Io6YTe", "sitio_web": "a[data-item-id='authority'] div.Io6YTe", "categoria": "button[jsaction*='category']"}
        self.logger.info("DetailPageSubscription creada.")

    def __call__(self, page): # quitamos 'async'
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
        except Exception as e:
            self.logger.error(f"Error parseando página de detalle {page.url}: {e}", exc_info=True)

# --- Funciones de Ayuda (sin cambios) ---
def generate_search_urls(cities: list, keywords_by_city: dict, logger_instance: StyledLogger) -> list[str]:
    urls = []
    base_url = "https://www.google.com/maps/search/"
    for city in cities:
        for keyword in keywords_by_city.get(city, []):
            query = f"{keyword} en {city}"
            encoded_query = "+".join(query.split())
            urls.append(f"{base_url}{encoded_query}")
    logger_instance.info(f"Generadas {len(urls)} URLs de búsqueda.")
    return urls

# --- Función Principal SÍNCRONA `run_spider` (MODIFICADA) ---
def run_spider(config: dict, logger_instance: StyledLogger) -> pd.DataFrame:
    logger_instance.info(f"Iniciando run_spider con config: {config}")
    
    # FASE 1: OBTENER URLs DE DETALLE
    logger_instance.section("FASE 1: Recolectando URLs de Negocios")
    search_urls = generate_search_urls(config.get('cities', []), config.get('keywords', {}), logger_instance)
    if not search_urls:
        logger_instance.warning("No se generaron URLs de búsqueda.")
        return pd.DataFrame()

    detail_urls_to_scrape = []
    search_subscription = SearchPageSubscription(detail_urls_to_scrape, logger_instance)
    
    # Crear una instancia de Website para TODAS las URLs de búsqueda
    website_search = Website(search_urls, False) # Pasar la lista completa
    # Configurar el scraper
    website_search.set_depth(config.get('depth', 1)) # Usar la profundidad de la config
    logger_instance.info(f"Ejecutando crawl en {len(search_urls)} URLs de búsqueda...")
    website_search.crawl(search_subscription) # Esta llamada es bloqueante y maneja la concurrencia internamente
    
    logger_instance.success(f"Fase 1 completada. URLs de detalle encontradas: {len(detail_urls_to_scrape)}")

    if not detail_urls_to_scrape:
        return pd.DataFrame()

    # FASE 2: SCRAPEAR DATOS DE LAS URLs DE DETALLE
    logger_instance.section("FASE 2: Extrayendo Datos de los Negocios")
    final_collected_items = []
    detail_subscription = DetailPageSubscription(final_collected_items, logger_instance)
    
    # Limitar para pruebas si es necesario
    detail_urls_to_scrape_subset = detail_urls_to_scrape[:50]
    logger_instance.info(f"Procesando las primeras {len(detail_urls_to_scrape_subset)} URLs de detalle.")
    
    website_detail = Website(detail_urls_to_scrape_subset, False)
    logger_instance.info(f"Ejecutando crawl en {len(detail_urls_to_scrape_subset)} URLs de detalle...")
    website_detail.crawl(detail_subscription)
    
    logger_instance.success(f"Fase 2 completada. Items finales recolectados: {len(final_collected_items)}")

    df_results = pd.DataFrame(final_collected_items)
    
    if not df_results.empty:
        logger_instance.info(f"Proceso de scraping finalizado. Se devuelven {len(df_results)} registros.")
    else:
        logger_instance.info("No se recolectaron datos finales.")

    return df_results