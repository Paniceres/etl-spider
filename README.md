# ETL Spider 🕷️🕸️

¡Bienvenido a **ETL Spider**! 
Este proyecto es una herramienta súper rápida diseñada para "navegar" o "rastrear" páginas web de forma automática (lo que en el mundo tecnológico se conoce como un *web scraper* o *spider*).

**¿Para qué sirve?**
Imagina que necesitas leer miles de páginas de un sitio web para recopilar información. Hacerlo a mano te tomaría días o meses. Este "spider" lo hace por ti en cuestión de minutos, extrae los enlaces y la información que necesitas, y guarda todo de forma organizada. 

Originalmente, este proyecto es una adaptación para **Python** del rapidísimo motor [spider-rs](https://github.com/spider-rs/spider) (construido en Rust). Esto significa que combina la facilidad de uso de Python con la velocidad extrema de Rust. ¡Es una de las herramientas más rápidas en su tipo!

---

## Para Usuarios Técnicos 🛠️

A continuación, encontrarás las instrucciones detalladas para instalar, usar y contribuir al desarrollo de esta herramienta.

### Primeros Pasos

La forma más fácil de instalar es usando pip:

1. `pip install spider_rs`

**Ejemplo de uso básico en Python:**

```python
import asyncio
from spider_rs import Website

async def main():
    # Definimos el sitio web que queremos rastrear
    website = Website("https://choosealicense.com")
    # Iniciamos el rastreo
    website.crawl()
    # Imprimimos los enlaces encontrados
    print(website.get_links())

# Ejecutamos la función principal
asyncio.run(main())
```

Consulta la carpeta de [ejemplos](./examples/) para aprender sobre usos más avanzados.

### Desarrollo Local

Si quieres modificar el código fuente de la herramienta (desarrollo de la librería en sí), sigue estos pasos. Se recomienda encarecidamente utilizar un entorno virtual de Python para aislar las dependencias y evitar conflictos.

1. **Instala las herramientas de construcción necesarias:**
   * **Python**: Asegúrate de tener Python instalado.
   * **Rust**: Instala Rust a través de `rustup` (https://rustup.rs/). Esto incluirá `cargo`, que es necesario para compilar el código de Rust.
   * **Maturin**: Instala maturin usando `pipx install maturin` (o `pip install maturin`). Maturin es necesario para construir el paquete de Python desde el código de Rust.

2. **Crea un entorno virtual de Python:**
   ```bash
   python -m venv .venv
   ```

3. **Activa el entorno virtual:**
   * En Windows:
     ```bash
     .venv\Scripts\activate
     ```
   * En macOS y Linux:
     ```bash
     source .venv/bin/activate
     ```

4. **Instala el proyecto en modo editable con maturin:**
   ```bash
   maturin develop
   ```

### Rendimiento (Benchmarks)

Puedes ver las [pruebas de rendimiento](./bench/README.md) detalladas para comparar entre diferentes librerías y plataformas.

Prueba con la URL: `https://espn.com`

| `Librería`                   | `Páginas analizadas` | `Tiempo` |
| :--------------------------- | :------------------- | :------- |
| **`spider(rust): crawl`**    | `150,387`            | `1m`     |
| **`spider(nodejs): crawl`**  | `150,387`            | `153s`   |
| **`spider(python): crawl`**  | `150,387`            | `186s`   |
| **`scrapy(python): crawl`**  | `49,598`             | `1h`     |
| **`crawlee(nodejs): crawl`** | `18,779`             | `30m`    |

*Nota: Las pruebas anteriores se ejecutaron en una Mac M1. El "spider" en máquinas Linux ARM funciona de 2 a 10 veces más rápido.*

### Problemas o Bugs (Issues)

Por favor, envía un "Issue" en Github para cualquier error que encuentres en el código original.
