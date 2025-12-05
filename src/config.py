"""
Configuración y constantes del proyecto
Carga variables de entorno y define configuración global
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Directorios base
BASE_DIR = Path(__file__).parent.parent.resolve()
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
EXPORTS_DIR = DATA_DIR / "exports"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
GRAFICOS_DIR = EXPORTS_DIR / "graficos"

# Crear directorios si no existen
for directory in [DATA_DIR, LOGS_DIR, EXPORTS_DIR, SNAPSHOTS_DIR, GRAFICOS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Base de datos
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "policies.db"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(LOGS_DIR / "scraper.log"))

# Rate Limiting
MIN_DELAY = float(os.getenv("MIN_DELAY", "2"))
MAX_DELAY = float(os.getenv("MAX_DELAY", "5"))

# Timeouts
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "45"))

# Retry Configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_BACKOFF = int(os.getenv("RETRY_BACKOFF", "2"))

# User Agents para rotación
USER_AGENTS = [
    os.getenv("USER_AGENT_1", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    os.getenv("USER_AGENT_2", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    os.getenv("USER_AGENT_3", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
]

# Playwright Configuration
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
BROWSER_TYPE = os.getenv("BROWSER_TYPE", "chromium")

# Claude API (opcional)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", None)

# Export Settings
EXPORT_CSV = os.getenv("EXPORT_CSV", "true").lower() == "true"
EXPORT_JSON = os.getenv("EXPORT_JSON", "true").lower() == "true"
EXPORT_EXCEL = os.getenv("EXPORT_EXCEL", "true").lower() == "true"
EXPORT_MARKDOWN = os.getenv("EXPORT_MARKDOWN", "true").lower() == "true"

# Análisis y Reporte
GENERATE_CHARTS = os.getenv("GENERATE_CHARTS", "true").lower() == "true"
CHART_DPI = int(os.getenv("CHART_DPI", "300"))

# Aerolíneas objetivo con sus URLs
AIRLINES_CONFIG = [
    {
        "nombre": "Avianca",
        "codigo": "AV",
        "url_politicas": "https://www.avianca.com/co/es/experiencia/condiciones-transporte/",
        "url_terminos": "https://www.avianca.com/co/es/footer/terminos-y-condiciones/",
        "prioridad": "alta",
        "notas": "Líder del mercado colombiano",
        "requires_javascript": False
    },
    {
        "nombre": "LATAM",
        "codigo": "LA",
        "url_politicas": "https://www.latamairlines.com/co/es/experiencia/cambios-y-reembolsos",
        "url_terminos": "https://www.latamairlines.com/co/es/condiciones-generales-de-transporte",
        "prioridad": "alta",
        "notas": "Segunda aerolínea más grande",
        "requires_javascript": False
    },
    {
        "nombre": "Wingo",
        "codigo": "P5",
        "url_politicas": "https://www.wingo.com/es/ayuda/cambios-y-cancelaciones",
        "url_terminos": None,
        "prioridad": "alta",
        "notas": "Low-cost, subsidiaria de Copa",
        "requires_javascript": False
    },
    {
        "nombre": "EasyFly",
        "codigo": "VE",
        "url_politicas": "https://www.easyfly.com.co/condiciones-generales",
        "url_terminos": None,
        "prioridad": "media",
        "notas": "Regional, rutas secundarias",
        "requires_javascript": False
    },
    {
        "nombre": "Satena",
        "codigo": "9R",
        "url_politicas": "https://www.satena.com/terminos-y-condiciones/",
        "url_terminos": None,
        "prioridad": "media",
        "notas": "Aerolínea estatal, rutas remotas",
        "requires_javascript": False
    },
    {
        "nombre": "Copa Airlines",
        "codigo": "CM",
        "url_politicas": "https://www.copaair.com/es/web/co/cambios-reembolsos",
        "url_terminos": None,
        "prioridad": "alta",
        "notas": "Hub en Panamá, muchos vuelos desde Colombia",
        "requires_javascript": False
    },
    {
        "nombre": "JetSmart",
        "codigo": "JA",
        "url_politicas": "https://jetsmart.com/co/es/condiciones-de-transporte",
        "url_terminos": None,
        "prioridad": "baja",
        "notas": "Low-cost chilena operando en Colombia",
        "requires_javascript": False
    }
]

# Campos críticos que deben extraerse
CRITICAL_FIELDS = [
    'allows_full_name_change',
    'allows_name_correction',
    'allows_transfer_to_third_party',
    'cost_name_change_domestic_cop',
]

# Campos importantes (nice to have)
IMPORTANT_FIELDS = [
    'allows_cancellation',
    'cancellation_cost_cop',
    'refund_percentage',
    'time_restrictions',
]

# Umbrales de confianza
CONFIDENCE_THRESHOLD_HIGH = 0.8  # Alta confianza
CONFIDENCE_THRESHOLD_MEDIUM = 0.5  # Confianza media
CONFIDENCE_THRESHOLD_LOW = 0.3  # Baja confianza

# Criterios de viabilidad del marketplace
VIABILITY_THRESHOLDS = {
    "market_coverage_minimum": 40.0,  # % mínimo de aerolíneas que deben permitir transferencia
    "market_coverage_ideal": 60.0,    # % ideal de cobertura
    "max_acceptable_cost_cop": 200000,  # Costo máximo aceptable para transferencia
    "min_airlines_needed": 3,           # Mínimo de aerolíneas viables
}

# Headers HTTP por defecto
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

# Nombres de archivos de salida
OUTPUT_FILES = {
    "csv": EXPORTS_DIR / "policies.csv",
    "json": EXPORTS_DIR / "policies.json",
    "excel": EXPORTS_DIR / "policies.xlsx",
    "markdown": EXPORTS_DIR / "REPORTE_VIABILIDAD.md",
}

# Configuración de gráficos
CHART_CONFIG = {
    "style": "seaborn-v0_8-darkgrid",
    "figsize": (12, 8),
    "dpi": CHART_DPI,
    "color_palette": "husl",
}

# Mensajes de log
LOG_MESSAGES = {
    "scrape_start": "🚀 Iniciando scrape de {airline}",
    "scrape_success": "✅ Datos extraídos correctamente de {airline}",
    "scrape_warning": "⚠️ Requiere revisión manual: {reason}",
    "scrape_error": "❌ Error al scrapear {airline}: {error}",
    "all_complete": "📊 {count} aerolíneas procesadas",
}
