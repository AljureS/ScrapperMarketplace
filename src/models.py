"""
Modelos de datos para políticas de aerolíneas
Define las estructuras de datos usando dataclasses
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List
from datetime import datetime


@dataclass
class AirlinePolicy:
    """
    Representa las políticas de una aerolínea respecto a cambios,
    cancelaciones y transferencias de boletos.
    """

    # Información básica de la aerolínea
    airline_name: str
    airline_code: str

    # Políticas críticas de cambio de nombre
    allows_full_name_change: Optional[bool] = None
    allows_name_correction: Optional[bool] = None
    cost_name_change_domestic_cop: Optional[int] = None
    cost_name_change_intl_cop: Optional[int] = None
    cost_name_change_usd: Optional[float] = None

    # Políticas de transferencia
    allows_transfer_to_third_party: Optional[bool] = None
    transfer_process_description: Optional[str] = None

    # Políticas de cancelación
    allows_cancellation: Optional[bool] = None
    cancellation_cost_cop: Optional[int] = None
    refund_percentage: Optional[int] = None

    # Restricciones y condiciones
    time_restrictions: Optional[str] = None
    fare_type_differences: Optional[str] = None
    max_change_deadline: Optional[str] = None

    # Información de contacto y soporte
    terms_url: Optional[str] = None
    support_phone: Optional[str] = None
    support_email: Optional[str] = None

    # Documentación y excepciones
    required_documentation: Optional[str] = None  # JSON string o lista separada por comas
    notable_exceptions: Optional[str] = None

    # Metadatos de scraping
    source_url: Optional[str] = None
    scraped_at: datetime = field(default_factory=datetime.now)
    raw_html_hash: Optional[str] = None

    # Control de calidad
    requires_manual_review: bool = False
    manual_review_notes: Optional[str] = None
    confidence_score: float = 0.0  # 0.0 a 1.0, indica confianza en los datos extraídos

    def to_dict(self) -> dict:
        """Convierte la política a diccionario"""
        data = asdict(self)
        # Convertir datetime a string
        if isinstance(data['scraped_at'], datetime):
            data['scraped_at'] = data['scraped_at'].isoformat()
        return data

    def to_db_tuple(self) -> tuple:
        """
        Convierte la política a tupla para inserción en base de datos
        Sigue el orden de las columnas en el schema
        """
        return (
            self.airline_name,
            self.airline_code,
            self.allows_full_name_change,
            self.allows_name_correction,
            self.cost_name_change_domestic_cop,
            self.cost_name_change_intl_cop,
            self.cost_name_change_usd,
            self.allows_transfer_to_third_party,
            self.transfer_process_description,
            self.allows_cancellation,
            self.cancellation_cost_cop,
            self.refund_percentage,
            self.time_restrictions,
            self.fare_type_differences,
            self.max_change_deadline,
            self.terms_url,
            self.support_phone,
            self.support_email,
            self.required_documentation,
            self.notable_exceptions,
            self.source_url,
            self.scraped_at.isoformat() if self.scraped_at else None,
            self.raw_html_hash,
            self.requires_manual_review,
            self.manual_review_notes
        )

    def is_transfer_viable(self) -> bool:
        """
        Determina si la aerolínea es viable para un marketplace de reventa
        basado en políticas de transferencia
        """
        # Viable si permite cambio completo de nombre O transferencia a terceros
        return (
            self.allows_full_name_change is True or
            self.allows_transfer_to_third_party is True
        )

    def get_viability_score(self) -> float:
        """
        Calcula un score de viabilidad (0.0 a 1.0)
        Score más alto = más viable para marketplace
        """
        score = 0.0

        # Peso por permitir transferencia (50% del score)
        if self.allows_transfer_to_third_party is True:
            score += 0.5
        elif self.allows_full_name_change is True:
            score += 0.3
        elif self.allows_name_correction is True:
            score += 0.1

        # Peso por costos razonables (30% del score)
        if self.cost_name_change_domestic_cop:
            if self.cost_name_change_domestic_cop < 50000:
                score += 0.3
            elif self.cost_name_change_domestic_cop < 100000:
                score += 0.2
            elif self.cost_name_change_domestic_cop < 200000:
                score += 0.1

        # Peso por facilidad de proceso (20% del score)
        if self.transfer_process_description:
            # Si hay descripción de proceso, asumimos que es posible
            score += 0.2

        return min(score, 1.0)  # Cap a 1.0

    def get_missing_fields(self) -> List[str]:
        """Retorna lista de campos críticos que faltan"""
        missing = []
        critical_fields = [
            'allows_full_name_change',
            'allows_name_correction',
            'allows_transfer_to_third_party',
            'cost_name_change_domestic_cop',
        ]

        for field_name in critical_fields:
            if getattr(self, field_name) is None:
                missing.append(field_name)

        return missing


@dataclass
class ScrapingResult:
    """
    Resultado de un intento de scraping
    Incluye la política extraída y metadatos del proceso
    """
    airline_name: str
    success: bool
    policy: Optional[AirlinePolicy] = None
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    execution_time_seconds: float = 0.0

    def __str__(self) -> str:
        status = "✅ Éxito" if self.success else "❌ Error"
        return f"{status} - {self.airline_name} ({self.execution_time_seconds:.2f}s)"


@dataclass
class ViabilityReport:
    """
    Reporte de viabilidad del marketplace
    Contiene métricas agregadas y conclusiones
    """
    total_airlines: int
    scraped_successfully: int
    allow_transfer: int
    allow_name_change: int
    allow_name_correction_only: int

    avg_cost_domestic_cop: Optional[float] = None
    min_cost_domestic_cop: Optional[int] = None
    max_cost_domestic_cop: Optional[int] = None

    viable_airlines: List[str] = field(default_factory=list)
    non_viable_airlines: List[str] = field(default_factory=list)

    market_coverage_percentage: float = 0.0
    overall_viability_score: float = 0.0

    conclusion: str = ""
    recommendation: str = ""

    generated_at: datetime = field(default_factory=datetime.now)

    def is_viable(self) -> bool:
        """
        Determina si el marketplace es viable
        Criterio: Al menos 40% del mercado (3 de 7 aerolíneas) permite transferencia
        """
        return self.market_coverage_percentage >= 40.0

    def get_viability_status(self) -> str:
        """Retorna el estado de viabilidad en formato legible"""
        if self.market_coverage_percentage >= 60:
            return "✅ VIABLE"
        elif self.market_coverage_percentage >= 40:
            return "⚠️ VIABLE CON RESTRICCIONES"
        else:
            return "❌ NO VIABLE"
