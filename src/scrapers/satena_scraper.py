"""
Scraper específico para Satena
"""

from datetime import datetime
from src.scrapers.base_scraper import BaseScraper
from src.models import AirlinePolicy
from src.utils import (
    extract_cop_amount, extract_usd_amount, extract_percentage,
    detect_boolean_policy, extract_sentences_with_keywords,
    extract_phone, extract_email, compute_html_hash, clean_text
)


class SatenaScraper(BaseScraper):
    """Scraper específico para Satena"""

    def __init__(self):
        super().__init__(
            airline_name="Satena",
            airline_code="9R",
            base_url="https://www.satena.com",
            policies_url="https://www.satena.com/terminos-y-condiciones/",
            requires_javascript=False
        )

    def extract_data(self) -> AirlinePolicy:
        """Extrae datos de políticas de Satena"""
        policy = AirlinePolicy(
            airline_name=self.airline_name,
            airline_code=self.airline_code,
            source_url=self.policies_url,
            scraped_at=datetime.now(),
            raw_html_hash=compute_html_hash(self.html_content)
        )

        page_text = self.soup.get_text(separator=' ', strip=True)

        transfer_keywords = ['cambio de nombre', 'modificar nombre', 'cambio de pasajero']
        cancellation_keywords = ['cancelación', 'reembolso', 'devolución']

        transfer_sections = extract_sentences_with_keywords(page_text, transfer_keywords, 2)
        cancellation_sections = extract_sentences_with_keywords(page_text, cancellation_keywords, 2)

        if transfer_sections:
            transfer_text = ' '.join(transfer_sections)
            allows_change, _ = detect_boolean_policy(transfer_text)
            policy.allows_full_name_change = allows_change
            policy.allows_name_correction = 'corrección' in transfer_text.lower()
            policy.cost_name_change_domestic_cop = extract_cop_amount(transfer_text)
            policy.allows_transfer_to_third_party = allows_change
            policy.transfer_process_description = clean_text(transfer_text[:500])

        if cancellation_sections:
            cancellation_text = ' '.join(cancellation_sections)
            allows_cancel, _ = detect_boolean_policy(cancellation_text)
            policy.allows_cancellation = allows_cancel
            policy.cancellation_cost_cop = extract_cop_amount(cancellation_text)
            policy.refund_percentage = extract_percentage(cancellation_text)

        policy.support_phone = extract_phone(page_text)
        policy.support_email = extract_email(page_text)
        policy.terms_url = self.policies_url
        policy.notable_exceptions = "Aerolínea estatal, rutas a zonas remotas"

        return policy
