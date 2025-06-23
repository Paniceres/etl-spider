# 📝 0_PLAN_SPIDER.md

---

## 🎯 Objetivo General  
Crear una **UI Streamlit** gratuita y profesional que permita:  
- Definir **keywords por ciudad**.  
- Ejecutar pipelines de scraping con **Spider-py/Rs**.  
- Descargar CSVs “raw” por ciudad.  
- (Manual) Consolidar esos CSVs en un **CSV Madre** (delegado a ETL Central).  
- (Opcional) Chunkear desde la UI si pinta (delegado a ETL Central).  

---

## 🧰 Módulos y Tareas a Desarrollar

<<<<<<< Updated upstream
### 1. Documentación & Planificación  
- [ ] 📄 **README.md** base (ya hecho)  
- [ ] 📋 **0_PLAN_SPIDER.md** (este archivo)  
- [ ] 📝 Plantillas de Prompts para Gemini:  
  - Prompt 1: Analizar errores en `app_streamlit.py` y actualizar `0_mejoras.md`.  
  - Prompt 2: Ejecutar tareas de mejora y mover a `0_pasado.md`.  
  - Prompt 3: Registrar tareas completadas en `4_registro_tareas.md`.  

### 2. Lógica Central (`core_logic.py`)  
- [ ] ⚙️ `run_spider(config: dict) → pd.DataFrame`  
- [ ] 🕸️ `parse_html(html: str, rules: dict) → dict`  
- [ ] 📜 Configurar **RotatingFileHandler** para `/logs/spider.log`  

### 3. Interfaz Streamlit (`app_streamlit.py`)  
- [ ] 🖥️ **Sidebar**  
  - [ ] `st.multiselect("Seleccionar Ciudad(es)", opciones)`  
  - [ ] `st.text_area("Keywords para X", value=…)` + Botón “Guardar keywords”  
  - [ ] `st.slider` o `st.number_input` para `depth`  
  - [ ] `st.checkbox` para extracción de emails  
  - [ ] `st.button("🚀 Iniciar Scraping")`  
- [ ] 📊 **Main Area** con pestañas:  
  - [ ] **Crudos**: preview + `st.download_button` por ciudad  
  - [ ] **Logs**: `st.text_area` con tail de `/logs/streamlit.log`  
- [ ] 🧩 Usar `st.expander()` y `st.columns()` para organización  

### 4. Config & Datos  
- [ ] 🗂️ `/config/parameters_default.json` (ciudades, depth default)  
- [ ] 🗂️ Ejemplos de `/config/keywords_<ciudad>.csv`  
- [ ] 📂 `/data/raw/` (CSVs crudos generados por Spider)  
- [ ] 📂 `/logs/` con `spider.log` y `streamlit.log` vacíos  
- [ ] 🔄 **Integración con ETL Central:**  
  - Archivos crudos se guardan en `/data/raw/` para ser procesados por ETL Central.  
  - ETL Central se encargará de consolidación, deduplicación y chunkeo.  

### 5. Pruebas & CI  
- [ ] ✅ `tests/test_run_spider.py`  
- [ ] ✅ `tests/test_logs.py`  
- [ ] ⚙️ GitHub Actions: instalar deps + correr pytest + flake8  

### 6. Deploy (Opcional)  
- [ ] 🚀 `deploy.sh` para Streamlit Community Cloud o Heroku gratis  
- [ ] 📜 Instrucciones en README  

---
=======
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
  - [ ] `st.button("🚀 Iniciar Scraping")`
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
>>>>>>> Stashed changes

## 📚 Historial de Mejoras (Checklist Estilo GOSOM)

- [ ] **Fase 1: MVP**  
  - Interfaz básica, `run_spider`, descarga raw.  
- [ ] **Fase 2: Integración con ETL Central**  
  - Validar que CSVs crudos se guardan en `/data/raw/` correctamente.  
- [ ] **Fase 3: QA & Docs**  
  - Tests, CI, docs finales.  

---

## 🔮 Siguientes Pasos  
1. Validar este **0_PLAN_SPIDER.md**.  
2. Empezar por **core_logic.py**: crear `run_spider()`.  
3. Avanzar en **app_streamlit.py** módulo a módulo.  
4. Configurar **prompts para Gemini** para automatizar tareas.  