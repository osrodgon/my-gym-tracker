import sqlite3
import datetime

from machine_images import MACHINE_IMAGES, get_machine_image_key

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
                    date TEXT NOT NULL,
                    FOREIGN KEY (machine_id) REFERENCES machines (id) ON DELETE CASCADE
                )
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

            conn.commit()

    def get_summary(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, m.name, u.weight, u.date
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
                SELECT u.date, m.name, u.weight
                FROM machines m
                LEFT JOIN usages u ON u.machine_id = m.id
                ORDER BY u.date ASC, u.id ASC
            """)
            return cursor.fetchall()

    def get_latest_usage(self, machine_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT weight, date
                FROM usages
                WHERE machine_id = ?
                ORDER BY date DESC, id DESC
                LIMIT 1
            """, (machine_id,))
            return cursor.fetchone()

    def log_use(self, machine_id, weight):
        today = datetime.date.today().strftime("%Y-%m-%d")
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usages (machine_id, weight, date) VALUES (?, ?, ?)", (machine_id, weight, today))
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
            conn.commit()

    def replace_data(
        self,
        machines: list[str],
        usages: list[tuple[str, str, float]],
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

            cursor.executemany(
                """
                INSERT INTO usages (date, machine_id, weight)
                VALUES (?, ?, ?)
                """,
                [
                    (usage_date, machine_ids[machine_name], weight)
                    for usage_date, machine_name, weight in usages
                ],
            )

            conn.commit()