"""
Scraper específico para Avianca
Extrae políticas de cambio, cancelación y transferencia de boletos
"""

from datetime import datetime
from src.scrapers.base_scraper import BaseScraper
from src.models import AirlinePolicy
from src.utils import (
    extract_cop_amount, extract_usd_amount, extract_percentage,
    detect_boolean_policy, extract_sentences_with_keywords,
    extract_phone, extract_email, compute_html_hash, clean_text
)


class AviancaScraper(BaseScraper):
    """
    Scraper específico para extraer políticas de Avianca
    """

    def __init__(self):
        super().__init__(
            airline_name="Avianca",
            airline_code="AV",
            base_url="https://www.avianca.com",
            policies_url="https://www.avianca.com/co/es/experiencia/condiciones-transporte/",
            requires_javascript=False
        )

    def extract_data(self) -> AirlinePolicy:
        """
        Extrae datos específicos de las políticas de Avianca

        Returns:
            AirlinePolicy con datos extraídos
        """
        # Crear objeto de política
        policy = AirlinePolicy(
            airline_name=self.airline_name,
            airline_code=self.airline_code,
            source_url=self.policies_url,
            scraped_at=datetime.now(),
            raw_html_hash=compute_html_hash(self.html_content)
        )

        # Obtener todo el texto de la página
        page_text = self.soup.get_text(separator=' ', strip=True)

        # Keywords para buscar secciones relevantes
        transfer_keywords = [
            'cambio de nombre', 'transferencia', 'cambiar nombre',
            'modificación de nombre', 'cambio del pasajero'
        ]

        cancellation_keywords = [
            'cancelación', 'cancelar', 'reembolso', 'devolución'
        ]

        # Extraer secciones relevantes
        transfer_sections = extract_sentences_with_keywords(
            page_text, transfer_keywords, context_sentences=2
        )

        cancellation_sections = extract_sentences_with_keywords(
            page_text, cancellation_keywords, context_sentences=2
        )

        # Analizar políticas de transferencia/cambio de nombre
        if transfer_sections:
            transfer_text = ' '.join(transfer_sections)

            # Verificar si permite cambio de nombre completo
            allows_change, confidence = detect_boolean_policy(
                transfer_text,
                keywords=['puede cambiar', 'permite cambio', 'cambio de nombre']
            )
            policy.allows_full_name_change = allows_change

            # Verificar correcciones menores
            if 'corrección' in transfer_text.lower() or 'error tipográfico' in transfer_text.lower():
                policy.allows_name_correction = True
            else:
                policy.allows_name_correction = False

            # Extraer costos
            cop_cost = extract_cop_amount(transfer_text)
            if cop_cost:
                policy.cost_name_change_domestic_cop = cop_cost

            usd_cost = extract_usd_amount(transfer_text)
            if usd_cost:
                policy.cost_name_change_usd = usd_cost

            # Detectar si permite transferencia a terceros
            if 'transferir' in transfer_text.lower() or 'tercero' in transfer_text.lower():
                allows_transfer, _ = detect_boolean_policy(
                    transfer_text,
                    keywords=['transferir', 'transferencia']
                )
                policy.allows_transfer_to_third_party = allows_transfer
            else:
                # Si solo habla de "cambio de nombre", asumir que es similar a transferencia
                policy.allows_transfer_to_third_party = policy.allows_full_name_change

            # Descripción del proceso
            policy.transfer_process_description = clean_text(transfer_text[:500])

        # Analizar políticas de cancelación
        if cancellation_sections:
            cancellation_text = ' '.join(cancellation_sections)

            # Verificar si permite cancelación
            allows_cancel, _ = detect_boolean_policy(
                cancellation_text,
                keywords=['puede cancelar', 'permite cancelación']
            )
            policy.allows_cancellation = allows_cancel

            # Extraer costo de cancelación
            cancel_cost = extract_cop_amount(cancellation_text)
            if cancel_cost:
                policy.cancellation_cost_cop = cancel_cost

            # Extraer porcentaje de reembolso
            refund_pct = extract_percentage(cancellation_text)
            if refund_pct:
                policy.refund_percentage = refund_pct

        # Buscar información de contacto
        policy.support_phone = extract_phone(page_text)
        policy.support_email = extract_email(page_text)
        policy.terms_url = self.policies_url

        # Buscar restricciones temporales
        time_restrictions = self._extract_time_restrictions(page_text)
        if time_restrictions:
            policy.time_restrictions = time_restrictions

        # Buscar diferencias entre tarifas
        fare_differences = self._extract_fare_differences(page_text)
        if fare_differences:
            policy.fare_type_differences = fare_differences

        # Excepciones notables
        if 'no reembolsable' in page_text.lower():
            policy.notable_exceptions = "Algunas tarifas son no reembolsables"

        return policy

    def _extract_time_restrictions(self, text: str) -> str:
        """
        Extrae restricciones temporales del texto

        Args:
            text: Texto completo de la página

        Returns:
            String con restricciones de tiempo o None
        """
        time_patterns = [
            r'(\d+)\s*horas?\s+antes',
            r'(\d+)\s*días?\s+antes',
            r'hasta\s+(\d+)\s+horas?',
            r'hasta\s+(\d+)\s+días?',
        ]

        import re
        restrictions = []

        for pattern in time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                restrictions.extend(matches)

        if restrictions:
            return f"Restricciones encontradas: {', '.join(set(restrictions))}"

        return None

    def _extract_fare_differences(self, text: str) -> str:
        """
        Extrae información sobre diferencias entre tipos de tarifa

        Args:
            text: Texto completo de la página

        Returns:
            String con información de tarifas o None
        """
        fare_keywords = ['básica', 'flexible', 'business', 'económica', 'premium']
        fare_sections = extract_sentences_with_keywords(text, fare_keywords, context_sentences=1)

        if fare_sections:
            return clean_text(' '.join(fare_sections)[:300])

        return None
