import sqlite3
import os
from datetime import datetime

class DBManager:
    def __init__(self, db_name="apem_basecamp.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        """Membuka koneksi ke SQLite database"""
        return sqlite3.connect(self.db_name)

    def init_db(self):
        """Membuat tabel lora_packets jika belum ada"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lora_packets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    scientific_name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    received_at TEXT NOT NULL
                )
            ''')
            conn.commit()

    def insert_packet(self, node_id: str, timestamp: float, scientific_name: str, confidence: float):
        """Menyimpan paket data baru yang diterima dari LoRa"""
        # Sesuai standar kode biologi, pastikan kata kedua nama ilmiah selalu lowercase
        names = scientific_name.strip().split()
        if len(names) >= 2:
            names[0] = names[0].capitalize()
            names[1] = names[1].lower()
            formatted_name = " ".join(names)
        else:
            formatted_name = scientific_name

        received_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO lora_packets (node_id, timestamp, scientific_name, confidence, received_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (node_id, timestamp, formatted_name, confidence, received_at))
            conn.commit()

    def fetch_all_packets(self):
        """Mengambil seluruh data untuk ditampilkan di tabel UI Streamlit"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Ambil data terbaru di posisi paling atas (DESC)
            cursor.execute("SELECT id, node_id, timestamp, scientific_name, confidence, received_at FROM lora_packets ORDER BY id DESC")
            return cursor.fetchall()