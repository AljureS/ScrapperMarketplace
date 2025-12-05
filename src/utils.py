"""
Utilidades y funciones auxiliares para el scraper
Incluye regex patterns, parsers, validadores y helpers
"""

import re
import hashlib
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import random


# ============================================================================
# REGEX PATTERNS
# ============================================================================

# Patrones para extraer costos en pesos colombianos
REGEX_COSTOS_COP = [
    r'\$\s*([\d,.]+)\s*(?:COP|pesos)',
    r'([\d,.]+)\s*pesos\s+colombianos',
    r'valor(?:\s+de)?\s+\$?\s*([\d,.]+)',
    r'\$\s*([\d,.]+)(?:\s|$)',
    r'([\d,.]+)\s*COP',
]

# Patrones para extraer costos en dólares
REGEX_COSTOS_USD = [
    r'USD?\s*\$?\s*([\d,.]+)',
    r'\$\s*([\d,.]+)\s*(?:USD|dólares|dolares)',
    r'([\d,.]+)\s*dólares?',
]

# Patrones para extraer porcentajes
REGEX_PORCENTAJES = [
    r'([\d]+)\s*%',
    r'([\d]+)\s*por\s*ciento',
]

# Patrones para extraer tiempo
REGEX_TIEMPO = [
    r'(\d+)\s*(?:hora|hr|h)s?',
    r'(\d+)\s*días?',
    r'(\d+)\s*semanas?',
]

# Palabras clave negativas (indican que NO se permite algo)
KEYWORDS_NEGATIVE = [
    r'no\s+(?:se\s+)?permite',
    r'no\s+(?:es\s+)?posible',
    r'no\s+(?:se\s+)?autoriza',
    r'imposible',
    r'prohibido',
    r'no\s+(?:se\s+)?puede',
    r'no\s+(?:es\s+)?permitido',
    r'no\s+reembolsable',
]

# Palabras clave positivas (indican que SÍ se permite algo)
KEYWORDS_POSITIVE = [
    r'permite',
    r'posible',
    r'puede',
    r'autorizado',
    r'permitido',
    r'disponible',
    r'se\s+acepta',
]


# ============================================================================
# FUNCIONES DE PARSING
# ============================================================================

def extract_cop_amount(text: str) -> Optional[int]:
    """
    Extrae cantidad en pesos colombianos de un texto
    Retorna: entero con el monto o None si no encuentra
    """
    if not text:
        return None

    text = text.strip()

    for pattern in REGEX_COSTOS_COP:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Tomar el primer match y limpiar
            amount_str = matches[0].replace(',', '').replace('.', '')
            try:
                return int(amount_str)
            except ValueError:
                continue

    return None


def extract_usd_amount(text: str) -> Optional[float]:
    """
    Extrae cantidad en dólares de un texto
    Retorna: float con el monto o None si no encuentra
    """
    if not text:
        return None

    text = text.strip()

    for pattern in REGEX_COSTOS_USD:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            amount_str = matches[0].replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                continue

    return None


def extract_percentage(text: str) -> Optional[int]:
    """
    Extrae porcentaje de un texto
    Retorna: entero con el porcentaje o None si no encuentra
    """
    if not text:
        return None

    for pattern in REGEX_PORCENTAJES:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                return int(matches[0])
            except ValueError:
                continue

    return None


def detect_boolean_policy(text: str, keywords: List[str] = None) -> Tuple[Optional[bool], float]:
    """
    Detecta si un texto indica una política positiva o negativa
    Retorna: (bool, confidence_score)
    - True: política permite la acción
    - False: política no permite la acción
    - None: no se pudo determinar
    - confidence_score: 0.0 a 1.0
    """
    if not text:
        return None, 0.0

    text = text.lower().strip()

    # Contar matches positivos y negativos
    positive_matches = 0
    negative_matches = 0

    for pattern in KEYWORDS_POSITIVE:
        if re.search(pattern, text, re.IGNORECASE):
            positive_matches += 1

    for pattern in KEYWORDS_NEGATIVE:
        if re.search(pattern, text, re.IGNORECASE):
            negative_matches += 1

    # Si hay keywords específicos, buscarlos también
    if keywords:
        for keyword in keywords:
            if keyword.lower() in text:
                positive_matches += 1

    # Determinar resultado
    if positive_matches > negative_matches:
        confidence = min(positive_matches / (positive_matches + negative_matches + 1), 0.9)
        return True, confidence
    elif negative_matches > positive_matches:
        confidence = min(negative_matches / (positive_matches + negative_matches + 1), 0.9)
        return False, confidence
    else:
        return None, 0.0


def extract_phone(text: str) -> Optional[str]:
    """
    Extrae número de teléfono de un texto
    Formatos: +57 601 123 4567, 601-123-4567, etc.
    """
    if not text:
        return None

    patterns = [
        r'\+?\d{1,3}[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{4}',
        r'\d{3}[\s-]\d{3}[\s-]\d{4}',
        r'\d{10,}',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)

    return None


def extract_email(text: str) -> Optional[str]:
    """
    Extrae dirección de email de un texto
    """
    if not text:
        return None

    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)

    if match:
        return match.group(0)

    return None


def extract_urls(text: str) -> List[str]:
    """
    Extrae todas las URLs de un texto
    """
    if not text:
        return []

    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(pattern, text)


# ============================================================================
# FUNCIONES DE VALIDACIÓN
# ============================================================================

def validate_cop_amount(amount: Optional[int]) -> bool:
    """Valida que un monto en COP sea razonable"""
    if amount is None:
        return True  # None es válido (campo opcional)
    return 0 <= amount <= 10_000_000  # Max 10 millones COP


def validate_usd_amount(amount: Optional[float]) -> bool:
    """Valida que un monto en USD sea razonable"""
    if amount is None:
        return True
    return 0 <= amount <= 5000  # Max 5000 USD


def validate_percentage(percentage: Optional[int]) -> bool:
    """Valida que un porcentaje esté en rango válido"""
    if percentage is None:
        return True
    return 0 <= percentage <= 100


def validate_url(url: Optional[str]) -> bool:
    """Valida que una URL tenga formato correcto"""
    if not url:
        return True

    pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
    return bool(re.match(pattern, url))


# ============================================================================
# FUNCIONES DE HASH Y TRACKING
# ============================================================================

def compute_html_hash(html_content: str) -> str:
    """
    Calcula hash MD5 del contenido HTML
    Útil para detectar cambios en las políticas
    """
    if not html_content:
        return ""

    return hashlib.md5(html_content.encode('utf-8')).hexdigest()


def has_content_changed(new_hash: str, old_hash: Optional[str]) -> bool:
    """
    Determina si el contenido ha cambiado comparando hashes
    """
    if not old_hash:
        return True  # Primera vez, consideramos que es nuevo
    return new_hash != old_hash


# ============================================================================
# FUNCIONES DE TEXTO
# ============================================================================

def clean_text(text: str) -> str:
    """
    Limpia texto removiendo espacios extras, saltos de línea, etc.
    """
    if not text:
        return ""

    # Remover múltiples espacios
    text = re.sub(r'\s+', ' ', text)
    # Remover espacios al inicio y final
    text = text.strip()
    return text


def extract_sentences_with_keywords(text: str, keywords: List[str], context_sentences: int = 1) -> List[str]:
    """
    Extrae oraciones que contienen ciertas palabras clave
    Útil para encontrar secciones relevantes en textos largos
    """
    if not text or not keywords:
        return []

    # Dividir en oraciones
    sentences = re.split(r'[.!?]+', text)
    relevant_sentences = []

    for i, sentence in enumerate(sentences):
        sentence_lower = sentence.lower()

        # Verificar si contiene alguna keyword
        if any(keyword.lower() in sentence_lower for keyword in keywords):
            # Agregar contexto (oraciones anteriores y posteriores)
            start = max(0, i - context_sentences)
            end = min(len(sentences), i + context_sentences + 1)

            context = ' '.join(sentences[start:end])
            relevant_sentences.append(clean_text(context))

    return relevant_sentences


# ============================================================================
# FUNCIONES DE LOGGING
# ============================================================================

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """
    Configura un logger con formato personalizado
    """
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evitar duplicar handlers
    if logger.handlers:
        return logger

    # Formato
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para archivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# ============================================================================
# FUNCIONES DE UTILIDAD GENERAL
# ============================================================================

def get_random_delay(min_delay: float = 2.0, max_delay: float = 5.0) -> float:
    """
    Retorna un delay aleatorio para rate limiting
    """
    return random.uniform(min_delay, max_delay)


def get_random_user_agent(user_agents: List[str]) -> str:
    """
    Retorna un User-Agent aleatorio de la lista
    """
    return random.choice(user_agents)


def format_timestamp(dt: datetime = None) -> str:
    """
    Formatea un datetime para nombres de archivo
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y%m%d_%H%M%S")


def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Trunca texto a longitud máxima agregando '...'
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - 3] + "..."


def safe_get(dictionary: Dict, *keys, default=None) -> Any:
    """
    Obtiene valor anidado de diccionario de forma segura
    Ejemplo: safe_get(data, 'airline', 'policies', 'transfer', default=False)
    """
    result = dictionary
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return default

        if result is None:
            return default

    return result


def format_cop_amount(amount: Optional[int]) -> str:
    """
    Formatea cantidad en COP con separadores de miles
    Ejemplo: 150000 -> "$150,000 COP"
    """
    if amount is None:
        return "N/A"

    return f"${amount:,} COP".replace(',', '.')


def format_usd_amount(amount: Optional[float]) -> str:
    """
    Formatea cantidad en USD
    Ejemplo: 50.5 -> "$50.50 USD"
    """
    if amount is None:
        return "N/A"

    return f"${amount:.2f} USD"
