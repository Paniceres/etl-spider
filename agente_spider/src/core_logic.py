# 0_AGENTE_SPIDER/src/core_logic.py

import pandas as pd
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote, urljoin

from spider_rs import Website

# --- Configuración de Logging ---
# (Asumimos que el script que llama a este módulo creará estos directorios)
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(os.path.join(LOG_DIR, 'spider_core.log'), maxBytes=1024*1024, backupCount=5),
        logging.StreamHandler() # Añadido para ver logs en la consola
    ]
)
logger = logging.getLogger(__name__)

# --- CLASE 1: Suscripción para la Página de BÚSQUEDA ---
# Objetivo: Encontrar los links a las páginas de detalle de cada negocio.
class SearchPageSubscription:
    def __init__(self, detail_urls_list: list):
        self.detail_urls_list = detail_urls_list
        logger.info("SearchPageSubscription creada para recolectar URLs de detalle.")

    async def __call__(self, page):
        if page.status_code != 200:
            logger.warning(f"Página de búsqueda {page.url} devolvió status {page.status_code}.")
            return

        try:
            soup = BeautifulSoup(page.text, 'html.parser')
            # Selector para los links de los resultados. Google Maps usa <a> con href que contiene /maps/place/
            # El selector puede variar. Este es un ejemplo común.
            link_elements = soup.select('a[href*="/maps/place/"]') 
            
            found_count = 0
            for link_element in link_elements:
                relative_url = link_element.get('href')
                if relative_url:
                    # Construir la URL absoluta
                    absolute_url = urljoin("https://www.google.com", relative_url)
                    if absolute_url not in self.detail_urls_list:
                        self.detail_urls_list.append(absolute_url)
                        found_count += 1
            
            logger.info(f"Encontradas {found_count} nuevas URLs de detalle en {page.url}")

        except Exception as e:
            logger.error(f"Error parseando la página de búsqueda {page.url}: {e}", exc_info=True)


# --- CLASE 2: Suscripción para la Página de DETALLE ---
# Objetivo: Extraer los datos finales (nombre, dirección, etc.) de una página de negocio.
class DetailPageSubscription:
    def __init__(self, collected_items_list: list):
        self.collected_items = collected_items_list
        # Los selectores CSS son ahora fijos porque solo scrapeamos páginas de detalle
        self.parsing_rules = {
            "nombre_negocio": "h1.DUwDvf.lfPIob",
            "direccion": "button[data-item-id='address'] div.Io6YTe", # Selector más específico para el botón de dirección
            "telefono": "button[data-item-id^='phone:tel:'] div.Io6YTe", # Selector para el botón de teléfono
            "sitio_web": "a[data-item-id='authority'] div.Io6YTe", # Selector para el botón de sitio web
            "categoria": "button[jsaction*='category']", # Selector para el botón de categoría
            # Podemos añadir más reglas aquí...
        }
        logger.info("DetailPageSubscription creada para extraer datos de negocios.")

    async def __call__(self, page):
        if page.status_code != 200:
            logger.warning(f"Página de detalle {page.url} devolvió status {page.status_code}.")
            return

        try:
            soup = BeautifulSoup(page.text, 'html.parser')
            extracted_data = {}
            
            for key, selector in self.parsing_rules.items():
                element = soup.select_one(selector)
                if element:
                    extracted_data[key] = element.get_text(strip=True)
                else:
                    extracted_data[key] = None
            
            # Añadir la URL de la cual se extrajeron los datos
            extracted_data['url_gmaps'] = page.url

            if extracted_data.get("nombre_negocio"):
                self.collected_items.append(extracted_data)
                logger.success(f"Item recolectado: '{extracted_data['nombre_negocio']}' desde {page.url}")
            else:
                logger.warning(f"No se extrajo nombre de negocio de {page.url}")

        except Exception as e:
            logger.error(f"Error parseando la página de detalle {page.url}: {e}", exc_info=True)

# --- Funciones de Ayuda ---
def generate_search_urls(cities: list, keywords_by_city: dict) -> list[str]:
    """Genera las URLs de BÚSQUEDA iniciales."""
    urls = []
    base_url = "https://www.google.com/maps/search/"
    for city in cities:
        for keyword in keywords_by_city.get(city, []):
            query = f"{keyword} en {city}"
            encoded_query = "+".join(query.split())
            urls.append(f"{base_url}{encoded_query}")
    logger.info(f"Generadas {len(urls)} URLs de búsqueda iniciales.")
    return urls

# --- Función Principal Asíncrona `run_spider` ---
async def run_spider(config: dict) -> pd.DataFrame:
    """
    Orquesta el proceso de scraping en dos fases:
    1. Scrapea las páginas de búsqueda para obtener links a los detalles.
    2. Scrapea las páginas de detalle para extraer los datos finales.
    """
    logger.info(f"Iniciando run_spider con config: {config}")

    # --- FASE 1: OBTENER URLs DE DETALLE ---
    logger.section("FASE 1: Recolectando URLs de Negocios")
    search_urls = generate_search_urls(config.get('cities', []), config.get('keywords', {}))
    if not search_urls:
        logger.warning("No se generaron URLs de búsqueda. Finalizando.")
        return pd.DataFrame()

    detail_urls_to_scrape = []
    search_subscription = SearchPageSubscription(detail_urls_to_scrape)
    
    # Crear tareas para la Fase 1
    search_tasks = []
    for url in search_urls:
        website_instance = Website(url, False) # No seguir links externos en la búsqueda
        # Configuración para que el spider sea más "profundo" en la página de búsqueda si es necesario
        # Esto depende de las capacidades de spider-rs, como manejar scrolls o clicks
        # website_instance.set_depth(config.get('depth', 1)) # Ejemplo conceptual
        search_tasks.append(website_instance.crawl(search_subscription))
    
    logger.info(f"Ejecutando {len(search_tasks)} tareas de búsqueda...")
    await asyncio.gather(*search_tasks)
    logger.success(f"Fase 1 completada. Total de URLs de detalle únicas encontradas: {len(detail_urls_to_scrape)}")

    if not detail_urls_to_scrape:
        logger.warning("No se encontraron URLs de detalle. No se puede proceder a la Fase 2.")
        return pd.DataFrame()

    # --- FASE 2: SCRAPEAR DATOS DE LAS URLs DE DETALLE ---
    logger.section("FASE 2: Extrayendo Datos de los Negocios")
    
    final_collected_items = []
    detail_subscription = DetailPageSubscription(final_collected_items)

    # Crear tareas para la Fase 2
    detail_tasks = []
    for url in detail_urls_to_scrape:
        # Aquí podrías querer habilitar la extracción de emails, lo que implicaría que
        # spider-rs siga el link del sitio web del negocio. Esto es más avanzado.
        # Por ahora, nos enfocamos en los datos de la página de Gmaps.
        website_instance = Website(url, False) # No seguir links a sitios web externos por ahora
        detail_tasks.append(website_instance.crawl(detail_subscription))

    logger.info(f"Ejecutando {len(detail_tasks)} tareas de extracción de detalles...")
    await asyncio.gather(*detail_tasks)
    logger.success(f"Fase 2 completada. Total de items finales recolectados: {len(final_collected_items)}")

    # Convertir a DataFrame y guardar
    df_results = pd.DataFrame(final_collected_items)
    
    if not df_results.empty:
        RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"spider_leads_{timestamp}.csv"
        file_path = os.path.join(RAW_DATA_DIR, filename)
        try:
            df_results.to_csv(file_path, index=False, encoding='utf-8-sig') # utf-8-sig para Excel
            logger.info(f"Resultados guardados en: {file_path}")
        except Exception as e:
            logger.error(f"Error al guardar el archivo CSV final: {e}", exc_info=True)
    else:
        logger.info("No se recolectaron datos finales. No se guardó ningún archivo.")

    return df_results