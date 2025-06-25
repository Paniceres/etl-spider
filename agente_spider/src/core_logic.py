import pandas as pd
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import asyncio # Necesario para trabajar con async/await y ejecución concurrente
import time # Puede ser útil para medir tiempos si se desea
from bs4 import BeautifulSoup # Mantenemos BeautifulSoup para parse_html
from urllib.parse import urlparse, unquote


# Importar la clase Website de la librería spider-rs
# La función crawl no se importa directamente, se usa el método .crawl() de la instancia de Website.
from spider_rs import Website
# Posiblemente necesites importar algo relacionado con la suscripción si no es solo una clase base implícita
# Si spider-rs tiene una clase base 'Subscription', la importaríamos así:
# from spider_rs import Subscription as SpiderRsSubscription # Ejemplo

# Asegurar que el directorio de logs existe
# Usamos una ruta absoluta o relativa desde donde se ejecutará el script.
# /workspace/ es común en algunos entornos de desarrollo en la nube,
# ajusta si tu entorno es diferente.
LOG_DIR = "/workspace/0_AGENTE_SPIDER/data/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configurar el logging para el spider
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # Formato del mensaje de log
    handlers=[
        RotatingFileHandler(os.path.join(LOG_DIR, 'spider.log'), maxBytes=1024*1024, backupCount=5)
     ]
)

logger = logging.getLogger(__name__)

# Clase de Suscripción para procesar cada página scrapeada por spider-rs
# Implementa el método asíncrono __call__(self, page).
# Si spider-rs tiene una clase base Subscription, heredaríamos de ella:
# class GoogleMapsSubscription(SpiderRsSubscription): # Ejemplo
class GoogleMapsSubscription: # Usamos una clase simple si no hay base explícita
    def __init__(self, parsing_rules: dict, config: dict, collected_items: list):
        """
        Inicializa la suscripción con reglas de parsing, configuración y una lista para recolectar items.

        Args:
            parsing_rules: Diccionario con selectores para extraer datos.
            config: Diccionario de configuración general (para acceder a extract_emails, etc.).
            collected_items: Una lista donde se añadirán los diccionarios de datos extraídos.
        """
        self.parsing_rules = parsing_rules
        self.config = config
        # La lista collected_items debe ser compartida entre todas las tareas
        # y ser accesible desde run_spider después de asyncio.gather.
        self.collected_items = collected_items
        logger.info("GoogleMapsSubscription creada.")

    # Este método es llamado por spider-rs para cada página scrapeada
    # 'page' es el objeto que representa la página scrapeada, proporcionado por spider-rs.
    # La estructura y atributos del objeto 'page' dependen de spider-rs (ej. page.url, page.text, page.status_code).

                # Este método es llamado por spider-rs para cada página scrapeada
    # 'page' es el objeto que representa la página scrapeada, proporcionado por spider-rs.
    # La estructura y atributos del objeto 'page' dependen de spider-rs (ej. page.url, page.text, page.status_code).
    async def __call__(self, page):
        logger.info(f"Subscription procesando URL: {page.url} con status code: {page.status_code}")
    
        if page.status_code != 200:
            logger.warning(f"Página {page.url} devolvió status code {page.status_code}. Saltando parsing.")
            return

    city_associated = "ParseError_City"
    keyword_associated = "ParseError_Keyword"

    try:
        parsed_url = urlparse(page.url)
        path_parts = parsed_url.path.rstrip('/').split('/')
        relevant_parts = [p for p in path_parts if p][-2:] if path_parts else []
        
        if len(relevant_parts) == 2:
            encoded_query_part = relevant_parts[0]
            encoded_city_part = relevant_parts[1]
            
            query = unquote(encoded_query_part.replace('+', ' '))
            city = unquote(encoded_city_part.replace('+', ' '))
            
            parts = query.split(' in ')
            if len(parts) == 2:
                keyword_associated = parts[0].strip()
                if parts[1].strip().lower() == city.lower():
                    city_associated = city.strip()
                else:
                    city_associated = city.strip()
                    keyword_associated = query.strip()
            else:
                city_associated = city.strip()
                keyword_associated = query.strip()
                
        elif len(relevant_parts) == 1:
            keyword_associated = unquote(relevant_parts[0].replace('+', ' ')).strip()
            city_associated = "UnknownCity_PartialURL"
            
    except Exception as url_parse_e:
        logger.error(f"Error al parsear URL '{page.url}': {url_parse_e}", exc_info=True)

    html_content = page.text
    extracted_data = parse_html(html_content, self.parsing_rules)
    
    extracted_data.update({
        'ciudad': city_associated,
        'keyword_buscada': keyword_associated,
        'url_scrapeada': page.url
    })

    if extracted_data.get("nombre_negocio"):
        self.collected_items.append(extracted_data)
        logger.info(f"Item recolectado para {page.url}")
    else:
        logger.info(f"No se extrajeron datos significativos de {page.url}")

# Definición de reglas de parsing (usada por la Suscripción)
def _get_parsing_rules(config: dict):
    """
    Define las reglas de parsing (selectores CSS/XPath) para Google Maps.
    Recibe la configuración para ajustar reglas (ej. extraer emails).

    Ajusta este diccionario con los selectores reales que encuentres.
    """
    rules = {
        # Selector actualizado basado en la inspección del detalle del negocio (h1)
        "nombre_negocio": "h1.DUwDvf.lfPIob",
        # Selector para la dirección (identificado en la vista de detalle)
        "direccion": "div.Io6YTe.fontBodyMedium.kR99db.fdkmkc",
        # Selector para teléfono (buscando el enlace tel: dentro del div relevante)
        "telefono": "div.Io6YTe a[href^=\"tel:\"]::attr(href)",
        # Selector para sitio web (buscando el enlace con la clase lcrQfb)
        "sitio_web": "a.lcrQfb::attr(href)",

        # Puedes añadir más reglas y selectores REALES aquí para otra información relevante (ej: rating, número de reseñas, categoría, etc.).
        # Ejemplo (si encuentras los selectores):
        # "rating": "span.MW4etd",
        # "reseñas_count": "span.UY7F9",
        # "categoria": "div.W4Efsd span span", # Este puede variar, necesita verificación

    }
    # Regla para extraer emails, solo si extract_emails es True
    if config.get('extract_emails', False):
        # Selector para email (buscando el enlace mailto: dentro del div relevante)
        rules["email_contacto"] = "div.Io6YTe a[href^=\"mailto:\"]::attr(href)"

    return rules




# Función para generar URLs de búsqueda en Google Maps
# Las URLs generadas aquí son básicas y podrían necesitar ajustes
# si Google Maps requiere un formato diferente para el scraping o si necesitas incluir coordenadas.
def generate_google_maps_urls(cities: list, keywords_by_city: dict) -> list[str]:
    """
    Genera una lista de URLs de búsqueda en Google Maps basadas en ciudades y palabras clave.

    Args:
        cities: Lista de nombres de ciudades.
        keywords_by_city: Diccionario donde las claves son nombres de ciudades
                          y los valores son listas de palabras clave.

    Returns:
        Una lista de cadenas de URL.
    """
    urls = []
    base_url = "https://www.google.com/maps/search/"

    for city in cities:
        keywords = keywords_by_city.get(city, [])

        # Considerar añadir coordenadas si cities.json incluye esos datos
        # y si tu estrategia de scraping en Google Maps lo requiere.
        # La estructura de cities.json ahora incluye gmaps_coordinates,
        # pero la función generate_google_maps_urls actual no las usa.
        # Si la librería spider-py/Rs permite pasar datos contextuales con la URL,
        # o si necesitas URLs de Maps más específicas (usando place IDs o coordenadas),
        # esta función necesitaría ser modificada.
        # Por ahora, solo usamos la consulta de texto.

        for keyword in keywords:
            query = f"{keyword} in {city}"
            # Codificar la consulta para la URL
            encoded_query = "+".join(query.split())
            url = f"{base_url}{encoded_query}/" # Google Maps a menudo termina con /search/.../

            urls.append(url)
            logger.info(f"Generada URL: {url} para '{keyword}' en '{city}'")

    # Nota sobre la profundidad (depth): Controlar la profundidad en Google Maps
    # (como cargar más resultados desplazándose o haciendo clic en "Más resultados")
    # generalmente requiere lógica dentro del spider (método parse o un método de pagination),
    # lo cual se manejaría dentro de la clase de suscripción o a través de la configuración
    # de Website si spider-rs lo soporta (ej. limitando páginas, siguiendo ciertos enlaces).
    # La variable 'depth' de la config debería ser usada por la lógica dentro de la Suscripción
    # o por la configuración de Website si aplica.

    return urls


# Función principal asíncrona para ejecutar el proceso de scraping con spider-rs
async def run_spider(config: dict) -> pd.DataFrame:
    """
    Ejecuta el proceso de scraping utilizando la librería spider-rs de forma concurrente para múltiples URLs.
    Esta función ahora es asíncrona y debe ser llamada con await.

    Args:
        config: Un diccionario conteniendo la configuración de scraping.
                Claves esperadas:
                'cities': lista de nombres de ciudades
                'keywords': dictionary where keys are city names and values are lists of keywords
                'depth': integer representing the scraping depth (usado por la Suscripción/Website)
                'emails': boolean indicating whether to extract emails

    Returns:
        A pandas DataFrame containing the scraped data.
        Retorna un DataFrame vacío si ocurre un error o no se recolectan datos.
    """
    logger.info(f"Iniciando el proceso de scraping concurrente con la siguiente configuración: {config}")

    cities = config.get('cities', [])
    keywords_by_city = config.get('keywords', {})
    depth = config.get('depth', 1) # Pasa depth a la configuración si Website lo usa
    extract_emails = config.get('extract_emails', False)

    # 1. Generar las URLs de inicio
    start_urls = generate_google_maps_urls(cities, keywords_by_city)

    # Asegurarse de que hay URLs para scrapear
    if not start_urls:
        logger.warning("No se generaron URLs para scrapear. Verifique las ciudades y palabras clave.")
        return pd.DataFrame() # Retorna un DataFrame vacío si no hay URLs

    # --- Configuración y ejecución concurrente con spider-rs ---

    collected_items = [] # Lista compartida para recolectar los items extraídos por todas las suscripciones

    try:
        logger.info(f"Generadas {len(start_urls)} URLs de inicio para scraping concurrente.")

        # 2. Crear tareas de scraping (corutinas) para cada URL
        tasks = []
        # Crear una única instancia de Suscripción que todas las tareas compartirán
        # para añadir items a la misma lista collected_items.
        parsing_rules = _get_parsing_rules(config)
        shared_subscription = GoogleMapsSubscription(parsing_rules, config, collected_items)

        for url in start_urls:
            # Validar URL básica (podrías querer validaciones más robustas)
            if not url.startswith(('http://', 'https://')):
                 logger.warning(f"URL inválida o incompleta, omitiendo: '{url}'")
                 continue

            # Crear una instancia de Website para cada URL.
            # El segundo argumento (False en ejemplos) parece controlar si se sigue link externos.
            # Para Google Maps, probablemente no queremos seguir links externos por defecto.
            # Si spider-rs tiene opciones de configuración adicionales a nivel de Website (ej. proxy), configúralas aquí.
            try:
                website_instance = Website(url, False)
                # Si Website tiene otros métodos de configuración que aplican por URL, úsalos aquí.
                # website_instance.with_user_agent("MyGoogleMapsScraper") # Ejemplo

                # Crear la corutina (tarea asíncrona) para ejecutar crawl en esta Website con la Suscripción compartida
                # El método .crawl() de Website es asíncrono en spider-rs.
                task = website_instance.crawl(shared_subscription) # Pasar la instancia de la suscripción compartida
                tasks.append(task)
                logger.debug(f"Tarea creada para URL: {url}") # Usar debug para no llenar logs con cada URL

            except Exception as url_e:
                logger.error(f"Error al crear instancia de Website o tarea para URL '{url}': {url_e}")
                # Decide si este error debe detener todo o solo omitir esta URL. Omitir es lo más común.

        # 3. Ejecutar todas las tareas de forma concurrente
        if not tasks:
            logger.warning("No hay tareas de scraping válidas para ejecutar después de la creación. Verifique URLs.")
            return pd.DataFrame() # Retorna un DataFrame vacío si no hay tareas válidas

        logger.info(f"Lanzando {len(tasks)} tareas de scraping concurrentes con asyncio.gather...")

        # asyncio.gather ejecuta todas las corutinas en la lista 'tasks' y espera a que todas terminen.
        # Devuelve una lista de los valores devueltos por cada corutina (que en el caso de website.crawl(subscription)
        # parece ser None o un objeto de Website según los ejemplos que vi).
        # LO IMPORTANTE es que la Suscripción (__call__) ha estado poblando 'collected_items' en el fondo.
        try:
            await asyncio.gather(*tasks) # Espera a que todas las tareas de crawl finalicen

        except Exception as e:
            # Este bloque catch capturará excepciones que escapen de las corutinas individuales
            logger.error(f"Ocurrió un error durante la ejecución concurrente de asyncio.gather: {e}")
            # Importante: Aunque hubo un error, 'collected_items' podría contener algunos datos
            # recolectados antes del fallo. No la reseteamos aquí.
            import traceback
            logger.error(traceback.format_exc())


        logger.info(f"Ejecución concurrente de scraping finalizada.")

        # Después de que asyncio.gather finaliza (exitosamente o con error capturado),
        # la lista 'collected_items' de la Suscripción compartida debería contener todos
        # los ítems que fueron yield-ed por el método __call__ de la suscripción
        # para todas las URLs procesadas.

        logger.info(f"Items recolectados por la suscripción (total): {len(collected_items)}")


    except Exception as e: # Manejo de errores general en run_spider (antes o después de gather)
        logger.error(f"Ocurrió un error general en run_spider (pre/post-gather): {e}")
        import traceback
        logger.error(traceback.format_exc())
        # En app_streamlit.py, asegúrate de capturar errores de run_spider
        # (que ahora es async) y mostrarlos en la UI para el usuario.
        # Si un error ocurrió antes de collect_items, collected_items podría estar vacía.
        # Si ocurrió durante gather, collected_items podría tener datos parciales.

    # 4. Convertir los resultados recolectados a un DataFrame de pandas
    #    'collected_items' es la lista de diccionarios llenada por la suscripción.
    #    Si 'collected_items' está vacía (por errores o falta de resultados), el DataFrame estará vacío.
    df_results = pd.DataFrame(collected_items)


    # --- Fin de la sección de integración concurrente ---

    # Guardar el DataFrame resultante a un archivo CSV
    RAW_DATA_DIR = "/workspace/0_AGENTE_SPIDER/data/raw" # Asegúrate de que esta ruta sea accesible y persistente

    os.makedirs(RAW_DATA_DIR, exist_ok=True) # Asegurar que el directorio existe

    if not df_results.empty: # Solo guardar si hay datos en el DataFrame
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraped_data_{timestamp}.csv"
        file_path = os.path.join(RAW_DATA_DIR, filename)

        try:
            # Usar encoding 'utf-8' para manejar caracteres especiales en los datos scrapeados
            df_results.to_csv(file_path, index=False, encoding='utf-8')
            logger.info(f"Datos guardados con éxito en: {file_path}")
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Error al intentar guardar el archivo CSV en {file_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Deberías comunicar este error de guardado a la UI de Streamlit (app_streamlit.py)
    else:
        logger.info("DataFrame de resultados vacío. No se guardó ningún archivo CSV.")

    return df_results # Devolver el DataFrame (puede estar vacío)


def parse_html(html: str, rules: dict) -> dict:
    """
    Procesa el contenido HTML proporcionado basándose en reglas específicas (selectores CSS/XPath)
    y extrae datos utilizando BeautifulSoup.
    Esta función es llamada por el método __call__ de GoogleMapsSubscription.

    Args:
        html: El contenido HTML como una cadena.
        rules: Un diccionario de reglas definiendo cómo extraer datos
               (ej. {clave_dato: selector_css_o_xpath}).

    Returns:
        Un diccionario conteniendo los datos extraídos para un solo ítem.
        Retorna un diccionario vacío si no se puede parsear o si no se encuentra ningún dato.
    """
    extracted_data = {}
    if not html or not rules:
        logger.warning("parse_html recibió HTML vacío o reglas vacías.")
        return extracted_data

    try:
        # Usar el parser 'html.parser' que viene con la librería estándar de Python
        soup = BeautifulSoup(html, 'html.parser')

        # Iterar a través de las reglas y extraer los datos correspondientes
        for key, selector in rules.items():
            if not selector:
                logger.warning(f"No selector CSS/XPath proporcionado para la clave '{key}' en las reglas de parsing.")
                extracted_data[key] = None
                continue

            try:
                # Si el selector especifica un atributo (ej. 'a::attr(href)')
                if '::attr(' in selector:
                    selector_part, attr_part = selector.split('::attr(')
                    attribute = attr_part.rstrip(')')
                    element = soup.select_one(selector_part)
                    if element:
                        extracted_data[key] = element.get(attribute)
                    else:
                        extracted_data[key] = None
                        # logger.debug(f"Elemento no encontrado para selector '{selector_part}'")
                else: # Si el selector busca texto
                    element = soup.select_one(selector)
                    if element:
                        extracted_data[key] = element.get_text(strip=True)
                    else:
                        extracted_data[key] = None
                        # logger.debug(f"Elemento no encontrado para selector '{selector}'")

            except Exception as e:
                logger.error(f"Error procesando la regla '{key}' con selector '{selector}': {e}")
                import traceback
                logger.error(traceback.format_exc())
                extracted_data[key] = None # Asegurar que la clave existe aunque haya habido error

    except Exception as e:
         logger.error(f"Error general en parse_html al procesar el HTML: {e}")
         import traceback
         logger.error(traceback.format_exc())
         return {} # Devolver un diccionario vacío si hay un error en el parsing general

    # TODO: Si es posible, añade aquí información contextual como ciudad y keyword.
    #       Es mejor obtenerla en el método __call__ de la suscripción
    #       si la librería proporciona acceso a la Request original o a metadatos.
    #       Ya hemos añadido placeholders para esto en el método __call__.

    return extracted_data # Retorna el diccionario de datos extraídos para un solo ítem

# Función placeholder simulada que ya no se usa con la integración real.
# Se mantiene comentada por referencia.
# def _simulate_scrape_and_parse(...):
#    ...
