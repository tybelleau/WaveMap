import sqlite3
from pathlib import Path

from PySide6.QtCore import QStandardPaths


class Database:
    def __init__(self):
        app_data_path = Path(
            QStandardPaths.writableLocation(
                QStandardPaths.AppDataLocation
            )
        )

        app_data_path.mkdir(parents=True, exist_ok=True)

        self.db_path = app_data_path / "wavemap.db"

        self.connection = sqlite3.connect(self.db_path)

        self._create_tables()

    def _create_tables(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS durations (
                file_path TEXT PRIMARY KEY,
                duration_ms INTEGER NOT NULL
            )
        """)

        self.connection.commit()

    def save_duration(self, file_path, duration_ms):
        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO durations (file_path, duration_ms)
            VALUES (?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                duration_ms = excluded.duration_ms
        """, (str(file_path), duration_ms))

        self.connection.commit()

    def load_durations(self):
        cursor = self.connection.cursor()

        cursor.execute("SELECT file_path, duration_ms FROM durations")

        return {
            Path(row[0]): row[1]
            for row in cursor.fetchall()
        }

    def close(self):
        self.connection.close()