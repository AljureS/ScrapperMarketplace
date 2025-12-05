"""
Generador de reporte markdown de viabilidad
Crea el documento REPORTE_VIABILIDAD.md con análisis completo
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from src.models import ViabilityReport, AirlinePolicy
from src.database import DatabaseManager
from src.analyzer import PolicyAnalyzer
from src.config import OUTPUT_FILES
from src.utils import format_cop_amount, format_usd_amount


logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Genera reporte markdown completo de viabilidad del marketplace
    """

    def __init__(self, db_manager: DatabaseManager = None):
        """
        Inicializa el generador de reportes

        Args:
            db_manager: Gestor de base de datos (opcional)
        """
        self.db = db_manager or DatabaseManager()
        self.analyzer = PolicyAnalyzer(self.db)

    def generate_full_report(self, output_path: Path = None) -> Path:
        """
        Genera el reporte completo de viabilidad

        Args:
            output_path: Ruta del archivo de salida (opcional)

        Returns:
            Ruta del archivo generado
        """
        if output_path is None:
            output_path = OUTPUT_FILES['markdown']

        logger.info("Generando reporte markdown de viabilidad...")

        # Cargar datos y generar análisis
        self.analyzer.load_data()
        stats = self.analyzer.generate_statistics()
        viability_report = self.analyzer.generate_viability_report()
        policies = self.db.get_all_policies()

        # Construir contenido del reporte
        content = []

        # 1. Portada
        content.append(self._generate_cover(viability_report))

        # 2. Conclusión de Viabilidad
        content.append(self._generate_viability_conclusion(viability_report))

        # 3. Hallazgos Clave
        content.append(self._generate_key_findings(viability_report, stats))

        # 4. Matriz Comparativa
        content.append(self._generate_comparison_matrix(policies))

        # 5. Análisis por Aerolínea
        content.append(self._generate_airline_analysis(policies))

        # 6. Análisis Estadístico
        content.append(self._generate_statistical_analysis(stats))

        # 7. Oportunidades Identificadas
        content.append(self._generate_opportunities(viability_report, policies))

        # 8. Modelos de Negocio Alternativos
        content.append(self._generate_business_models(viability_report))

        # 9. Proyección Financiera
        content.append(self._generate_financial_projection(viability_report, stats))

        # 10. Próximos Pasos
        content.append(self._generate_next_steps(viability_report))

        # 11. Apéndices
        content.append(self._generate_appendices(policies, stats))

        # Escribir archivo
        full_content = '\n\n'.join(content)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        logger.info(f"✅ Reporte generado: {output_path}")

        return output_path

    def _generate_cover(self, report: ViabilityReport) -> str:
        """Genera la portada del reporte"""
        return f"""# 📊 Reporte de Viabilidad: Marketplace de Reventa de Boletos Aéreos en Colombia

**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Versión:** 1.0

---

## 📋 Resumen Ejecutivo

Este reporte presenta un análisis exhaustivo de la viabilidad de crear un marketplace de reventa
de boletos aéreos en Colombia, basado en el scraping y análisis de políticas de {report.total_airlines}
aerolíneas que operan en el país.

**Conclusión Principal:** {report.get_viability_status()}

**Cobertura del Mercado:** {report.market_coverage_percentage}% de aerolíneas permiten transferencia/cambio de nombre

**Aerolíneas Viables:** {len(report.viable_airlines)} de {report.total_airlines}

---
"""

    def _generate_viability_conclusion(self, report: ViabilityReport) -> str:
        """Genera la sección de conclusión de viabilidad"""
        status_icon = "✅" if report.is_viable() else ("⚠️" if report.market_coverage_percentage >= 40 else "❌")

        return f"""## 🎯 Conclusión de Viabilidad

### {status_icon} Estado: {report.get_viability_status()}

**Score de Viabilidad:** {report.overall_viability_score:.2f} / 1.0

### Análisis

{report.conclusion}

### Recomendación

{report.recommendation}

---
"""

    def _generate_key_findings(self, report: ViabilityReport, stats: Dict) -> str:
        """Genera la sección de hallazgos clave"""
        return f"""## 🔑 Hallazgos Clave

### Métricas Principales

- **Aerolíneas Analizadas:** {report.total_airlines}
- **Scraping Exitoso:** {report.scraped_successfully} aerolíneas
- **Permiten Transferencia a Terceros:** {report.allow_transfer} aerolíneas ({report.allow_transfer/report.total_airlines*100:.1f}%)
- **Permiten Cambio de Nombre Completo:** {report.allow_name_change} aerolíneas ({report.allow_name_change/report.total_airlines*100:.1f}%)
- **Solo Permiten Correcciones Menores:** {report.allow_name_correction_only} aerolíneas

### Costos

- **Costo Promedio (Doméstico):** {format_cop_amount(report.avg_cost_domestic_cop)}
- **Rango de Costos:** {format_cop_amount(report.min_cost_domestic_cop)} - {format_cop_amount(report.max_cost_domestic_cop)}
- **Mediana de Costos:** {format_cop_amount(stats.get('median_cost_domestic_cop'))}

### Cobertura del Mercado

El {report.market_coverage_percentage}% del mercado es viable para un marketplace de reventa.

**Aerolíneas Viables:**
{self._format_list(report.viable_airlines)}

**Aerolíneas No Viables:**
{self._format_list(report.non_viable_airlines)}

---
"""

    def _generate_comparison_matrix(self, policies: List[AirlinePolicy]) -> str:
        """Genera matriz comparativa de políticas"""
        # Crear tabla markdown
        table = """## 📋 Matriz Comparativa de Políticas

| Aerolínea | Cambio Nombre | Corrección | Transferencia | Costo (COP) | Cancelación | Reembolso |
|-----------|---------------|------------|---------------|-------------|-------------|-----------|
"""

        for policy in policies:
            name = policy.airline_name
            name_change = "✅" if policy.allows_full_name_change else ("❌" if policy.allows_full_name_change is False else "❓")
            correction = "✅" if policy.allows_name_correction else ("❌" if policy.allows_name_correction is False else "❓")
            transfer = "✅" if policy.allows_transfer_to_third_party else ("❌" if policy.allows_transfer_to_third_party is False else "❓")
            cost = format_cop_amount(policy.cost_name_change_domestic_cop)
            cancellation = "✅" if policy.allows_cancellation else ("❌" if policy.allows_cancellation is False else "❓")
            refund = f"{policy.refund_percentage}%" if policy.refund_percentage else "N/A"

            table += f"| {name} | {name_change} | {correction} | {transfer} | {cost} | {cancellation} | {refund} |\n"

        table += "\n**Leyenda:** ✅ = Sí permite | ❌ = No permite | ❓ = No determinado\n\n---\n"

        return table

    def _generate_airline_analysis(self, policies: List[AirlinePolicy]) -> str:
        """Genera análisis detallado por aerolínea"""
        content = "## 🔍 Análisis Detallado por Aerolínea\n\n"

        for policy in policies:
            viability_score = policy.get_viability_score()
            viability_status = "✅ VIABLE" if viability_score >= 0.5 else "❌ NO VIABLE"

            content += f"""### {policy.airline_name} ({policy.airline_code})

**Status:** {viability_status} (Score: {viability_score:.2f})

**Políticas de Transferencia:**
- Permite cambio de nombre completo: {'✅ Sí' if policy.allows_full_name_change else '❌ No' if policy.allows_full_name_change is False else '❓ No determinado'}
- Permite corrección de nombre: {'✅ Sí' if policy.allows_name_correction else '❌ No' if policy.allows_name_correction is False else '❓ No determinado'}
- Permite transferencia a terceros: {'✅ Sí' if policy.allows_transfer_to_third_party else '❌ No' if policy.allows_transfer_to_third_party is False else '❓ No determinado'}

**Costos:**
- Vuelos domésticos: {format_cop_amount(policy.cost_name_change_domestic_cop)}
- Vuelos internacionales: {format_cop_amount(policy.cost_name_change_intl_cop)}
- En USD: {format_usd_amount(policy.cost_name_change_usd)}

**Políticas de Cancelación:**
- Permite cancelación: {'✅ Sí' if policy.allows_cancellation else '❌ No' if policy.allows_cancellation is False else '❓ No determinado'}
- Costo de cancelación: {format_cop_amount(policy.cancellation_cost_cop)}
- Porcentaje de reembolso: {policy.refund_percentage}% if policy.refund_percentage else 'N/A'

**Restricciones:**
{policy.time_restrictions if policy.time_restrictions else 'No especificadas'}

**Proceso de Transferencia:**
{policy.transfer_process_description[:300] + '...' if policy.transfer_process_description and len(policy.transfer_process_description) > 300 else (policy.transfer_process_description or 'No especificado')}

**Contacto:**
- Teléfono: {policy.support_phone or 'N/A'}
- Email: {policy.support_email or 'N/A'}
- Términos: {policy.terms_url or 'N/A'}

**Excepciones Notables:**
{policy.notable_exceptions or 'Ninguna'}

{'⚠️ **Requiere Revisión Manual:** ' + policy.manual_review_notes if policy.requires_manual_review else ''}

---

"""

        return content

    def _generate_statistical_analysis(self, stats: Dict) -> str:
        """Genera sección de análisis estadístico"""
        return f"""## 📈 Análisis Estadístico

### Distribución de Políticas

- **Total de aerolíneas analizadas:** {stats['total_airlines']}
- **Permiten transferencia:** {stats['allow_transfer']} ({stats['allow_transfer']/stats['total_airlines']*100:.1f}%)
- **Permiten cambio de nombre:** {stats['allow_name_change']} ({stats['allow_name_change']/stats['total_airlines']*100:.1f}%)
- **Solo correcciones:** {stats['allow_correction_only']} ({stats['allow_correction_only']/stats['total_airlines']*100:.1f}%)
- **Permiten cancelación:** {stats['allow_cancellation']} ({stats['allow_cancellation']/stats['total_airlines']*100:.1f}%)

### Estadísticas de Costos (Vuelos Domésticos)

- **Promedio:** {format_cop_amount(stats['avg_cost_domestic_cop'])}
- **Mínimo:** {format_cop_amount(stats['min_cost_domestic_cop'])}
- **Máximo:** {format_cop_amount(stats['max_cost_domestic_cop'])}
- **Mediana:** {format_cop_amount(stats.get('median_cost_domestic_cop'))}

### Costos en USD

- **Promedio:** {format_usd_amount(stats['avg_cost_usd'])}
- **Mínimo:** {format_usd_amount(stats['min_cost_usd'])}
- **Máximo:** {format_usd_amount(stats['max_cost_usd'])}

### Reembolsos

- **Porcentaje promedio de reembolso:** {stats['avg_refund_percentage']:.1f}% if stats['avg_refund_percentage'] else 'N/A'
- **Rango:** {stats['min_refund_percentage'] if stats['min_refund_percentage'] else 'N/A'}% - {stats['max_refund_percentage'] if stats['max_refund_percentage'] else 'N/A'}%

### Cobertura de Datos

"""

        for field, coverage in stats.get('data_coverage', {}).items():
            content += f"- **{field}:** {coverage}% de datos completos\n"

        content += f"""
### Calidad de Datos

- **Políticas que requieren revisión manual:** {stats['requires_review']} ({stats['requires_review']/stats['total_airlines']*100:.1f}%)

---

"""

        return content

    def _generate_opportunities(self, report: ViabilityReport, policies: List[AirlinePolicy]) -> str:
        """Genera sección de oportunidades identificadas"""
        viable_policies = [p for p in policies if p.is_transfer_viable()]

        content = """## 💡 Oportunidades Identificadas

### Aerolíneas con Políticas Más Flexibles

Las siguientes aerolíneas tienen las políticas más favorables para un marketplace:

"""

        for policy in viable_policies:
            score = policy.get_viability_score()
            content += f"- **{policy.airline_name}** (Score: {score:.2f}): "

            if policy.allows_transfer_to_third_party:
                content += "Permite transferencia directa a terceros. "
            elif policy.allows_full_name_change:
                content += "Permite cambio de nombre completo. "

            if policy.cost_name_change_domestic_cop and policy.cost_name_change_domestic_cop < 100000:
                content += "Costo razonable. "

            content += "\n"

        content += """
### Nichos de Mercado

1. **Vuelos Domésticos**: Mayor flexibilidad y costos más bajos
2. **Tarifas Flexibles**: Típicamente permiten más cambios
3. **Vuelos de Negocios**: Mayor disposición a pagar comisiones

### Segmentos de Clientes Potenciales

1. **Viajeros Frecuentes**: Interesados en recuperar valor de boletos no usados
2. **Compradores Flexibles**: Buscan descuentos en boletos
3. **Agencias de Viaje**: Posible B2B para gestión de inventario

---

"""

        return content

    def _generate_business_models(self, report: ViabilityReport) -> str:
        """Genera sección de modelos de negocio sugeridos"""
        return """## 🚀 Modelos de Negocio Sugeridos

### Opción A: Marketplace Directo (Si alta viabilidad)

**Descripción:** Plataforma que facilita transferencia oficial de boletos entre usuarios

**Pros:**
- Modelo transparente y legal
- Menor riesgo regulatorio
- Mayor confianza del usuario

**Contras:**
- Limitado a aerolíneas que permiten transferencia
- Costos de transferencia pueden ser altos
- Requiere integración con cada aerolínea

**Viabilidad:** Alta si >60% del mercado permite transferencia

---

### Opción B: Marketplace de Compensación (Alternativa)

**Descripción:** Sistema donde vendedor compra boleto nuevo a comprador y este le paga, sin transferencia oficial

**Pros:**
- No limitado por políticas de aerolíneas
- Mayor cobertura de mercado
- Más flexible

**Contras:**
- Mayor riesgo de fraude
- Requiere sistema robusto de verificación
- Zona gris legal

**Viabilidad:** Media, requiere validación legal exhaustiva

---

### Opción C: Seguros + Reventa (Híbrido)

**Descripción:** Ofrecer seguros de cancelación y, cuando se activan, revender el boleto

**Pros:**
- Modelo B2B con aerolíneas
- Menor riesgo regulatorio
- Genera ingresos por seguros

**Contras:**
- Requiere capital para seguros
- Complejo de implementar
- Depende de acuerdos con aerolíneas

**Viabilidad:** Alta a largo plazo, requiere partnerships

---

### Opción D: Plataforma de Alertas (MVP Simplificado)

**Descripción:** Notificar a usuarios cuando hay boletos disponibles de otros usuarios, sin intermediar transacción

**Pros:**
- Muy simple de implementar
- Sin riesgo regulatorio
- Bajo costo operativo

**Contras:**
- Menor monetización
- No resuelve problema completamente
- Difícil de escalar

**Viabilidad:** Alta como MVP para validar mercado

---

"""

    def _generate_financial_projection(self, report: ViabilityReport, stats: Dict) -> str:
        """Genera proyección financiera inicial"""
        # Cálculos simplificados
        avg_ticket_price = 300000  # COP promedio
        commission_rate = 0.10  # 10% de comisión
        avg_commission = avg_ticket_price * commission_rate

        monthly_transactions_conservative = 50
        monthly_transactions_moderate = 200
        monthly_transactions_optimistic = 500

        monthly_revenue_conservative = monthly_transactions_conservative * avg_commission
        monthly_revenue_moderate = monthly_transactions_moderate * avg_commission
        monthly_revenue_optimistic = monthly_transactions_optimistic * avg_commission

        return f"""## 💰 Proyección Financiera Inicial

### Supuestos

- **Precio promedio de boleto:** ${avg_ticket_price:,} COP
- **Comisión sugerida:** {commission_rate*100:.0f}%
- **Comisión promedio por transacción:** ${avg_commission:,} COP
- **Costo de transferencia promedio:** {format_cop_amount(stats['avg_cost_domestic_cop'])}

### Escenarios de Revenue Mensual

| Escenario | Transacciones/Mes | Revenue Mensual | Revenue Anual |
|-----------|-------------------|-----------------|---------------|
| **Conservador** | {monthly_transactions_conservative} | ${monthly_revenue_conservative:,} COP | ${monthly_revenue_conservative*12:,} COP |
| **Moderado** | {monthly_transactions_moderate} | ${monthly_revenue_moderate:,} COP | ${monthly_revenue_moderate*12:,} COP |
| **Optimista** | {monthly_transactions_optimistic} | ${monthly_revenue_optimistic:,} COP | ${monthly_revenue_optimistic*12:,} COP |

### Break-Even Analysis

Asumiendo costos operativos mensuales de $5,000,000 COP (servidor, marketing, equipo mínimo):

- **Transacciones necesarias para break-even:** {int(5000000 / avg_commission)} transacciones/mes

### Viabilidad Financiera

{'✅ **VIABLE**: Con {report.market_coverage_percentage:.0f}% de cobertura de mercado y costos razonables, el modelo es financieramente viable.' if report.is_viable() else '⚠️ **REQUIERE VALIDACIÓN**: La cobertura actual del {report.market_coverage_percentage:.0f}% requiere validación adicional de demanda.' if report.market_coverage_percentage >= 40 else '❌ **NO VIABLE**: Cobertura insuficiente del mercado para sostener el modelo.'}

---

"""

    def _generate_next_steps(self, report: ViabilityReport) -> str:
        """Genera sección de próximos pasos"""
        if report.is_viable():
            return """## 📍 Próximos Pasos Recomendados

### Fase 1: Validación (Semanas 1-4)

1. ✅ **Validación Legal**
   - Consultar con abogado especialista en derecho aeronáutico
   - Verificar compliance con regulaciones de Aerocivil
   - Revisar términos y condiciones de cada aerolínea

2. ✅ **Validación de Mercado**
   - Encuestas a viajeros frecuentes (n=100+)
   - Entrevistas con potenciales usuarios
   - Análisis de competencia internacional

3. ✅ **Validación Técnica**
   - Verificar manualmente procesos de transferencia
   - Contactar servicio al cliente de aerolíneas viables
   - Documentar flujos de transferencia reales

### Fase 2: MVP (Semanas 5-12)

1. **Desarrollo de Plataforma**
   - Landing page + formulario de interés
   - Sistema básico de matching vendedor-comprador
   - Panel de administración

2. **Piloto Limitado**
   - Enfocarse en 2-3 aerolíneas más flexibles
   - 10-20 transacciones iniciales
   - Documentar todo el proceso

3. **Refinamiento**
   - Iterar basado en feedback
   - Optimizar proceso de transferencia
   - Desarrollar sistema de verificación

### Fase 3: Escalamiento (Semanas 13+)

1. **Partnerships**
   - Acercamiento a aerolíneas viables
   - Negociar condiciones especiales
   - Automatizar procesos cuando sea posible

2. **Marketing y Crecimiento**
   - Campañas digitales enfocadas
   - Programa de referidos
   - Contenido educativo sobre reventa

3. **Expansión de Servicios**
   - Agregar seguros
   - Ofrecer garantías
   - Servicios premium

---

"""
        else:
            return """## 📍 Próximos Pasos Recomendados

### El Marketplace Tradicional NO es Viable

Basado en el análisis, se recomienda **NO** proceder con un marketplace tradicional de reventa de boletos.

### Alternativas a Explorar

1. **Modelo de Compensación P2P**
   - Investigar viabilidad legal
   - Desarrollar sistema robusto de verificación
   - Consultar con expertos legales

2. **Plataforma de Seguros**
   - Partnership con aerolíneas
   - Modelo B2B de seguros de cancelación
   - Requiere capital inicial

3. **Alertas y Notificaciones**
   - MVP simple sin intermediación
   - Monetizar vía publicidad o subscripciones
   - Validar demanda del mercado

4. **Pivot Completo**
   - Explorar otros pain points en viajes
   - Servicios complementarios (traslados, hoteles)
   - Diferentes geografías con mejores políticas

### Investigación Adicional

- Analizar mercados internacionales con políticas más flexibles
- Estudiar casos de éxito en otros países
- Validar restricciones legales en Colombia

---

"""

    def _generate_appendices(self, policies: List[AirlinePolicy], stats: Dict) -> str:
        """Genera apéndices"""
        content = """## 📎 Apéndices

### A. URLs Scrapeadas

"""

        for policy in policies:
            content += f"- **{policy.airline_name}**: {policy.source_url}\n"

        content += f"""

### B. Fechas de Extracción

"""

        for policy in policies:
            content += f"- **{policy.airline_name}**: {policy.scraped_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        content += """

### C. Items que Requieren Revisión Manual

"""

        manual_review_policies = [p for p in policies if p.requires_manual_review]

        if manual_review_policies:
            for policy in manual_review_policies:
                content += f"- **{policy.airline_name}**: {policy.manual_review_notes}\n"
        else:
            content += "Ninguno - todos los datos fueron extraídos satisfactoriamente.\n"

        content += """

### D. Limitaciones del Estudio

1. **Scraping Automatizado**: Los datos fueron extraídos automáticamente y pueden contener errores
2. **Cambios de Políticas**: Las aerolíneas pueden cambiar sus políticas sin previo aviso
3. **Interpretación**: Algunas políticas pueden tener matices no capturados por el scraper
4. **Validación Manual**: Se recomienda verificar manualmente con cada aerolínea antes de tomar decisiones
5. **Aspecto Legal**: Este reporte es informativo, no constituye asesoría legal

### E. Disclaimer Legal

Este reporte es generado con fines informativos y de investigación. La información sobre políticas
de aerolíneas puede estar sujeta a cambios. Se recomienda:

- Verificar información directamente con cada aerolínea
- Consultar con abogado especializado antes de implementar cualquier modelo de negocio
- Revisar regulaciones de Aerocivil y autoridades competentes
- Obtener términos y condiciones actualizados de cada aerolínea

### F. Metodología

**Herramientas utilizadas:**
- Python 3.10+
- Scrapy + BeautifulSoup4 para web scraping
- Pandas para análisis de datos
- SQLite para almacenamiento
- Matplotlib/Seaborn para visualizaciones

**Proceso:**
1. Scraping automatizado de páginas de políticas
2. Extracción con regex y NLP básico
3. Validación y limpieza de datos
4. Análisis estadístico con Pandas
5. Generación de reportes y visualizaciones

---

## 📧 Contacto y Feedback

Para preguntas, sugerencias o reportar errores en este análisis, por favor contactar al equipo
de investigación.

---

**Fin del Reporte**

*Generado automáticamente por el Sistema de Análisis de Políticas de Aerolíneas v1.0*
"""

        return content

    def _format_list(self, items: List[str]) -> str:
        """Formatea una lista como items de markdown"""
        if not items:
            return "- Ninguna"

        return '\n'.join([f"- {item}" for item in items])
