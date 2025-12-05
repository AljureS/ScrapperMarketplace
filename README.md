# 🛫 Scraper de Investigación: Aerolíneas Colombianas

Sistema automatizado de web scraping y análisis para investigar la viabilidad de un marketplace de reventa de boletos aéreos en Colombia.

## 📋 Descripción

Este proyecto analiza las políticas de cambio de nombre, cancelación y transferencia de boletos de las principales aerolíneas que operan en Colombia para determinar la viabilidad de crear un marketplace de reventa de boletos.

### Aerolíneas Analizadas

- ✈️ **Avianca** (AV) - Líder del mercado colombiano
- ✈️ **LATAM** (LA) - Segunda aerolínea más grande
- ✈️ **Wingo** (P5) - Low-cost, subsidiaria de Copa
- ✈️ **EasyFly** (VE) - Regional, rutas secundarias
- ✈️ **Satena** (9R) - Aerolínea estatal
- ✈️ **Copa Airlines** (CM) - Hub en Panamá
- ✈️ **JetSmart** (JA) - Low-cost chilena

## 🎯 Objetivo

Responder la pregunta: **¿Es viable crear un marketplace de reventa de boletos aéreos en Colombia?**

El sistema extrae, analiza y reporta información sobre:
- Políticas de cambio de nombre
- Costos de modificación
- Políticas de transferencia a terceros
- Políticas de cancelación y reembolso
- Restricciones y condiciones

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Conexión a Internet

### Instalación

1. **Clonar el repositorio o navegar al directorio:**

```bash
cd scrapeTravel
```

2. **Crear entorno virtual:**

```bash
python -m venv venv
```

3. **Activar entorno virtual:**

```bash
# En macOS/Linux:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

4. **Instalar dependencias:**

```bash
pip install -r requirements.txt
```

5. **Copiar archivo de configuración:**

```bash
cp .env.example .env
```

### Ejecución Completa

Para ejecutar el proceso completo (scraping + análisis + reporte):

```bash
python main.py run-all
```

Esto ejecutará:
1. ✅ Scraping de todas las aerolíneas
2. ✅ Análisis estadístico con Pandas
3. ✅ Generación de gráficos comparativos
4. ✅ Exportación a CSV, JSON y Excel
5. ✅ Generación del reporte markdown

**Tiempo estimado:** 25-60 minutos (dependiendo de la velocidad de conexión)

## 📖 Uso Detallado

### Comandos Disponibles

#### 1. Scraping

**Scrapear todas las aerolíneas:**
```bash
python main.py scrape --all
```

**Scrapear una aerolínea específica:**
```bash
python main.py scrape --airline AV    # Avianca
python main.py scrape --airline LA    # LATAM
python main.py scrape --airline P5    # Wingo
```

#### 2. Análisis

**Generar análisis estadístico:**
```bash
python main.py analyze
```

Esto genera:
- Estadísticas descriptivas
- Reporte de viabilidad
- Gráficos comparativos (PNG)

#### 3. Exportación

**Exportar datos a diferentes formatos:**
```bash
python main.py export --format csv,json,xlsx
```

Formatos disponibles:
- `csv` - Comma-Separated Values
- `json` - JavaScript Object Notation
- `xlsx` - Microsoft Excel

#### 4. Reporte

**Generar reporte markdown:**
```bash
python main.py report
```

Genera el archivo `REPORTE_VIABILIDAD.md` con análisis completo.

## 📁 Estructura del Proyecto

```
scrapeTravel/
│
├── main.py                      # 🎯 Punto de entrada principal
├── requirements.txt             # 📦 Dependencias del proyecto
├── README.md                    # 📖 Este archivo
├── .env.example                 # ⚙️ Configuración de ejemplo
├── .gitignore                   # 🚫 Archivos ignorados por git
│
├── src/                         # 📂 Código fuente
│   ├── __init__.py
│   ├── config.py                # ⚙️ Configuración y constantes
│   ├── models.py                # 📊 Modelos de datos (dataclasses)
│   ├── database.py              # 💾 Gestión de SQLite
│   ├── utils.py                 # 🛠️ Funciones auxiliares y regex
│   ├── analyzer.py              # 📈 Análisis con Pandas
│   ├── report_generator.py      # 📄 Generador de reportes
│   │
│   └── scrapers/                # 🕷️ Scrapers de aerolíneas
│       ├── __init__.py
│       ├── base_scraper.py      # 🏗️ Clase base abstracta
│       ├── avianca_scraper.py
│       ├── latam_scraper.py
│       ├── wingo_scraper.py
│       ├── easyfly_scraper.py
│       ├── satena_scraper.py
│       ├── copa_scraper.py
│       └── jetsmart_scraper.py
│
├── data/                        # 📊 Datos y resultados
│   ├── policies.db              # 💾 Base de datos SQLite
│   ├── snapshots/               # 📸 HTML guardado por fecha
│   └── exports/                 # 📤 Archivos exportados
│       ├── policies.csv
│       ├── policies.json
│       ├── policies.xlsx
│       ├── REPORTE_VIABILIDAD.md
│       └── graficos/            # 📊 Gráficos PNG
│
├── logs/                        # 📝 Archivos de log
│   └── scraper.log
│
└── tests/                       # 🧪 Tests (futuro)
    └── test_scrapers.py
```

## 📊 Archivos Generados

Después de ejecutar `python main.py run-all`, encontrarás:

### 1. Base de Datos
- `data/policies.db` - SQLite con todas las políticas

### 2. Exportaciones
- `data/exports/policies.csv` - Datos en CSV
- `data/exports/policies.json` - Datos en JSON
- `data/exports/policies.xlsx` - Excel con formato

### 3. Reporte Principal
- `data/exports/REPORTE_VIABILIDAD.md` - **⭐ Reporte principal con conclusiones**

### 4. Gráficos
- `data/exports/graficos/costos_comparacion.png` - Comparación de costos
- `data/exports/graficos/politicas_distribucion.png` - Distribución de políticas
- `data/exports/graficos/politicas_comparacion.png` - Comparación por aerolínea
- `data/exports/graficos/cobertura_datos.png` - Heatmap de cobertura

### 5. Snapshots HTML
- `data/snapshots/[airline]_[timestamp].html` - HTML original de cada scraping

### 6. Logs
- `logs/scraper.log` - Log detallado de ejecución

## 🔧 Configuración

El archivo `.env` permite personalizar:

```bash
# Rate Limiting (segundos entre requests)
MIN_DELAY=2
MAX_DELAY=5

# Timeouts
REQUEST_TIMEOUT=30
PAGE_LOAD_TIMEOUT=45

# Retry
MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO

# Exportación
EXPORT_CSV=true
EXPORT_JSON=true
EXPORT_EXCEL=true
GENERATE_CHARTS=true
```

## 🧩 Arquitectura

### Diseño Modular

El proyecto usa **herencia de clases** para máxima modularidad:

```python
BaseScraper (abstracta)
    ├── AviancaScraper
    ├── LatamScraper
    ├── WingoScraper
    └── ... (otros scrapers)
```

Cada scraper:
- Hereda funcionalidad común de `BaseScraper`
- Implementa lógica específica en `extract_data()`
- Maneja errores de forma robusta
- Guarda snapshots HTML
- Calcula confidence scores

### Flujo de Datos

```
1. Scraping → 2. Validación → 3. Base de Datos → 4. Análisis → 5. Reporte
```

## 📊 Datos Extraídos

Para cada aerolínea se extrae:

### Campos Críticos
- ✅ Permite cambio de nombre completo
- ✅ Permite corrección de nombre
- ✅ Costo de cambio (doméstico/internacional)
- ✅ Permite transferencia a terceros

### Campos Importantes
- Permite cancelación
- Costo de cancelación
- Porcentaje de reembolso
- Restricciones temporales
- Diferencias entre tarifas

### Metadatos
- URL de origen
- Fecha de scraping
- Hash del HTML (para detectar cambios)
- Confidence score
- Requiere revisión manual (flag)

## 🎯 Criterios de Viabilidad

El sistema determina viabilidad basado en:

1. **Cobertura de Mercado** ≥ 40% de aerolíneas permiten transferencia
2. **Costos Razonables** ≤ $200,000 COP promedio
3. **Mínimo de Aerolíneas** ≥ 3 aerolíneas viables

### Estados Posibles

- ✅ **VIABLE** - Cobertura ≥ 60%
- ⚠️ **VIABLE CON RESTRICCIONES** - Cobertura 40-59%
- ❌ **NO VIABLE** - Cobertura < 40%

## 🛡️ Consideraciones Legales

### ⚠️ Disclaimer Importante

Este proyecto es para **investigación y análisis**. Antes de implementar un marketplace:

1. ✅ **Consultar con abogado** especializado en derecho aeronáutico
2. ✅ **Verificar políticas** directamente con cada aerolínea
3. ✅ **Revisar regulaciones** de Aerocivil Colombia
4. ✅ **Obtener permisos** necesarios de aerolíneas
5. ✅ **Respetar robots.txt** y términos de servicio

### Web Scraping Responsable

Este scraper:
- ✅ Usa delays entre requests (rate limiting)
- ✅ Respeta timeouts razonables
- ✅ Implementa retry con backoff exponencial
- ✅ Rota User-Agents
- ✅ No hace requests excesivos (1 cada 2-5 segundos)
- ✅ Guarda snapshots para análisis posterior

**Nota:** Verifica `robots.txt` de cada sitio antes de uso en producción.

## 🔍 Manejo de Errores

El sistema maneja múltiples escenarios:

### CAPTCHAs Detectados
Si detecta CAPTCHA, marca la aerolínea para revisión manual.

### Páginas con JavaScript
Configura `requires_javascript=True` en `config.py` para usar Playwright.

### Datos Incompletos
- Calcula confidence score automáticamente
- Marca para revisión manual si score < 0.4
- Continúa con otras aerolíneas

### Fallos de Red
- Reintentos automáticos con backoff exponencial
- Logging detallado de errores
- Proceso continúa con siguientes aerolíneas

## 📈 Análisis Estadístico

El módulo `analyzer.py` genera:

### Estadísticas Descriptivas
- Promedios, medianas, rangos
- Distribuciones de costos
- Porcentajes de políticas

### Visualizaciones
- Gráficos de barras (costos)
- Pie charts (distribuciones)
- Heatmaps (cobertura de datos)

### Reporte de Viabilidad
- Score agregado (0.0 a 1.0)
- Conclusión ejecutiva
- Recomendaciones accionables

## 🐛 Troubleshooting

### Problema: "ModuleNotFoundError"
**Solución:** Asegúrate de activar el entorno virtual y instalar dependencias:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Problema: "No se pudo obtener contenido HTML"
**Solución:**
- Verifica conexión a internet
- Algunas páginas pueden estar temporalmente caídas
- Intenta nuevamente más tarde

### Problema: "Requiere revisión manual"
**Solución:**
- Esto es esperado para algunas aerolíneas
- Revisa manualmente la URL en el reporte
- El proceso continúa con otras aerolíneas

### Problema: Playwright no funciona
**Solución:**
```bash
playwright install chromium
```

## 🚀 Próximos Pasos

Después de ejecutar el scraper:

1. **Leer el reporte:** `data/exports/REPORTE_VIABILIDAD.md`
2. **Revisar gráficos:** `data/exports/graficos/`
3. **Verificar datos manualmente** con aerolíneas
4. **Consultar asesoría legal** antes de proceder
5. **Tomar decisión** basada en conclusiones

## 🤝 Contribuir

Para mejorar el proyecto:

1. Crear nuevos scrapers para aerolíneas adicionales
2. Mejorar regex patterns de extracción
3. Agregar tests unitarios
4. Optimizar performance
5. Mejorar documentación

## 📝 Licencia

Este proyecto es para uso educativo y de investigación.

## 🙏 Agradecimientos

Construido con:
- **Scrapy** - Framework de scraping
- **BeautifulSoup4** - Parsing HTML
- **Pandas** - Análisis de datos
- **Matplotlib/Seaborn** - Visualizaciones
- **SQLite** - Base de datos

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa la sección de Troubleshooting
2. Verifica los logs en `logs/scraper.log`
3. Asegúrate de tener la última versión de dependencias

---

**¡Listo para usar!** 🚀

Ejecuta `python main.py run-all` y obtén tu reporte de viabilidad en minutos.

---

*Generado para investigación de mercado de boletos aéreos en Colombia*
# ScrapperMarketplace
