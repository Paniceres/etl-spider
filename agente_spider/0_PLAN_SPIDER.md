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

## 📚 Historial de Mejoras (Checklist Estilo GOSOM)

- [ ] **Fase 3: QA y Docs**
  - Pruebas, CI, documentación final.

---

## 🔮 Siguientes Pasos  
1. Validar este **0_PLAN_SPIDER.md**.  
2. Empezar por **core_logic.py**: crear `run_spider()`.  
3. Avanzar en **app_streamlit.py** módulo a módulo.  
4. Configurar **prompts para Gemini** para automatizar tareas.