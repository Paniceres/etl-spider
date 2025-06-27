# 📝 0_PLAN_SPIDER.md
---
## 🎯 Objetivo General  
Crear una **UI Streamlit** gratuita y profesional que permita:  
- Definir **keywords por ciudad**.  
- Ejecutar pipelines de scraping con **Spider-py/Rs**.  
- Descargar CSVs “raw” por ciudad.  

---
## 🧰 Módulos y Tareas a Desarrollar  

### 1. Documentación y Planificación  
- [x] 📄 **README.md** base (ya hecho)  
- [x] 📋 **0_PLAN_SPIDER.md** (este archivo)  
- [x] 📝 Plantillas de Prompts para Gemini: **/0_AGENTE_SPIDER/0_prompts/0_Futuro.md**, **/0_AGENTE_SPIDER/0_prompts/0_Pasado.md**, **/0_AGENTE_SPIDER/0_prompts/1_Mejoras.md**
  - Prompt 1: Analizar errores en **/0_AGENTE_SPIDER/app_streamlit.py** y actualizar **/0_AGENTE_SPIDER/0_prompts/1_Mejoras.md**.
  - Prompt 2: Ejecutar tareas de mejora y mover a **/0_AGENTE_SPIDER/0_prompts/0_Pasado.md**.

### 2. Lógica Central (`core_logic.py`)
- [x] ⚙️ `run_spider(config: dict) → pd.DataFrame`: Implementación simulada añadida. Requiere integración con Spider-py/Rs.
- [x] 🕸️ `parse_html(html: str, rules: dict) → dict`: Implementación detallada añadida usando BeautifulSoup para extraer datos según reglas.
- [x] 📜 Configurar **RotatingFileHandler** para `/logs/spider.log`. Se ha añadido código placeholder y se requiere implementación real.
- [x] Añadir estructura detallada y comentarios a las funciones placeholder.
- [x] Añadir funciones auxiliares: `generate_google_maps_urls` y `_get_parsing_rules`. La estructura para integrar `spider-py/Rs` en `run_spider` está definida, pero **requiere reemplazar la simulación de ejecución** y **ajustar los selectores de parsing** en `_get_parsing_rules` para que coincidan con la estructura real de Google Maps.

### 3. Interfaz Streamlit (`app_streamlit.py`)
- [x] 🖥️ **Sidebar**  
  - [x] `st.multiselect(\"Seleccionar Ciudad(es)\", opciones)`
  - [x] `st.text_area(\"Keywords para X\", value=…)` + Botón “Guardar keywords”
  - [x] Mejorar manejo de errores, retroalimentación al usuario, y añadir indicador de progreso para el scraping.
  - [x] `st.checkbox` para extracción de emails
  - [x] `st.button("🚀 Iniciar Scraping")`
- [x] 📊 **Main Area con pestañas:**  

#### Refinamientos Adicionales de UI
- [ ] Añadir mensajes de error visuales (alta prioridad)
- [ ] Validar permisos de escritura en `/data/` (alta prioridad)

  - [x] **Crudos**: previsualización + `st.download_button` por ciudad
 - Se ha añadido un resumen básico del DataFrame (filas y columnas).
  - [x] **Logs**: `st.text_area` con tail de `/logs/spider.log`  
- [x] 🧩 Usar `st.expander()` y `st.columns()` para organización  
- [x] Gestión de Keywords por Ciudad
### 4. Configuración y Datos
- [x] 🗂️ /0_AGENTE_SPIDER/config/cities.json (Coordenadas de ciudades)
- [x] 🗂️ Ejemplos de **/0_AGENTE_SPIDER/config/keywords_<ciudad>.csv**: **/0_AGENTE_SPIDER/config/keywords_example.csv**, **/0_AGENTE_SPIDER/config/keywords_neuquen.csv**, **/0_AGENTE_SPIDER/config/keywords_cipolletti.csv**
- [x] 📂 **/0_AGENTE_SPIDER/data/raw/** (CSVs crudos generados por Spider): Estructura de directorios base creada. Se ha añadido código placeholder y se requiere implementación real.

## 📚 Historial de Mejoras (Checklist Estilo GOSOM)


---

## 🔮 Siguientes Pasos  
 Lista de Tareas Pendientes para Agente Spider:

Estas tareas se centran principalmente en implementar la lógica de scraping real y refinar la interfaz de usuario.

Integración de Spider-py/Rs en core_logic.py:

Objetivo: Reemplazar la implementación simulada de run_spider con llamadas reales a la librería spider-py/Rs. Acciones: Modificar la función run_spider en agente_spider/src/core_logic.py. Utilizar spider-py/Rs para configurar y ejecutar las tareas de scraping basadas en el diccionario config (que incluye ciudades, keywords, profundidad y opción de extraer emails). Asegurar que la función run_spider devuelva los resultados scrapeados como un pandas DataFrame. Manejar posibles errores o excepciones durante la ejecución de spider-py/Rs y registrarlos usando el sistema de logging. Ajuste de Selectores de Parsing en core_logic.py:

Objetivo: Asegurar que la función parse_html extraiga correctamente los datos de las páginas de resultados de Google Maps utilizando BeautifulSoup. Acciones: Revisar la función _get_parsing_rules y la lógica dentro de parse_html en agente_spider/src/core_logic.py. Actualizar los selectores CSS o XPath (dependiendo de cómo parse_html utilice BeautifulSoup y las "rules") para que coincidan con la estructura HTML actual de los listados de negocios en Google Maps. Identificar y extraer campos clave como nombre del negocio, categoría, dirección, teléfono, sitio web, email (si aplica y es extraíble), etc. Implementación Real del Logging en core_logic.py:

Objetivo: Configurar y utilizar correctamente un RotatingFileHandler para registrar la actividad y los errores del proceso de scraping principal. Acciones: Asegurarse de que el logger en agente_spider/src/core_logic.py (o donde se maneje el logging del core) esté configurado con RotatingFileHandler apuntando a agente_spider/data/logs/spider_core.log. Añadir mensajes de log informativos, de advertencia y de error en puntos clave de la ejecución de run_spider y las funciones relacionadas. Guardar Datos Scrapeados en /data/raw/ desde core_logic.py:

Objetivo: Guardar automáticamente los resultados del scraping en archivos CSV separados en el directorio agente_spider/data/raw/. Acciones: Dentro de run_spider (o una función auxiliar llamada por esta), implementar la lógica para guardar el DataFrame resultante (o partes de él, por ciudad o keyword) en archivos CSV. Utilizar pandas.DataFrame.to_csv para guardar los datos. Asegurar que los nombres de los archivos CSV sean descriptivos (ej: resultados_neuquen_abogados_YYYYMMDD_HHMMSS.csv). Manejar posibles errores de escritura de archivos. Refinamientos Adicionales de la UI en app_streamlit.py:

Objetivo: Mejorar la retroalimentación visual al usuario. Acciones: Implementar mensajes de error más visibles y amigables en la interfaz de Streamlit (utilizando st.error, st.warning, etc.) para los problemas que puedan ocurrir durante la carga de configuración, el scraping o el guardado de archivos. Validar los permisos de escritura en el directorio agente_spider/data/ al inicio de la aplicación o antes de intentar guardar archivos, e informar al usuario si hay problemas.