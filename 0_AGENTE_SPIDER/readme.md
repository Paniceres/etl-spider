Aquí tienes el **README.md** actualizado para **Agente Spider**, optimizado para enfocarse en la generación de CSVs crudos y alineado con la estructura y estilo del proyecto GOSOM, pero adaptado a las necesidades específicas de Spider:

---

# 🚀✨ Agente Spider - Especificación de la Interfaz Streamlit 📊🤖

---

## 🎯 Objetivo General de la UI

Proporcionar una **interfaz web simple y amigable** para configurar, ejecutar y monitorear tareas de scraping de Google Maps con el **Agente Spider**, generando **CSVs crudos por ciudad** que se procesarán en el **ETL Central**.

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
  - **Opciones:** Cargadas desde `SPIDER_COORDINATES` en `parameters_default.json`.  
  - **Label:** "Seleccionar Ciudad(es) a Procesar"  

- 📝 **Widget 2: Gestión de Keywords por Ciudad**  
  - **Cada ciudad tiene un `st.text_area`** con keywords precargadas desde `/config/keywords_<ciudad>.csv`.  
  - **Editable:** El usuario puede añadir, modificar o eliminar palabras clave.  
  - **Label:** "Keywords para [Nombre de la Ciudad]"  

- 🔍 **Widget 3: Profundidad de Búsqueda (`depth`)**  
  - **Tipo:** `st.slider`  
  - **Rango sugerido:** 1 a 20  
  - **Valor por defecto:** `DEFAULT_DEPTH` en `parameters_default.json`.  

- 📧 **Widget 4: Activar Extracción de Emails**  
  - **Tipo:** `st.checkbox`  
  - **Valor por defecto:** `True`  
  - **Nota:** Aumenta el tiempo de ejecución.  

- ▶️ **Widget 5: Botón de Inicio**  
  - **Tipo:** `st.button`  
  - **Label:** "🚀 Iniciar Scraping"  

---

### 2. 📈 Monitoreo de Progreso (Main Area)

Mantiene informado al usuario sobre el estado de la ejecución.

- ✨ **Título:** "Progreso de la Tarea"  
- ⏳ **Indicador de Actividad:** `st.spinner("Scraping en progreso...")`  
- 📜 **Registro del Proceso (Log):**  
  - **Implementación actual:** Mostrar contenido de `/data/logs/spider.log` con `st.text_area`.  
  - *Futuro:* Mostrar logs en tiempo real con `tail -n 50`.  

---

### 3. 📊 Visualización de Resultados (Main Area - Pestañas)

#### 📁 Pestaña/Sección 1: Datos Crudos (por ciudad)

- Seleccionar ciudad de entre las procesadas.  
- Mostrar vista previa con `st.dataframe`.  
- Descargar CSV específico con `st.download_button`.  

---

## 📂 Estructura de Archivos

```text
0_agente_spider/
├── 0_prompts/
│   ├── 0_Futuro.md          # Ideas futuras
│   ├── 1_Mejoras.md         # Tareas pendientes
│   └── 2_Historial.md       # Tareas completadas
├── config/
│   ├── parameters_default.json
│   └── keywords_<ciudad>.csv
├── data/
│   ├── raw/                 # CSVs crudos generados por Spider
│   └── logs/                # Logs de ejecución
├── src/
│   ├── core_logic.py        # Lógica de scraping (sin consolidación)
│   └── utils.py             # Funciones auxiliares
├── app_streamlit.py         # Interfaz principal
├── 0_PLAN_SPIDER.md         # Planificación del proyecto
└── README.md                # Documentación general
```

---

## 📁 Ubicaciones de Archivos Clave

- **CSVs Crudos:** `/data/raw/<ciudad>_<timestamp>.csv`  
- **Configuración de Parámetros:** `/config/parameters_default.json`  
- **Keywords por Ciudad:** `/config/keywords_<ciudad>.csv`  
- **Logs de Ejecución:** `/data/logs/spider.log`  

---

## 🚶‍♂️ Flujo de Usuario Típico

1. **Acceso:**  
   - El usuario accede a la aplicación Streamlit desde el navegador.  

2. **Configuración:**  
   - En la barra lateral:  
     - Selecciona ciudades y edita keywords.  
     - Define profundidad y activa/desactiva extracción de emails.  

3. **Ejecución:**  
   - Hace clic en "🚀 Iniciar Scraping".  
   - Mientras se ejecuta:  
     - Ve un spinner indicando actividad.  
     - Al finalizar, muestra el log completo del proceso.  

4. **Resultados:**  
   - Descarga los CSVs crudos generados.  

---

## 📂 Documentación Adicional

- 🚀 **[Ideas Futuras](0_prompts/0_Futuro.md):** Mejoras para versiones futuras.  
- 📋 **[Tareas Pendientes](0_prompts/1_Mejoras.md):** Plan de trabajo para el MVP.  
- ✅ **[Historial de Mejoras Completadas](0_prompts/2_Historial.md):** Registro de tareas resueltas.  

---

## 📌 Notas Clave

- **Enfoque en Scraping:** Spider se limita a generar CSVs crudos sin procesamiento adicional.  
- **ETL Central:** Toda la consolidación, deduplicación y chunkeo se realizarán en un módulo separado.  
- **Sin dependencias costosas:** Solo herramientas gratuitas (Streamlit, Pandas).  

---

*¡Gracias por leer esta documentación!  
El Agente Spider está diseñado para ser **simple, modular y escalable**.* 🌟  

---
