"""
Analizador de políticas de aerolíneas usando Pandas
Genera estadísticas, gráficos comparativos y métricas de viabilidad
"""

import logging
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Backend sin interfaz gráfica
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.models import AirlinePolicy, ViabilityReport
from src.database import DatabaseManager
from src.config import GRAFICOS_DIR, CHART_CONFIG, VIABILITY_THRESHOLDS
from src.utils import format_cop_amount


logger = logging.getLogger(__name__)


class PolicyAnalyzer:
    """
    Analizador de políticas de aerolíneas
    Genera estadísticas, visualizaciones y reportes de viabilidad
    """

    def __init__(self, db_manager: DatabaseManager = None):
        """
        Inicializa el analizador

        Args:
            db_manager: Gestor de base de datos (opcional)
        """
        self.db = db_manager or DatabaseManager()
        self.df: Optional[pd.DataFrame] = None

        # Configurar estilo de gráficos
        try:
            plt.style.use('seaborn-v0_8-darkgrid')
        except:
            plt.style.use('default')

        sns.set_palette(CHART_CONFIG['color_palette'])

    def load_data(self) -> pd.DataFrame:
        """
        Carga datos de políticas desde la base de datos

        Returns:
            DataFrame de pandas con las políticas
        """
        logger.info("Cargando datos de políticas...")

        policies = self.db.get_all_policies()

        if not policies:
            logger.warning("No hay políticas en la base de datos")
            return pd.DataFrame()

        # Convertir a lista de diccionarios
        data = [policy.to_dict() for policy in policies]

        # Crear DataFrame
        self.df = pd.DataFrame(data)

        logger.info(f"✅ {len(self.df)} políticas cargadas")

        return self.df

    def generate_statistics(self) -> Dict[str, Any]:
        """
        Genera estadísticas descriptivas de las políticas

        Returns:
            Diccionario con estadísticas
        """
        if self.df is None or self.df.empty:
            self.load_data()

        if self.df.empty:
            return {}

        stats = {}

        # Conteos básicos
        stats['total_airlines'] = len(self.df)

        stats['allow_transfer'] = self.df['allows_transfer_to_third_party'].sum()
        stats['allow_name_change'] = self.df['allows_full_name_change'].sum()
        stats['allow_correction_only'] = self.df['allows_name_correction'].sum()
        stats['allow_cancellation'] = self.df['allows_cancellation'].sum()

        # Estadísticas de costos (domésticos en COP)
        costs_domestic = self.df['cost_name_change_domestic_cop'].dropna()

        if not costs_domestic.empty:
            stats['avg_cost_domestic_cop'] = int(costs_domestic.mean())
            stats['min_cost_domestic_cop'] = int(costs_domestic.min())
            stats['max_cost_domestic_cop'] = int(costs_domestic.max())
            stats['median_cost_domestic_cop'] = int(costs_domestic.median())
        else:
            stats['avg_cost_domestic_cop'] = None
            stats['min_cost_domestic_cop'] = None
            stats['max_cost_domestic_cop'] = None
            stats['median_cost_domestic_cop'] = None

        # Estadísticas de costos USD
        costs_usd = self.df['cost_name_change_usd'].dropna()

        if not costs_usd.empty:
            stats['avg_cost_usd'] = float(costs_usd.mean())
            stats['min_cost_usd'] = float(costs_usd.min())
            stats['max_cost_usd'] = float(costs_usd.max())
        else:
            stats['avg_cost_usd'] = None
            stats['min_cost_usd'] = None
            stats['max_cost_usd'] = None

        # Porcentajes de reembolso
        refunds = self.df['refund_percentage'].dropna()

        if not refunds.empty:
            stats['avg_refund_percentage'] = float(refunds.mean())
            stats['min_refund_percentage'] = int(refunds.min())
            stats['max_refund_percentage'] = int(refunds.max())
        else:
            stats['avg_refund_percentage'] = None
            stats['min_refund_percentage'] = None
            stats['max_refund_percentage'] = None

        # Aerolíneas que requieren revisión manual
        stats['requires_review'] = self.df['requires_manual_review'].sum()

        # Cobertura de datos (campos no nulos)
        stats['data_coverage'] = {}
        critical_fields = ['allows_full_name_change', 'allows_name_correction',
                          'allows_transfer_to_third_party', 'cost_name_change_domestic_cop']

        for field in critical_fields:
            coverage = (self.df[field].notna().sum() / len(self.df)) * 100
            stats['data_coverage'][field] = round(coverage, 1)

        logger.info("📊 Estadísticas generadas")

        return stats

    def generate_viability_report(self) -> ViabilityReport:
        """
        Genera reporte de viabilidad del marketplace

        Returns:
            ViabilityReport con conclusiones y métricas
        """
        if self.df is None or self.df.empty:
            self.load_data()

        logger.info("Generando reporte de viabilidad...")

        stats = self.generate_statistics()

        # Calcular aerolíneas viables
        viable_mask = (
            (self.df['allows_transfer_to_third_party'] == True) |
            (self.df['allows_full_name_change'] == True)
        )

        viable_airlines = self.df[viable_mask]['airline_name'].tolist()
        non_viable_airlines = self.df[~viable_mask]['airline_name'].tolist()

        # Calcular cobertura del mercado
        total = len(self.df)
        viable_count = len(viable_airlines)
        market_coverage = (viable_count / total * 100) if total > 0 else 0

        # Calcular score general de viabilidad
        overall_score = self._calculate_overall_viability_score()

        # Generar conclusión
        conclusion = self._generate_conclusion(market_coverage, viable_count, stats)

        # Generar recomendación
        recommendation = self._generate_recommendation(market_coverage, viable_count, stats)

        report = ViabilityReport(
            total_airlines=stats['total_airlines'],
            scraped_successfully=stats['total_airlines'] - stats['requires_review'],
            allow_transfer=stats['allow_transfer'],
            allow_name_change=stats['allow_name_change'],
            allow_name_correction_only=stats['allow_correction_only'],
            avg_cost_domestic_cop=stats['avg_cost_domestic_cop'],
            min_cost_domestic_cop=stats['min_cost_domestic_cop'],
            max_cost_domestic_cop=stats['max_cost_domestic_cop'],
            viable_airlines=viable_airlines,
            non_viable_airlines=non_viable_airlines,
            market_coverage_percentage=round(market_coverage, 1),
            overall_viability_score=overall_score,
            conclusion=conclusion,
            recommendation=recommendation
        )

        logger.info(f"✅ Reporte de viabilidad: {report.get_viability_status()}")

        return report

    def generate_charts(self) -> List[Path]:
        """
        Genera todos los gráficos comparativos

        Returns:
            Lista de rutas a los gráficos generados
        """
        if self.df is None or self.df.empty:
            self.load_data()

        if self.df.empty:
            logger.warning("No hay datos para generar gráficos")
            return []

        logger.info("Generando gráficos comparativos...")

        chart_files = []

        try:
            # 1. Gráfico de barras: Costos por aerolínea
            chart_files.append(self._create_cost_comparison_chart())

            # 2. Pie chart: Permitir vs No permitir transferencia
            chart_files.append(self._create_transfer_policy_pie_chart())

            # 3. Gráfico de barras: Políticas por aerolínea
            chart_files.append(self._create_policies_comparison_chart())

            # 4. Heatmap de cobertura de datos
            chart_files.append(self._create_data_coverage_heatmap())

            logger.info(f"✅ {len(chart_files)} gráficos generados")

        except Exception as e:
            logger.error(f"Error generando gráficos: {e}")

        return chart_files

    def _create_cost_comparison_chart(self) -> Path:
        """Crea gráfico de comparación de costos"""
        fig, ax = plt.subplots(figsize=(12, 6))

        # Filtrar aerolíneas con costos
        df_costs = self.df[self.df['cost_name_change_domestic_cop'].notna()].copy()

        if df_costs.empty:
            logger.warning("No hay datos de costos para graficar")
            plt.close()
            return None

        # Ordenar por costo
        df_costs = df_costs.sort_values('cost_name_change_domestic_cop')

        # Crear gráfico de barras
        bars = ax.barh(
            df_costs['airline_name'],
            df_costs['cost_name_change_domestic_cop'],
            color='skyblue'
        )

        # Agregar etiquetas de valor
        for bar in bars:
            width = bar.get_width()
            ax.text(
                width,
                bar.get_y() + bar.get_height() / 2,
                f'${width:,.0f}',
                ha='left',
                va='center',
                fontsize=10
            )

        ax.set_xlabel('Costo en COP', fontsize=12)
        ax.set_ylabel('Aerolínea', fontsize=12)
        ax.set_title('Comparación de Costos de Cambio de Nombre (Vuelos Domésticos)', fontsize=14, fontweight='bold')

        plt.tight_layout()

        filepath = GRAFICOS_DIR / 'costos_comparacion.png'
        plt.savefig(filepath, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"Gráfico guardado: {filepath.name}")
        return filepath

    def _create_transfer_policy_pie_chart(self) -> Path:
        """Crea pie chart de políticas de transferencia"""
        fig, ax = plt.subplots(figsize=(10, 8))

        # Contar políticas
        allows_transfer = self.df['allows_transfer_to_third_party'].fillna(False).sum()
        allows_name_change = self.df['allows_full_name_change'].fillna(False).sum()
        allows_correction = self.df['allows_name_correction'].fillna(False).sum()

        # No permite ninguno
        no_allows = len(self.df) - len(self.df[
            (self.df['allows_transfer_to_third_party'] == True) |
            (self.df['allows_full_name_change'] == True) |
            (self.df['allows_name_correction'] == True)
        ])

        labels = [
            f'Permite Transferencia\n({allows_transfer})',
            f'Permite Cambio Nombre\n({allows_name_change})',
            f'Solo Correcciones\n({allows_correction})',
            f'No Permite\n({no_allows})'
        ]

        sizes = [allows_transfer, allows_name_change, allows_correction, no_allows]
        colors = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3']
        explode = (0.1, 0, 0, 0.1)

        # Crear pie chart
        ax.pie(
            sizes,
            explode=explode,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 11}
        )

        ax.set_title('Distribución de Políticas de Transferencia/Cambio de Nombre', fontsize=14, fontweight='bold')

        filepath = GRAFICOS_DIR / 'politicas_distribucion.png'
        plt.savefig(filepath, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"Gráfico guardado: {filepath.name}")
        return filepath

    def _create_policies_comparison_chart(self) -> Path:
        """Crea gráfico de comparación de políticas por aerolínea"""
        fig, ax = plt.subplots(figsize=(12, 8))

        # Preparar datos
        airlines = self.df['airline_name'].tolist()

        transfer = self.df['allows_transfer_to_third_party'].fillna(False).astype(int)
        name_change = self.df['allows_full_name_change'].fillna(False).astype(int)
        cancellation = self.df['allows_cancellation'].fillna(False).astype(int)

        x = range(len(airlines))
        width = 0.25

        # Crear barras agrupadas
        ax.bar([i - width for i in x], transfer, width, label='Permite Transferencia', color='#66c2a5')
        ax.bar(x, name_change, width, label='Permite Cambio Nombre', color='#fc8d62')
        ax.bar([i + width for i in x], cancellation, width, label='Permite Cancelación', color='#8da0cb')

        ax.set_xlabel('Aerolínea', fontsize=12)
        ax.set_ylabel('Permite (1) / No Permite (0)', fontsize=12)
        ax.set_title('Comparación de Políticas por Aerolínea', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(airlines, rotation=45, ha='right')
        ax.legend()
        ax.set_ylim(0, 1.2)

        plt.tight_layout()

        filepath = GRAFICOS_DIR / 'politicas_comparacion.png'
        plt.savefig(filepath, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"Gráfico guardado: {filepath.name}")
        return filepath

    def _create_data_coverage_heatmap(self) -> Path:
        """Crea heatmap de cobertura de datos"""
        fig, ax = plt.subplots(figsize=(10, 8))

        # Seleccionar campos críticos
        fields = [
            'allows_full_name_change',
            'allows_name_correction',
            'allows_transfer_to_third_party',
            'cost_name_change_domestic_cop',
            'allows_cancellation',
            'refund_percentage'
        ]

        # Crear matriz de disponibilidad (1 = tiene dato, 0 = no tiene)
        data_matrix = self.df[fields].notna().astype(int)
        data_matrix.index = self.df['airline_name']

        # Renombrar columnas para mejor visualización
        field_names = {
            'allows_full_name_change': 'Cambio Nombre',
            'allows_name_correction': 'Corrección',
            'allows_transfer_to_third_party': 'Transferencia',
            'cost_name_change_domestic_cop': 'Costo (COP)',
            'allows_cancellation': 'Cancelación',
            'refund_percentage': '% Reembolso'
        }

        data_matrix = data_matrix.rename(columns=field_names)

        # Crear heatmap
        sns.heatmap(
            data_matrix,
            annot=True,
            fmt='d',
            cmap='RdYlGn',
            cbar_kws={'label': 'Dato Disponible'},
            ax=ax
        )

        ax.set_title('Cobertura de Datos por Aerolínea y Campo', fontsize=14, fontweight='bold')
        ax.set_xlabel('Campo de Datos', fontsize=12)
        ax.set_ylabel('Aerolínea', fontsize=12)

        plt.tight_layout()

        filepath = GRAFICOS_DIR / 'cobertura_datos.png'
        plt.savefig(filepath, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"Gráfico guardado: {filepath.name}")
        return filepath

    def _calculate_overall_viability_score(self) -> float:
        """Calcula score general de viabilidad (0.0 a 1.0)"""
        if self.df.empty:
            return 0.0

        # Factores de viabilidad
        total = len(self.df)

        # 1. % de aerolíneas que permiten transferencia (50% del score)
        transfer_score = (self.df['allows_transfer_to_third_party'].fillna(False).sum() / total) * 0.5

        # 2. % de aerolíneas con costos razonables (30% del score)
        reasonable_costs = self.df[
            self.df['cost_name_change_domestic_cop'] <= VIABILITY_THRESHOLDS['max_acceptable_cost_cop']
        ]
        cost_score = (len(reasonable_costs) / total) * 0.3

        # 3. Completitud de datos (20% del score)
        data_score = (1 - (self.df['requires_manual_review'].sum() / total)) * 0.2

        overall_score = transfer_score + cost_score + data_score

        return round(overall_score, 2)

    def _generate_conclusion(self, market_coverage: float, viable_count: int, stats: Dict) -> str:
        """Genera conclusión de viabilidad"""
        if market_coverage >= VIABILITY_THRESHOLDS['market_coverage_ideal']:
            return (
                f"El marketplace de reventa de boletos ES VIABLE en Colombia. "
                f"{viable_count} de {stats['total_airlines']} aerolíneas ({market_coverage:.1f}%) "
                f"permiten transferencia o cambio de nombre, lo cual representa una cobertura "
                f"excelente del mercado. Los costos promedio son razonables y el proceso es factible."
            )
        elif market_coverage >= VIABILITY_THRESHOLDS['market_coverage_minimum']:
            return (
                f"El marketplace de reventa de boletos ES VIABLE CON RESTRICCIONES en Colombia. "
                f"{viable_count} de {stats['total_airlines']} aerolíneas ({market_coverage:.1f}%) "
                f"permiten transferencia o cambio de nombre. Aunque no es cobertura ideal, "
                f"representa un mercado suficiente para iniciar operaciones, especialmente si "
                f"se enfoca en las aerolíneas con políticas más flexibles."
            )
        else:
            return (
                f"El marketplace de reventa de boletos tradicional NO ES VIABLE en Colombia. "
                f"Solo {viable_count} de {stats['total_airlines']} aerolíneas ({market_coverage:.1f}%) "
                f"permiten transferencia o cambio de nombre, lo cual es insuficiente para "
                f"un marketplace efectivo. Se recomienda explorar modelos alternativos de negocio."
            )

    def _generate_recommendation(self, market_coverage: float, viable_count: int, stats: Dict) -> str:
        """Genera recomendación accionable"""
        if market_coverage >= VIABILITY_THRESHOLDS['market_coverage_ideal']:
            return (
                "RECOMENDACIÓN: Proceder con desarrollo de MVP. Enfocarse en las aerolíneas "
                "con políticas más flexibles. Establecer partnerships con aerolíneas viables. "
                "Considerar sistema de verificación de identidad robusto para transferencias."
            )
        elif market_coverage >= VIABILITY_THRESHOLDS['market_coverage_minimum']:
            return (
                "RECOMENDACIÓN: Proceder con piloto limitado. Enfocarse inicialmente en las "
                f"{viable_count} aerolíneas viables. Validar modelo de negocio antes de escalar. "
                "Considerar ofrecer servicios adicionales (seguros, compensación) para aumentar valor."
            )
        else:
            return (
                "RECOMENDACIÓN: NO proceder con marketplace tradicional. Explorar modelos alternativos: "
                "1) Marketplace de compensación (pagos entre usuarios sin transferencia oficial), "
                "2) Plataforma de seguros de cancelación, "
                "3) Sistema de alertas y recompra automática. "
                "Validar restricciones legales antes de implementar cualquier alternativa."
            )

    def export_to_excel(self, filepath: Path = None) -> Path:
        """
        Exporta datos a Excel con formato

        Args:
            filepath: Ruta del archivo (opcional)

        Returns:
            Ruta del archivo generado
        """
        if self.df is None or self.df.empty:
            self.load_data()

        if filepath is None:
            from src.config import OUTPUT_FILES
            filepath = OUTPUT_FILES['excel']

        logger.info(f"Exportando a Excel: {filepath}")

        # Crear writer de Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Hoja principal con datos
            self.df.to_excel(writer, sheet_name='Políticas', index=False)

            # Hoja de estadísticas
            stats = self.generate_statistics()
            stats_df = pd.DataFrame([stats])
            stats_df.to_excel(writer, sheet_name='Estadísticas', index=False)

        logger.info(f"✅ Excel generado: {filepath}")
        return filepath
