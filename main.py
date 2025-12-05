#!/usr/bin/env python3
"""
Scraper de Investigación de Aerolíneas Colombianas
Punto de entrada principal del sistema

Uso:
    python main.py run-all                    # Ejecutar todo el proceso
    python main.py scrape --all               # Scrapear todas las aerolíneas
    python main.py scrape --airline avianca   # Scrapear una aerolínea específica
    python main.py analyze                    # Analizar datos y generar estadísticas
    python main.py report                     # Generar reporte markdown
    python main.py export --format csv,json   # Exportar datos
"""

import sys
import argparse
import logging
import json
import pandas as pd
from pathlib import Path
from typing import List

# Importar módulos del proyecto
from src.config import (
    AIRLINES_CONFIG, OUTPUT_FILES, LOG_FILE, LOG_LEVEL,
    EXPORT_CSV, EXPORT_JSON, EXPORT_EXCEL, EXPORT_MARKDOWN
)
from src.utils import setup_logger
from src.database import DatabaseManager
from src.analyzer import PolicyAnalyzer
from src.report_generator import ReportGenerator

# Importar scrapers
from src.scrapers.avianca_scraper import AviancaScraper
from src.scrapers.latam_scraper import LatamScraper
from src.scrapers.wingo_scraper import WingoScraper
from src.scrapers.easyfly_scraper import EasyFlyScraper
from src.scrapers.satena_scraper import SatenaScraper
from src.scrapers.copa_scraper import CopaScraper
from src.scrapers.jetsmart_scraper import JetSmartScraper


# Configurar logger principal
logger = setup_logger('main', LOG_FILE, getattr(logging, LOG_LEVEL))


# Mapeo de códigos de aerolínea a clases de scraper
SCRAPER_MAP = {
    'AV': AviancaScraper,
    'LA': LatamScraper,
    'P5': WingoScraper,
    'VE': EasyFlyScraper,
    '9R': SatenaScraper,
    'CM': CopaScraper,
    'JA': JetSmartScraper,
}


def scrape_all() -> List[dict]:
    """
    Scrapea todas las aerolíneas configuradas

    Returns:
        Lista de resultados de scraping
    """
    logger.info("=" * 80)
    logger.info("🚀 INICIANDO SCRAPING DE TODAS LAS AEROLÍNEAS")
    logger.info("=" * 80)

    results = []

    for airline_config in AIRLINES_CONFIG:
        codigo = airline_config['codigo']
        nombre = airline_config['nombre']

        logger.info(f"\n{'='*60}")
        logger.info(f"Procesando: {nombre} ({codigo})")
        logger.info(f"{'='*60}")

        result = scrape_airline(codigo)
        results.append(result)

    # Resumen final
    logger.info("\n" + "=" * 80)
    logger.info("📊 RESUMEN DE SCRAPING")
    logger.info("=" * 80)

    successful = sum(1 for r in results if r['success'])
    failed = sum(1 for r in results if not r['success'])

    logger.info(f"✅ Exitosos: {successful}")
    logger.info(f"❌ Fallidos: {failed}")
    logger.info(f"📈 Total: {len(results)}")

    for result in results:
        status = "✅" if result['success'] else "❌"
        logger.info(f"  {status} {result['airline']} - {result.get('message', 'OK')}")

    logger.info("=" * 80)

    return results


def scrape_airline(airline_code: str) -> dict:
    """
    Scrapea una aerolínea específica

    Args:
        airline_code: Código IATA de la aerolínea

    Returns:
        Diccionario con resultado del scraping
    """
    airline_code = airline_code.upper()

    if airline_code not in SCRAPER_MAP:
        logger.error(f"❌ Aerolínea no encontrada: {airline_code}")
        logger.info(f"Aerolíneas disponibles: {', '.join(SCRAPER_MAP.keys())}")
        return {
            'airline': airline_code,
            'success': False,
            'message': 'Aerolínea no encontrada'
        }

    try:
        # Instanciar scraper
        scraper_class = SCRAPER_MAP[airline_code]
        scraper = scraper_class()

        # Ejecutar scraping
        result = scraper.scrape()

        return {
            'airline': result.airline_name,
            'success': result.success,
            'message': result.error_message if not result.success else 'OK',
            'execution_time': result.execution_time_seconds
        }

    except Exception as e:
        logger.error(f"❌ Error inesperado al scrapear {airline_code}: {e}")
        return {
            'airline': airline_code,
            'success': False,
            'message': str(e)
        }


def analyze_data():
    """
    Analiza los datos scrapeados y genera estadísticas
    """
    logger.info("=" * 80)
    logger.info("📊 ANALIZANDO DATOS")
    logger.info("=" * 80)

    try:
        db = DatabaseManager()
        analyzer = PolicyAnalyzer(db)

        # Cargar datos
        df = analyzer.load_data()

        if df.empty:
            logger.warning("⚠️ No hay datos para analizar. Ejecute 'scrape' primero.")
            return

        # Generar estadísticas
        logger.info("Generando estadísticas...")
        stats = analyzer.generate_statistics()

        logger.info("\n📈 ESTADÍSTICAS:")
        logger.info(f"  Total aerolíneas: {stats['total_airlines']}")
        logger.info(f"  Permiten transferencia: {stats['allow_transfer']}")
        logger.info(f"  Permiten cambio nombre: {stats['allow_name_change']}")
        logger.info(f"  Costo promedio (COP): ${stats['avg_cost_domestic_cop']:,}" if stats['avg_cost_domestic_cop'] else "  Costo promedio: N/A")

        # Generar reporte de viabilidad
        logger.info("\nGenerando reporte de viabilidad...")
        viability_report = analyzer.generate_viability_report()

        logger.info(f"\n🎯 VIABILIDAD: {viability_report.get_viability_status()}")
        logger.info(f"  Cobertura de mercado: {viability_report.market_coverage_percentage}%")
        logger.info(f"  Score de viabilidad: {viability_report.overall_viability_score:.2f}")
        logger.info(f"  Aerolíneas viables: {', '.join(viability_report.viable_airlines)}")

        # Generar gráficos
        logger.info("\n📊 Generando gráficos...")
        chart_files = analyzer.generate_charts()

        logger.info(f"✅ {len(chart_files)} gráficos generados")

        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Error al analizar datos: {e}")
        raise


def generate_report():
    """
    Genera el reporte markdown de viabilidad
    """
    logger.info("=" * 80)
    logger.info("📄 GENERANDO REPORTE MARKDOWN")
    logger.info("=" * 80)

    try:
        db = DatabaseManager()
        report_gen = ReportGenerator(db)

        output_path = report_gen.generate_full_report()

        logger.info(f"✅ Reporte generado exitosamente: {output_path}")
        logger.info(f"   Puede leer el reporte en: {output_path.absolute()}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Error al generar reporte: {e}")
        raise


def export_data(formats: List[str]):
    """
    Exporta datos a diferentes formatos

    Args:
        formats: Lista de formatos (csv, json, xlsx)
    """
    logger.info("=" * 80)
    logger.info("💾 EXPORTANDO DATOS")
    logger.info("=" * 80)

    try:
        db = DatabaseManager()

        # Obtener datos
        policies_data = db.export_to_dict_list()

        if not policies_data:
            logger.warning("⚠️ No hay datos para exportar.")
            return

        logger.info(f"Exportando {len(policies_data)} políticas...")

        # Exportar CSV
        if 'csv' in formats and EXPORT_CSV:
            df = pd.DataFrame(policies_data)
            output_path = OUTPUT_FILES['csv']
            df.to_csv(output_path, index=False, encoding='utf-8')
            logger.info(f"✅ CSV exportado: {output_path}")

        # Exportar JSON
        if 'json' in formats and EXPORT_JSON:
            output_path = OUTPUT_FILES['json']
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(policies_data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"✅ JSON exportado: {output_path}")

        # Exportar Excel
        if 'xlsx' in formats and EXPORT_EXCEL:
            analyzer = PolicyAnalyzer(db)
            analyzer.load_data()
            output_path = analyzer.export_to_excel()
            logger.info(f"✅ Excel exportado: {output_path}")

        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Error al exportar datos: {e}")
        raise


def run_all():
    """
    Ejecuta el proceso completo: scrape + analyze + report + export
    """
    logger.info("\n")
    logger.info("🎯" * 40)
    logger.info("🚀 EJECUTANDO PROCESO COMPLETO")
    logger.info("🎯" * 40)
    logger.info("\n")

    try:
        # 1. Scraping
        logger.info("PASO 1/4: Scraping de aerolíneas...\n")
        scrape_all()

        # 2. Análisis
        logger.info("\n\nPASO 2/4: Análisis de datos...\n")
        analyze_data()

        # 3. Exportación
        logger.info("\n\nPASO 3/4: Exportación de datos...\n")
        export_data(['csv', 'json', 'xlsx'])

        # 4. Reporte
        logger.info("\n\nPASO 4/4: Generación de reporte...\n")
        generate_report()

        logger.info("\n")
        logger.info("🎉" * 40)
        logger.info("✅ PROCESO COMPLETO FINALIZADO")
        logger.info("🎉" * 40)
        logger.info("\n")

        logger.info("📁 Archivos generados:")
        logger.info(f"  - Base de datos: {OUTPUT_FILES.get('csv').parent.parent / 'policies.db'}")
        logger.info(f"  - CSV: {OUTPUT_FILES['csv']}")
        logger.info(f"  - JSON: {OUTPUT_FILES['json']}")
        logger.info(f"  - Excel: {OUTPUT_FILES['excel']}")
        logger.info(f"  - Reporte: {OUTPUT_FILES['markdown']}")
        logger.info(f"  - Gráficos: data/exports/graficos/")
        logger.info("\n")

        logger.info("🎯 SIGUIENTE PASO:")
        logger.info(f"   Leer el reporte de viabilidad: {OUTPUT_FILES['markdown']}")
        logger.info("\n")

    except Exception as e:
        logger.error(f"\n❌ Error en el proceso: {e}")
        sys.exit(1)


def main():
    """Función principal con CLI"""
    parser = argparse.ArgumentParser(
        description='Scraper de Investigación de Aerolíneas Colombianas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py run-all                     # Ejecutar todo el proceso
  python main.py scrape --all                # Scrapear todas las aerolíneas
  python main.py scrape --airline AV         # Scrapear solo Avianca
  python main.py analyze                     # Analizar datos
  python main.py report                      # Generar reporte
  python main.py export --format csv,json    # Exportar datos

Aerolíneas disponibles:
  AV  - Avianca
  LA  - LATAM
  P5  - Wingo
  VE  - EasyFly
  9R  - Satena
  CM  - Copa Airlines
  JA  - JetSmart
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')

    # Comando: run-all
    subparsers.add_parser(
        'run-all',
        help='Ejecutar proceso completo (scrape + analyze + export + report)'
    )

    # Comando: scrape
    scrape_parser = subparsers.add_parser('scrape', help='Scrapear aerolíneas')
    scrape_group = scrape_parser.add_mutually_exclusive_group(required=True)
    scrape_group.add_argument('--all', action='store_true', help='Scrapear todas las aerolíneas')
    scrape_group.add_argument('--airline', type=str, help='Código de aerolínea específica (ej: AV)')

    # Comando: analyze
    subparsers.add_parser('analyze', help='Analizar datos y generar estadísticas')

    # Comando: report
    subparsers.add_parser('report', help='Generar reporte markdown de viabilidad')

    # Comando: export
    export_parser = subparsers.add_parser('export', help='Exportar datos')
    export_parser.add_argument(
        '--format',
        type=str,
        default='csv,json,xlsx',
        help='Formatos de exportación separados por coma (csv,json,xlsx)'
    )

    # Parsear argumentos
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Ejecutar comando
    try:
        if args.command == 'run-all':
            run_all()

        elif args.command == 'scrape':
            if args.all:
                scrape_all()
            else:
                result = scrape_airline(args.airline)
                if not result['success']:
                    sys.exit(1)

        elif args.command == 'analyze':
            analyze_data()

        elif args.command == 'report':
            generate_report()

        elif args.command == 'export':
            formats = [f.strip() for f in args.format.split(',')]
            export_data(formats)

    except KeyboardInterrupt:
        logger.info("\n⚠️ Proceso interrumpido por el usuario")
        sys.exit(1)

    except Exception as e:
        logger.error(f"\n❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
