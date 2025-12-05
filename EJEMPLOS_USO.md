# 📚 Ejemplos de Uso Práctico

Este documento contiene ejemplos prácticos de cómo usar el scraper.

## 🚀 Escenarios Comunes

### Escenario 1: Primera Ejecución Completa

**Objetivo:** Obtener un reporte completo de viabilidad

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar entorno (opcional)
cp .env.example .env

# 3. Verificar configuración
python check_setup.py

# 4. Ejecutar todo el proceso
python main.py run-all

# 5. Ver el reporte
cat data/exports/REPORTE_VIABILIDAD.md
# O abrirlo con un editor de markdown
```

**Tiempo estimado:** 25-60 minutos

---

### Escenario 2: Scrapear Solo una Aerolínea

**Objetivo:** Probar el scraper con una sola aerolínea primero

```bash
# Scrapear solo Avianca
python main.py scrape --airline AV

# Ver resultados en la base de datos
sqlite3 data/policies.db "SELECT * FROM airline_policies WHERE airline_code='AV';"

# O exportar a CSV
python main.py export --format csv
cat data/exports/policies.csv
```

---

### Escenario 3: Actualizar Datos Periódicamente

**Objetivo:** Re-scrapear para detectar cambios en políticas

```bash
# Scrapear todas las aerolíneas nuevamente
python main.py scrape --all

# El sistema detectará automáticamente cambios en el HTML
# y actualizará la base de datos

# Generar nuevo reporte con datos actualizados
python main.py report
```

---

### Escenario 4: Análisis Personalizado

**Objetivo:** Hacer análisis específico sin re-scrapear

```bash
# Solo analizar datos existentes
python main.py analyze

# Ver estadísticas en los logs
tail -100 logs/scraper.log

# Exportar datos para análisis externo
python main.py export --format json,xlsx
```

---

### Escenario 5: Debugging de un Scraper Específico

**Objetivo:** Investigar por qué una aerolínea falló

```bash
# 1. Scrapear la aerolínea específica con logs detallados
python main.py scrape --airline LA

# 2. Ver el log específico de esa aerolínea
cat logs/scraper_LA.log

# 3. Ver el snapshot HTML guardado
ls -lt data/snapshots/LA_*.html | head -1

# 4. Inspeccionar la política en la base de datos
sqlite3 data/policies.db "SELECT * FROM airline_policies WHERE airline_code='LA';"

# 5. Ver si requiere revisión manual
sqlite3 data/policies.db "SELECT airline_name, requires_manual_review, manual_review_notes FROM airline_policies WHERE requires_manual_review=1;"
```

---

### Escenario 6: Exportar Solo Aerolíneas Viables

**Objetivo:** Generar lista de aerolíneas viables para marketplace

```bash
# Ejecutar análisis completo primero
python main.py run-all

# Consultar solo aerolíneas viables en SQL
sqlite3 data/policies.db << EOF
SELECT
    airline_name,
    airline_code,
    allows_transfer_to_third_party,
    cost_name_change_domestic_cop
FROM airline_policies
WHERE allows_transfer_to_third_party = 1
   OR allows_full_name_change = 1
ORDER BY cost_name_change_domestic_cop;
EOF
```

---

### Escenario 7: Generar Presentación para Stakeholders

**Objetivo:** Crear material para presentar a inversionistas

```bash
# 1. Ejecutar análisis completo
python main.py run-all

# 2. Archivos a compartir:
#    - data/exports/REPORTE_VIABILIDAD.md (convertir a PDF)
#    - data/exports/policies.xlsx (para Excel)
#    - data/exports/graficos/*.png (gráficos)

# 3. Convertir markdown a PDF (requiere pandoc)
# pandoc data/exports/REPORTE_VIABILIDAD.md -o reporte.pdf

# 4. Abrir gráficos
open data/exports/graficos/
```

---

## 🐍 Uso Programático (Python)

### Ejemplo 1: Usar el Scraper en Código Propio

```python
from src.scrapers.avianca_scraper import AviancaScraper
from src.database import DatabaseManager

# Crear instancia del scraper
scraper = AviancaScraper()

# Ejecutar scraping
result = scraper.scrape()

if result.success:
    print(f"✅ Scraping exitoso: {result.airline_name}")
    print(f"Permite transferencia: {result.policy.allows_transfer_to_third_party}")
    print(f"Costo: ${result.policy.cost_name_change_domestic_cop}")
else:
    print(f"❌ Error: {result.error_message}")
```

### Ejemplo 2: Consultar Base de Datos

```python
from src.database import DatabaseManager

# Crear instancia del gestor de BD
db = DatabaseManager()

# Obtener todas las políticas
policies = db.get_all_policies()

for policy in policies:
    print(f"{policy.airline_name}: {policy.allows_transfer_to_third_party}")

# Obtener solo aerolíneas viables
viable_airlines = db.get_viable_airlines()
print(f"\nAerolíneas viables: {len(viable_airlines)}")

# Obtener estadísticas
stats = db.get_statistics()
print(f"Costo promedio: ${stats['avg_cost_domestic_cop']:,} COP")
```

### Ejemplo 3: Análisis Personalizado con Pandas

```python
from src.analyzer import PolicyAnalyzer
from src.database import DatabaseManager

# Crear analizador
db = DatabaseManager()
analyzer = PolicyAnalyzer(db)

# Cargar datos en DataFrame
df = analyzer.load_data()

# Análisis personalizado
print("Aerolíneas más baratas:")
cheap = df.nsmallest(3, 'cost_name_change_domestic_cop')[['airline_name', 'cost_name_change_domestic_cop']]
print(cheap)

print("\nAerolíneas que permiten transferencia:")
transfer_ok = df[df['allows_transfer_to_third_party'] == True]['airline_name'].tolist()
print(transfer_ok)

# Generar estadísticas
stats = analyzer.generate_statistics()
print(f"\nPromedio de costos: ${stats['avg_cost_domestic_cop']:,} COP")

# Generar reporte de viabilidad
report = analyzer.generate_viability_report()
print(f"\nViabilidad: {report.get_viability_status()}")
print(f"Cobertura: {report.market_coverage_percentage}%")
```

### Ejemplo 4: Generar Reporte Personalizado

```python
from src.report_generator import ReportGenerator
from src.database import DatabaseManager

# Crear generador
db = DatabaseManager()
report_gen = ReportGenerator(db)

# Generar reporte markdown
output_path = report_gen.generate_full_report()

print(f"Reporte generado: {output_path}")

# Leer y procesar el reporte
with open(output_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar sección específica
if 'VIABLE' in content:
    print("✅ El marketplace ES viable")
else:
    print("❌ El marketplace NO es viable")
```

---

## 🔧 Configuración Avanzada

### Cambiar Configuración Programáticamente

```python
import os
os.environ['MIN_DELAY'] = '1'  # Reducir delay (no recomendado)
os.environ['MAX_RETRIES'] = '5'  # Más reintentos
os.environ['LOG_LEVEL'] = 'DEBUG'  # Más logs

from src.scrapers.avianca_scraper import AviancaScraper
scraper = AviancaScraper()
result = scraper.scrape()
```

---

## 📊 Consultas SQL Útiles

### Ver todas las aerolíneas y sus políticas

```sql
SELECT
    airline_name,
    allows_transfer_to_third_party,
    cost_name_change_domestic_cop,
    scraped_at
FROM airline_policies
ORDER BY cost_name_change_domestic_cop;
```

### Aerolíneas que requieren revisión manual

```sql
SELECT
    airline_name,
    manual_review_notes,
    scraped_at
FROM airline_policies
WHERE requires_manual_review = 1;
```

### Estadísticas agregadas

```sql
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN allows_transfer_to_third_party = 1 THEN 1 ELSE 0 END) as allows_transfer,
    AVG(cost_name_change_domestic_cop) as avg_cost,
    MIN(cost_name_change_domestic_cop) as min_cost,
    MAX(cost_name_change_domestic_cop) as max_cost
FROM airline_policies;
```

---

## 🎯 Casos de Uso Real

### Caso 1: Validar Viabilidad antes de Invertir

```bash
# 1. Ejecutar análisis completo
python main.py run-all

# 2. Revisar conclusión en el reporte
grep "Conclusión de Viabilidad" -A 20 data/exports/REPORTE_VIABILIDAD.md

# 3. Ver gráficos
open data/exports/graficos/

# 4. Tomar decisión GO/NO-GO basado en:
#    - Cobertura de mercado
#    - Costos promedio
#    - Complejidad de implementación
```

### Caso 2: Preparar Pitch para Inversionistas

```bash
# 1. Generar todos los materiales
python main.py run-all

# 2. Crear presentación con:
#    - Reporte markdown (convertir a PDF)
#    - Gráficos comparativos
#    - Datos en Excel para respaldo

# 3. Puntos clave a resaltar:
#    - % de mercado viable
#    - Costo promedio por transacción
#    - Proyección financiera (del reporte)
#    - Aerolíneas específicas con mejores políticas
```

### Caso 3: Monitoreo Continuo de Cambios

```bash
# Crear cron job para scrapear semanalmente
# crontab -e

# Agregar línea (cada domingo a las 2am):
# 0 2 * * 0 cd /path/to/scrapeTravel && /path/to/venv/bin/python main.py run-all

# Esto mantendrá tus datos actualizados y detectará cambios automáticamente
```

---

## 💡 Tips y Trucos

### Tip 1: Ver solo el resumen de viabilidad

```bash
python main.py run-all 2>&1 | grep -E "VIABILIDAD|Cobertura|Score"
```

### Tip 2: Exportar solo aerolíneas viables a CSV

```python
import pandas as pd
from src.database import DatabaseManager

db = DatabaseManager()
viable = db.get_viable_airlines()

df = pd.DataFrame([p.to_dict() for p in viable])
df.to_csv('aerolíneas_viables.csv', index=False)
```

### Tip 3: Comparar dos ejecuciones

```bash
# Primera ejecución
python main.py run-all
cp data/exports/policies.csv data/exports/policies_2024_12_04.csv

# Esperar una semana...

# Segunda ejecución
python main.py run-all

# Comparar
diff data/exports/policies_2024_12_04.csv data/exports/policies.csv
```

---

## 🐛 Debugging Común

### Problema: Una aerolínea siempre falla

**Solución:**
```bash
# 1. Ver el HTML descargado
ls -lt data/snapshots/[CODIGO]_*.html | head -1

# 2. Abrir en navegador
open "$(ls -t data/snapshots/[CODIGO]_*.html | head -1)"

# 3. Verificar si hay CAPTCHA o bloqueo
grep -i "captcha\|cloudflare" "$(ls -t data/snapshots/[CODIGO]_*.html | head -1)"

# 4. Ajustar scraper específico si es necesario
```

---

¿Necesitas más ejemplos o tienes un caso de uso específico? ¡Agrega tus propios ejemplos aquí!
