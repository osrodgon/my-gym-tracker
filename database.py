import sqlite3
import datetime

from machine_images import MACHINE_IMAGES, get_machine_image_key

DEFAULT_REPS = 12
"""Reps assumed for a record that has none: rows logged before the reps column
existed and three-column Excel imports. The value is normalised into the table
on startup, so every stored set ends up with an explicit rep count."""

class GymDatabase:
    def __init__(self, db_name="gym.db"):
        self.db_name = db_name
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS machines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    machine_id INTEGER,
                    weight REAL NOT NULL,
                    reps INTEGER,
                    date TEXT NOT NULL,
                    FOREIGN KEY (machine_id) REFERENCES machines (id) ON DELETE CASCADE
                )
            """)
            self._dedupe_usages(cursor)
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_usages_machine_date
                ON usages (machine_id, date)
            """)
            columns = {
                row[1]
                for row in cursor.execute("PRAGMA table_info(machines)")
            }

            if "image_key" not in columns:
                cursor.execute("ALTER TABLE machines ADD COLUMN image_key TEXT")

                machines = cursor.execute(
                    "SELECT id, name FROM machines"
                ).fetchall()

                for machine_id, name in machines:
                    image_key = get_machine_image_key(name)
                    if image_key is not None:
                        cursor.execute(
                            "UPDATE machines SET image_key = ? WHERE id = ?",
                            (image_key, machine_id),
                        )

            # Databases created before 2.2.0 have no reps column. Older records
            # keep NULL here and are normalised to DEFAULT_REPS below.
            usage_columns = {
                row[1]
                for row in cursor.execute("PRAGMA table_info(usages)")
            }

            if "reps" not in usage_columns:
                cursor.execute("ALTER TABLE usages ADD COLUMN reps INTEGER")

            # A set without reps is treated as DEFAULT_REPS rather than as an
            # incomplete record, so the history renders one uniform shape.
            cursor.execute(
                "UPDATE usages SET reps = ? WHERE reps IS NULL",
                (DEFAULT_REPS,),
            )

            conn.commit()

    def _dedupe_usages(self, cursor):
        """Keep only the newest usage per machine and date before indexing."""
        has_duplicates = cursor.execute("""
            SELECT 1
            FROM usages
            GROUP BY machine_id, date
            HAVING COUNT(*) > 1
            LIMIT 1
        """).fetchone()

        if has_duplicates is None:
            return

        cursor.execute("""
            DELETE FROM usages
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM usages
                GROUP BY machine_id, date
            )
        """)

    @staticmethod
    def _today() -> str:
        return datetime.date.today().strftime("%Y-%m-%d")

    def get_summary(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, m.id, m.name, u.weight, u.reps, u.date
                FROM usages u
                JOIN machines m ON m.id = u.machine_id
                ORDER BY u.date DESC, u.id DESC
            """)
            return cursor.fetchall()

    def get_machines(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, image_key FROM machines ORDER BY name ASC"
            )
            return cursor.fetchall()

    def get_usage_history(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.date, m.name, u.weight, u.reps
                FROM machines m
                LEFT JOIN usages u ON u.machine_id = m.id
                ORDER BY u.date ASC, u.id ASC
            """)
            return cursor.fetchall()

    def get_latest_usage(self, machine_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT weight, reps, date
                FROM usages
                WHERE machine_id = ?
                ORDER BY date DESC, id DESC
                LIMIT 1
            """, (machine_id,))
            return cursor.fetchone()

    def get_usage_for_date(self, machine_id, usage_date=None):
        usage_date = usage_date or self._today()
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, weight, reps
                FROM usages
                WHERE machine_id = ? AND date = ?
                """,
                (machine_id, usage_date),
            )
            return cursor.fetchone()

    def log_use(self, machine_id, weight, reps):
        today = self._today()
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO usages (machine_id, weight, reps, date)
                VALUES (?, ?, ?, ?)
                """,
                (machine_id, weight, reps, today),
            )
            conn.commit()

    def update_usage(self, usage_id: int, weight: float, reps: int) -> None:
        """Overwrite the weight and reps of an existing usage record."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usages SET weight = ?, reps = ? WHERE id = ?",
                (weight, reps, usage_id),
            )
            conn.commit()

    def add_machine(self, name, image_key=None):
        if image_key is not None and image_key not in MACHINE_IMAGES:
            raise ValueError(f"Unknown machine image key: {image_key}")

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO machines (name, image_key) VALUES (?, ?)",
                (name, image_key),
            )
            conn.commit()

    def rename_machine(self, machine_id, new_name, image_key=None):
        if image_key is not None and image_key not in MACHINE_IMAGES:
            raise ValueError(f"Unknown machine image key: {image_key}")

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE machines SET name = ?, image_key = ? WHERE id = ?",
                (new_name, image_key, machine_id),
            )
            conn.commit()

    def delete_machine(self, machine_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usages WHERE machine_id = ?", (machine_id,))
            cursor.execute("DELETE FROM machines WHERE id = ?", (machine_id,))

    def delete_usage(self, usage_id: int) -> None:
        """Delete a usage record by ID."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usages WHERE id = ?", (usage_id,))
            conn.commit()

    def replace_data(
        self,
        machines: list[str],
        usages: list[tuple[str, str, float, int | None]],
    ):
        with self._connect() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM usages")
            cursor.execute("DELETE FROM machines")

            cursor.executemany(
                "INSERT INTO machines (name, image_key) VALUES (?, ?)",
                [
                    (name, get_machine_image_key(name))
                    for name in machines
                ],
            )

            machine_ids = {
                name: machine_id
                for machine_id, name in cursor.execute(
                    "SELECT id, name FROM machines"
                ).fetchall()
            }

            # The unique index allows one usage per machine and date, so an
            # imported workbook with duplicates keeps the last row for each pair.
            unique_usages: dict[tuple[str, str], tuple[float, int]] = {}
            for usage_date, machine_name, weight, reps in usages:
                unique_usages[(usage_date, machine_name)] = (
                    weight,
                    DEFAULT_REPS if reps is None else reps,
                )

            cursor.executemany(
                """
                INSERT INTO usages (date, machine_id, weight, reps)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (usage_date, machine_ids[machine_name], weight, reps)
                    for (usage_date, machine_name), (weight, reps)
                    in unique_usages.items()
                ],
            )

            conn.commit()