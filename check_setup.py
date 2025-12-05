#!/usr/bin/env python3
"""
Script para verificar que el setup está completo y listo para usar
"""

import sys
from pathlib import Path

def check_setup():
    """Verifica que todo esté configurado correctamente"""

    print("🔍 Verificando configuración del proyecto...\n")

    errors = []
    warnings = []

    # Verificar Python version
    if sys.version_info < (3, 10):
        errors.append(f"Python 3.10+ requerido (actual: {sys.version_info.major}.{sys.version_info.minor})")
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # Verificar estructura de carpetas
    required_dirs = ['src', 'data', 'logs', 'data/exports', 'data/snapshots', 'data/exports/graficos']

    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ Carpeta: {dir_path}")
        else:
            errors.append(f"Falta carpeta: {dir_path}")

    # Verificar archivos principales
    required_files = [
        'main.py',
        'requirements.txt',
        'README.md',
        'src/config.py',
        'src/models.py',
        'src/database.py',
        'src/utils.py',
        'src/analyzer.py',
        'src/report_generator.py',
        'src/scrapers/base_scraper.py'
    ]

    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ Archivo: {file_path}")
        else:
            errors.append(f"Falta archivo: {file_path}")

    # Verificar .env
    if Path('.env').exists():
        print("✅ Archivo .env configurado")
    else:
        warnings.append("Archivo .env no encontrado (puedes copiar .env.example)")

    # Verificar módulos importables
    print("\n📦 Verificando módulos de Python...")

    modules_to_check = [
        'scrapy',
        'bs4',
        'lxml',
        'requests',
        'pandas',
        'openpyxl',
        'matplotlib',
        'seaborn',
        'dotenv'
    ]

    for module in modules_to_check:
        try:
            __import__(module)
            print(f"✅ Módulo: {module}")
        except ImportError:
            errors.append(f"Módulo no instalado: {module}")

    # Resumen
    print("\n" + "="*60)

    if errors:
        print(f"❌ Se encontraron {len(errors)} errores:\n")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ No se encontraron errores")

    if warnings:
        print(f"\n⚠️  Se encontraron {len(warnings)} advertencias:\n")
        for warning in warnings:
            print(f"  - {warning}")

    print("="*60)

    if not errors:
        print("\n🎉 ¡Todo listo! Puedes ejecutar:")
        print("   python main.py run-all")
        print("\n📖 O consulta el README.md para más opciones")
        return True
    else:
        print("\n⚠️  Por favor, corrige los errores antes de continuar")
        print("   Instala dependencias: pip install -r requirements.txt")
        return False


if __name__ == '__main__':
    success = check_setup()
    sys.exit(0 if success else 1)
