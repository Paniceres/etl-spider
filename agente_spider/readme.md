# 🚀✨ Agente Spider - Especificación de la Interfaz Streamlit 📊🤖

---

## 🎯 Objetivo General de la UI  
Proporcionar una **interfaz web simple y amigable** para configurar, ejecutar y monitorear tareas de scraping de Google Maps con el **Agente Spider**, generando **CSVs crudos por ciudad**.

---

## 📐 Layout General  
La interfaz se divide en dos áreas principales:  

- 🖥️ **Barra Lateral (Sidebar):**  
  - Configuración de parámetros (ciudades, keywords, profundidad, extracción de emails).  
  - Botón "🚀 Iniciar Scraping".  

- 📊 **Área Principal (Main Area):**  
  - Pestañas para:  
    - **Datos Crudos**: Vista previa y descarga por ciudad.  
    - **Logs**: Visualización de registros de ejecución.  

---

## 🛠️ Componentes y Funcionalidades Detalladas  

### 1. ⚙️ Configuración de la Tarea de Scraping (Sidebar)  
Permite al usuario definir los parámetros para ejecutar el scraping de Google Maps.  

- ✨ **Título:** "Configurar Nueva Tarea de Scraping"  
- 🌍 **Widget 1: Selección de Ciudad(es)**  
  - **Tipo:** `st.multiselect`  
  - **Opciones:** Cargadas desde `cities.json`.  
  - **Label:** "Seleccionar Ciudad(es) a Procesar".  
- 📝 **Widget 2: Gestión de Keywords por Ciudad**  
  - **Cada ciudad tiene un `st.text_area`** con keywords precargadas desde `/config/keywords_<ciudad>.csv`.  
  - **Editable:** El usuario puede añadir, modificar o eliminar palabras clave.  
  - **Label:** "Keywords para [Nombre de la Ciudad]".  
- 🔍 **Widget 3: Profundidad de Búsqueda (`depth`)**  
  - **Tipo:** `st.slider`  
  - **Rango sugerido:** 1 a 20.  
- 📧 **Widget 4: Activar Extracción de Emails**  
  - **Tipo:** `st.checkbox`.  
  - **Valor por defecto:** `True`.  
- ▶️ **Widget 5: Botón de Inicio**  
  - **Tipo:** `st.button`.  
  - **Label:** "🚀 Iniciar Scraping".  

---

## 📁 Estructura de Archivos  
```text
0_AGENTE_SPIDER/  
├── config/             # Keywords y ciudades  
│   ├── cities.json     # Coordenadas de ciudades  
│   └── keywords_<ciudad>.csv  
├── data/               # Datos crudos y logs  
│   ├── raw/            # CSVs crudos generados  
│   └── logs/           # Logs de ejecución  
├── src/                # Lógica de scraping  
│   └── spider.py       # Funciones de scraping  
├── app_streamlit.py    # Interfaz principal  
├── 0_PLAN_SPIDER.md    # Planificación del proyecto  
└── README.md           # Documentación general  