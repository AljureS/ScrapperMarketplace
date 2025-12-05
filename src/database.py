"""
Gestión de base de datos SQLite para políticas de aerolíneas
Maneja creación de tablas, inserciones, consultas y actualizaciones
"""

import sqlite3
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from src.models import AirlinePolicy
from src.config import DB_PATH


logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Gestor de base de datos SQLite
    Maneja todas las operaciones CRUD para políticas de aerolíneas
    """

    def __init__(self, db_path: str = DB_PATH):
        """
        Inicializa el gestor de base de datos

        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection: Optional[sqlite3.Connection] = None

        # Crear tablas si no existen
        self._init_database()

    def _init_database(self):
        """Inicializa la base de datos y crea las tablas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Crear tabla principal de políticas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS airline_policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    airline_name TEXT NOT NULL,
                    airline_code TEXT UNIQUE NOT NULL,
                    allows_full_name_change BOOLEAN,
                    allows_name_correction BOOLEAN,
                    cost_name_change_domestic_cop INTEGER,
                    cost_name_change_intl_cop INTEGER,
                    cost_name_change_usd REAL,
                    allows_transfer_to_third_party BOOLEAN,
                    transfer_process_description TEXT,
                    allows_cancellation BOOLEAN,
                    cancellation_cost_cop INTEGER,
                    refund_percentage INTEGER,
                    time_restrictions TEXT,
                    fare_type_differences TEXT,
                    max_change_deadline TEXT,
                    terms_url TEXT,
                    support_phone TEXT,
                    support_email TEXT,
                    required_documentation TEXT,
                    notable_exceptions TEXT,
                    source_url TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    raw_html_hash TEXT,
                    requires_manual_review BOOLEAN DEFAULT 0,
                    manual_review_notes TEXT
                )
            """)

            # Crear índices para mejorar performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_airline_code
                ON airline_policies(airline_code)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_scraped_at
                ON airline_policies(scraped_at)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_requires_review
                ON airline_policies(requires_manual_review)
            """)

            # Tabla de historial (para tracking de cambios)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS policy_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    airline_code TEXT NOT NULL,
                    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    field_changed TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    FOREIGN KEY (airline_code) REFERENCES airline_policies(airline_code)
                )
            """)

            conn.commit()

        logger.info(f"Base de datos inicializada en: {self.db_path}")

    def get_connection(self) -> sqlite3.Connection:
        """
        Obtiene una conexión a la base de datos
        Usa Row factory para acceso por nombre de columna
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def insert_policy(self, policy: AirlinePolicy) -> bool:
        """
        Inserta una nueva política en la base de datos

        Args:
            policy: Objeto AirlinePolicy a insertar

        Returns:
            True si fue exitoso, False si falló
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO airline_policies (
                        airline_name, airline_code, allows_full_name_change,
                        allows_name_correction, cost_name_change_domestic_cop,
                        cost_name_change_intl_cop, cost_name_change_usd,
                        allows_transfer_to_third_party, transfer_process_description,
                        allows_cancellation, cancellation_cost_cop, refund_percentage,
                        time_restrictions, fare_type_differences, max_change_deadline,
                        terms_url, support_phone, support_email,
                        required_documentation, notable_exceptions, source_url,
                        scraped_at, raw_html_hash, requires_manual_review,
                        manual_review_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, policy.to_db_tuple())

                conn.commit()

                logger.info(f"✅ Política de {policy.airline_name} guardada en BD")
                return True

        except sqlite3.Error as e:
            logger.error(f"❌ Error al insertar política de {policy.airline_name}: {e}")
            return False

    def get_policy_by_code(self, airline_code: str) -> Optional[AirlinePolicy]:
        """
        Obtiene una política por código de aerolínea

        Args:
            airline_code: Código IATA de la aerolínea (ej: "AV")

        Returns:
            AirlinePolicy o None si no existe
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM airline_policies
                    WHERE airline_code = ?
                    ORDER BY scraped_at DESC
                    LIMIT 1
                """, (airline_code,))

                row = cursor.fetchone()

                if row:
                    return self._row_to_policy(row)
                return None

        except sqlite3.Error as e:
            logger.error(f"Error al consultar política de {airline_code}: {e}")
            return None

    def get_all_policies(self) -> List[AirlinePolicy]:
        """
        Obtiene todas las políticas de la base de datos

        Returns:
            Lista de AirlinePolicy
        """
        policies = []

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM airline_policies
                    ORDER BY scraped_at DESC
                """)

                rows = cursor.fetchall()

                for row in rows:
                    policy = self._row_to_policy(row)
                    if policy:
                        policies.append(policy)

        except sqlite3.Error as e:
            logger.error(f"Error al consultar todas las políticas: {e}")

        return policies

    def get_policies_requiring_review(self) -> List[AirlinePolicy]:
        """
        Obtiene políticas que requieren revisión manual

        Returns:
            Lista de AirlinePolicy que necesitan revisión
        """
        policies = []

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM airline_policies
                    WHERE requires_manual_review = 1
                    ORDER BY scraped_at DESC
                """)

                rows = cursor.fetchall()

                for row in rows:
                    policy = self._row_to_policy(row)
                    if policy:
                        policies.append(policy)

        except sqlite3.Error as e:
            logger.error(f"Error al consultar políticas para revisión: {e}")

        return policies

    def get_viable_airlines(self) -> List[AirlinePolicy]:
        """
        Obtiene aerolíneas viables para marketplace
        (permiten transferencia o cambio de nombre)

        Returns:
            Lista de AirlinePolicy viables
        """
        policies = []

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM airline_policies
                    WHERE allows_transfer_to_third_party = 1
                       OR allows_full_name_change = 1
                    ORDER BY airline_name
                """)

                rows = cursor.fetchall()

                for row in rows:
                    policy = self._row_to_policy(row)
                    if policy:
                        policies.append(policy)

        except sqlite3.Error as e:
            logger.error(f"Error al consultar aerolíneas viables: {e}")

        return policies

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas agregadas de las políticas

        Returns:
            Diccionario con estadísticas
        """
        stats = {}

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Total de aerolíneas
                cursor.execute("SELECT COUNT(*) FROM airline_policies")
                stats['total_airlines'] = cursor.fetchone()[0]

                # Aerolíneas que permiten transferencia
                cursor.execute("""
                    SELECT COUNT(*) FROM airline_policies
                    WHERE allows_transfer_to_third_party = 1
                """)
                stats['allow_transfer'] = cursor.fetchone()[0]

                # Aerolíneas que permiten cambio de nombre
                cursor.execute("""
                    SELECT COUNT(*) FROM airline_policies
                    WHERE allows_full_name_change = 1
                """)
                stats['allow_name_change'] = cursor.fetchone()[0]

                # Costo promedio de cambio doméstico
                cursor.execute("""
                    SELECT AVG(cost_name_change_domestic_cop)
                    FROM airline_policies
                    WHERE cost_name_change_domestic_cop IS NOT NULL
                """)
                result = cursor.fetchone()[0]
                stats['avg_cost_domestic_cop'] = int(result) if result else None

                # Costo mínimo y máximo
                cursor.execute("""
                    SELECT MIN(cost_name_change_domestic_cop),
                           MAX(cost_name_change_domestic_cop)
                    FROM airline_policies
                    WHERE cost_name_change_domestic_cop IS NOT NULL
                """)
                min_cost, max_cost = cursor.fetchone()
                stats['min_cost_cop'] = min_cost
                stats['max_cost_cop'] = max_cost

                # Aerolíneas que requieren revisión
                cursor.execute("""
                    SELECT COUNT(*) FROM airline_policies
                    WHERE requires_manual_review = 1
                """)
                stats['requires_review'] = cursor.fetchone()[0]

        except sqlite3.Error as e:
            logger.error(f"Error al obtener estadísticas: {e}")

        return stats

    def export_to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Exporta todas las políticas como lista de diccionarios
        Útil para exportar a CSV/JSON

        Returns:
            Lista de diccionarios con las políticas
        """
        policies = self.get_all_policies()
        return [policy.to_dict() for policy in policies]

    def delete_policy(self, airline_code: str) -> bool:
        """
        Elimina una política de la base de datos

        Args:
            airline_code: Código de la aerolínea

        Returns:
            True si fue exitoso, False si falló
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM airline_policies
                    WHERE airline_code = ?
                """, (airline_code,))
                conn.commit()

                logger.info(f"Política de {airline_code} eliminada")
                return True

        except sqlite3.Error as e:
            logger.error(f"Error al eliminar política de {airline_code}: {e}")
            return False

    def clear_all_policies(self) -> bool:
        """
        Limpia todas las políticas de la base de datos
        ⚠️ Usar con precaución

        Returns:
            True si fue exitoso, False si falló
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM airline_policies")
                conn.commit()

                logger.warning("⚠️ Todas las políticas han sido eliminadas")
                return True

        except sqlite3.Error as e:
            logger.error(f"Error al limpiar políticas: {e}")
            return False

    def _row_to_policy(self, row: sqlite3.Row) -> Optional[AirlinePolicy]:
        """
        Convierte una fila de SQLite a objeto AirlinePolicy

        Args:
            row: Fila de resultado de SQLite

        Returns:
            AirlinePolicy o None si hay error
        """
        try:
            # Parsear scraped_at
            scraped_at = datetime.fromisoformat(row['scraped_at']) if row['scraped_at'] else datetime.now()

            return AirlinePolicy(
                airline_name=row['airline_name'],
                airline_code=row['airline_code'],
                allows_full_name_change=bool(row['allows_full_name_change']) if row['allows_full_name_change'] is not None else None,
                allows_name_correction=bool(row['allows_name_correction']) if row['allows_name_correction'] is not None else None,
                cost_name_change_domestic_cop=row['cost_name_change_domestic_cop'],
                cost_name_change_intl_cop=row['cost_name_change_intl_cop'],
                cost_name_change_usd=row['cost_name_change_usd'],
                allows_transfer_to_third_party=bool(row['allows_transfer_to_third_party']) if row['allows_transfer_to_third_party'] is not None else None,
                transfer_process_description=row['transfer_process_description'],
                allows_cancellation=bool(row['allows_cancellation']) if row['allows_cancellation'] is not None else None,
                cancellation_cost_cop=row['cancellation_cost_cop'],
                refund_percentage=row['refund_percentage'],
                time_restrictions=row['time_restrictions'],
                fare_type_differences=row['fare_type_differences'],
                max_change_deadline=row['max_change_deadline'],
                terms_url=row['terms_url'],
                support_phone=row['support_phone'],
                support_email=row['support_email'],
                required_documentation=row['required_documentation'],
                notable_exceptions=row['notable_exceptions'],
                source_url=row['source_url'],
                scraped_at=scraped_at,
                raw_html_hash=row['raw_html_hash'],
                requires_manual_review=bool(row['requires_manual_review']),
                manual_review_notes=row['manual_review_notes']
            )

        except Exception as e:
            logger.error(f"Error al convertir fila a AirlinePolicy: {e}")
            return None

    def close(self):
        """Cierra la conexión a la base de datos"""
        if self.connection:
            self.connection.close()
            logger.info("Conexión a BD cerrada")
