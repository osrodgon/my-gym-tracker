import sqlite3
import datetime

class GymDatabase:
    def __init__(self, db_name="gym.db"):
        self.db_name = db_name
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_name)

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
            cursor.execute("SELECT id, name FROM machines ORDER BY name ASC")
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

    def add_machine(self, name):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO machines (name) VALUES (?)", (name,))
            conn.commit()

    def rename_machine(self, machine_id, new_name):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE machines SET name = ? WHERE id = ?", (new_name, machine_id))
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
                "INSERT INTO machines (name) VALUES (?)",
                [(name,) for name in machines],
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