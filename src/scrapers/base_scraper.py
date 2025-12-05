"""
Clase base abstracta para todos los scrapers de aerolíneas
Define la interfaz común y funcionalidad compartida
"""

import time
import logging
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

from src.models import AirlinePolicy, ScrapingResult
from src.config import (
    USER_AGENTS, DEFAULT_HEADERS, REQUEST_TIMEOUT,
    MAX_RETRIES, RETRY_BACKOFF, SNAPSHOTS_DIR
)
from src.utils import (
    compute_html_hash, get_random_delay, get_random_user_agent,
    format_timestamp, setup_logger
)
from src.database import DatabaseManager


class BaseScraper(ABC):
    """
    Clase abstracta base para scrapers de aerolíneas
    Todos los scrapers específicos deben heredar de esta clase
    """

    def __init__(
        self,
        airline_name: str,
        airline_code: str,
        base_url: str,
        policies_url: str,
        requires_javascript: bool = False
    ):
        """
        Inicializa el scraper base

        Args:
            airline_name: Nombre completo de la aerolínea
            airline_code: Código IATA de la aerolínea
            base_url: URL base del sitio web
            policies_url: URL de la página de políticas
            requires_javascript: Si requiere navegador para JS
        """
        self.airline_name = airline_name
        self.airline_code = airline_code
        self.base_url = base_url
        self.policies_url = policies_url
        self.requires_javascript = requires_javascript

        # Configurar logger específico para esta aerolínea
        self.logger = setup_logger(
            f"scraper.{airline_code}",
            f"logs/scraper_{airline_code}.log"
        )

        # Database manager
        self.db = DatabaseManager()

        # Almacenar contenido HTML
        self.html_content: Optional[str] = None
        self.soup: Optional[BeautifulSoup] = None

    def scrape(self) -> ScrapingResult:
        """
        Método principal que orquesta el proceso de scraping

        Returns:
            ScrapingResult con el resultado del scraping
        """
        start_time = time.time()
        self.logger.info(f"🚀 Iniciando scrape de {self.airline_name}")

        try:
            # 1. Obtener contenido HTML
            self.logger.info(f"Descargando página: {self.policies_url}")
            self.html_content = self.fetch_page(self.policies_url)

            if not self.html_content:
                raise Exception("No se pudo obtener contenido HTML")

            # 2. Parsear HTML con BeautifulSoup
            self.soup = BeautifulSoup(self.html_content, 'lxml')

            # 3. Guardar snapshot
            self.save_snapshot()

            # 4. Extraer datos (método abstracto, implementado por cada scraper)
            self.logger.info("Extrayendo datos de políticas...")
            policy = self.extract_data()

            # 5. Validar datos extraídos
            validation_result = self.validate_extracted_data(policy)

            if not validation_result['is_valid']:
                policy.requires_manual_review = True
                policy.manual_review_notes = "; ".join(validation_result['errors'])
                self.logger.warning(
                    f"⚠️ Datos requieren revisión manual: {validation_result['errors']}"
                )

            # 6. Calcular confidence score
            policy.confidence_score = self.calculate_confidence_score(policy)

            # 7. Guardar en base de datos
            self.db.insert_policy(policy)

            # 8. Detectar cambios
            if self.detect_policy_changes(policy):
                self.logger.info("📝 Se detectaron cambios en las políticas")

            execution_time = time.time() - start_time

            self.logger.info(
                f"✅ Scraping de {self.airline_name} completado en {execution_time:.2f}s"
            )

            return ScrapingResult(
                airline_name=self.airline_name,
                success=True,
                policy=policy,
                execution_time_seconds=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)

            self.logger.error(f"❌ Error al scrapear {self.airline_name}: {error_msg}")

            return ScrapingResult(
                airline_name=self.airline_name,
                success=False,
                error_message=error_msg,
                execution_time_seconds=execution_time
            )

    def fetch_page(self, url: str) -> Optional[str]:
        """
        Obtiene el contenido HTML de una página con reintentos

        Args:
            url: URL a descargar

        Returns:
            Contenido HTML o None si falla
        """
        for attempt in range(MAX_RETRIES):
            try:
                # Rate limiting - esperar antes del request
                if attempt > 0:
                    wait_time = RETRY_BACKOFF ** attempt
                    self.logger.info(f"Reintento {attempt + 1}/{MAX_RETRIES} en {wait_time}s")
                    time.sleep(wait_time)
                else:
                    time.sleep(get_random_delay())

                # Preparar headers con User-Agent rotado
                headers = DEFAULT_HEADERS.copy()
                headers['User-Agent'] = get_random_user_agent(USER_AGENTS)

                # Hacer request
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True
                )

                response.raise_for_status()

                # Verificar si es CAPTCHA o bloqueo
                if self._detect_captcha(response.text):
                    self.logger.warning("⚠️ CAPTCHA detectado - requiere revisión manual")
                    # Continuar de todas formas, el scraper específico manejará esto
                    return response.text

                return response.text

            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Intento {attempt + 1} falló: {e}")

                if attempt == MAX_RETRIES - 1:
                    self.logger.error(f"Falló después de {MAX_RETRIES} intentos")
                    return None

        return None

    @abstractmethod
    def extract_data(self) -> AirlinePolicy:
        """
        Método abstracto que debe ser implementado por cada scraper
        Extrae los datos específicos de la aerolínea

        Returns:
            AirlinePolicy con los datos extraídos
        """
        pass

    def parse_costs(self, text: str) -> Dict[str, Any]:
        """
        Parsea costos de un texto (puede ser sobrescrito por scrapers específicos)

        Args:
            text: Texto a parsear

        Returns:
            Diccionario con costos extraídos
        """
        from src.utils import extract_cop_amount, extract_usd_amount

        return {
            'cop': extract_cop_amount(text),
            'usd': extract_usd_amount(text)
        }

    def detect_policy_changes(self, new_policy: AirlinePolicy) -> bool:
        """
        Detecta si las políticas han cambiado desde el último scraping

        Args:
            new_policy: Nueva política scrapeada

        Returns:
            True si hay cambios, False si no
        """
        old_policy = self.db.get_policy_by_code(self.airline_code)

        if not old_policy:
            return True  # Es la primera vez

        # Comparar hashes
        if old_policy.raw_html_hash != new_policy.raw_html_hash:
            self.logger.info("Hash diferente - contenido cambió")
            return True

        return False

    def save_snapshot(self) -> None:
        """
        Guarda un snapshot del HTML descargado
        """
        if not self.html_content:
            return

        try:
            timestamp = format_timestamp()
            filename = f"{self.airline_code}_{timestamp}.html"
            filepath = SNAPSHOTS_DIR / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.html_content)

            self.logger.info(f"Snapshot guardado: {filename}")

        except Exception as e:
            self.logger.error(f"Error al guardar snapshot: {e}")

    def validate_extracted_data(self, policy: AirlinePolicy) -> Dict[str, Any]:
        """
        Valida los datos extraídos

        Args:
            policy: Política a validar

        Returns:
            Diccionario con resultado de validación
        """
        from src.utils import (
            validate_cop_amount, validate_usd_amount,
            validate_percentage, validate_url
        )

        errors = []

        # Validar costos
        if not validate_cop_amount(policy.cost_name_change_domestic_cop):
            errors.append("Costo doméstico COP fuera de rango")

        if not validate_usd_amount(policy.cost_name_change_usd):
            errors.append("Costo USD fuera de rango")

        if not validate_percentage(policy.refund_percentage):
            errors.append("Porcentaje de reembolso inválido")

        # Validar URLs
        if not validate_url(policy.terms_url):
            errors.append("URL de términos inválida")

        if not validate_url(policy.source_url):
            errors.append("URL de origen inválida")

        # Verificar campos críticos
        critical_missing = policy.get_missing_fields()
        if len(critical_missing) > 3:
            errors.append(f"Faltan campos críticos: {', '.join(critical_missing)}")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }

    def calculate_confidence_score(self, policy: AirlinePolicy) -> float:
        """
        Calcula un score de confianza en los datos extraídos

        Args:
            policy: Política extraída

        Returns:
            Score de 0.0 a 1.0
        """
        score = 0.0
        total_fields = 0
        filled_fields = 0

        # Campos críticos (peso mayor)
        critical_fields = [
            'allows_full_name_change',
            'allows_name_correction',
            'allows_transfer_to_third_party',
            'cost_name_change_domestic_cop'
        ]

        for field in critical_fields:
            total_fields += 2  # Peso doble para campos críticos
            if getattr(policy, field) is not None:
                filled_fields += 2

        # Campos importantes
        important_fields = [
            'allows_cancellation',
            'cancellation_cost_cop',
            'refund_percentage',
            'time_restrictions'
        ]

        for field in important_fields:
            total_fields += 1
            if getattr(policy, field) is not None:
                filled_fields += 1

        if total_fields > 0:
            score = filled_fields / total_fields

        return round(score, 2)

    def _detect_captcha(self, html_content: str) -> bool:
        """
        Detecta si la página contiene un CAPTCHA

        Args:
            html_content: Contenido HTML

        Returns:
            True si se detecta CAPTCHA, False si no
        """
        captcha_indicators = [
            'recaptcha',
            'captcha',
            'g-recaptcha',
            'cloudflare',
            'cf-browser-verification',
            'human verification'
        ]

        html_lower = html_content.lower()

        for indicator in captcha_indicators:
            if indicator in html_lower:
                return True

        return False

    def needs_manual_review(self, policy: AirlinePolicy) -> bool:
        """
        Determina si una política requiere revisión manual

        Args:
            policy: Política a revisar

        Returns:
            True si requiere revisión, False si no
        """
        # Revisar si tiene muchos campos vacíos
        missing_critical = len(policy.get_missing_fields())

        if missing_critical > 2:
            return True

        # Revisar si el confidence score es muy bajo
        if policy.confidence_score < 0.4:
            return True

        return False

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self.airline_name} ({self.airline_code})>"
