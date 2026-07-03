import serial
import json
import threading
import time
from src.database.db_manager import DBManager

class LoRaListener:
    def __init__(self, port="COM5", baudrate=9600, db_manager: DBManager = None):
        self.port = port
        self.baudrate = baudrate
        self.db_manager = db_manager if db_manager else DBManager()
        self.ser = None
        self.is_running = False
        self._thread = None

    def start(self):
        """Menjalankan pendengar serial di thread latar belakang"""
        if self.is_running:
            return
        
        self.is_running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
    def stop(self):
        """Menghentikan pembacaan serial secara aman tanpa membuat UI macet"""
        self.is_running = False
        
        # Langsung tutup paksa gerbang port serial agar memicu interupsi di loop thread
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
                print(f"[LoRa Listener]: Port {self.port} berhasil ditutup.")
        except Exception as e:
            print(f"[LoRa Listener Warning]: Gagal menutup port saat stop: {e}")
            
        # HAPUS ATAU JANGAN GUNAKAN self._thread.join() yang bikin UI Streamlit terkunci hang
        print("[LoRa Listener]: Sinyal stop dikirim, thread dilepas secara aman.")

    def _listen_loop(self):
        """Loop internal yang berjalan terus-menerus di background thread"""
        try:
            # BARIS PENGAMAN TAMBAHAN:
            # Mengizinkan koneksi database bawaan menunggu hingga 10 detik jika sedang dibaca oleh Streamlit
            if self.db_manager:
                self.db_manager.get_connection().close() # Memastikan pool awal bersih jika ada sisa koneksi
            
            # Menggunakan timeout pendek (0.1 detik) agar thread bisa merespons perintah stop dengan cepat
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
            buffer_data = ""

            while self.is_running:
                if self.ser.in_waiting > 0:
                    data_mentah = self.ser.read(self.ser.in_waiting)
                    buffer_data += data_mentah.decode('utf-8', errors='ignore')
                    
                    # Memproses data jika mendeteksi pemisah baris (\n)
                    while "\n" in buffer_data:
                        baris, buffer_data = buffer_data.split("\n", 1)
                        baris = baris.strip()
                        
                        if baris:
                            self._process_incoming_line(baris)
                else:
                    # Beri jeda sangat kecil agar CPU laptop tidak bekerja keras (0% CPU usage)
                    time.sleep(0.01)

        except Exception as e:
            print(f"[LoRa Listener Error]: Gagal membuka atau membaca {self.port}. Pesan: {e}")
            self.is_running = False
            
    def _process_incoming_line(self, line: str):
        """Mengurai baris teks string JSON dan menyimpannya ke database"""
        try:
            # Contoh data yang diharapkan masuk dari Edge:
            # {"node": "APEM_NODE_01", "species": "Charadrius javanicus", "conf": 0.852, "timestamp": 1717374528.0}
            data_json = json.loads(line)
            
            # Ekstraksi data dengan fallback/nilai default yang aman jika ada key yang hilang
            node_id = data_json.get("node", "UNKNOWN_NODE")
            scientific_name = data_json.get("species", "Unknown Species")
            confidence = float(data_json.get("conf", 0.0))
            timestamp = float(data_json.get("timestamp", time.time()))
            
            # Simpan langsung ke database SQLite via DBManager
            self.db_manager.insert_packet(
                node_id=node_id,
                timestamp=timestamp,
                scientific_name=scientific_name,
                confidence=confidence
            )
            print(f"[LoRa Listener Success]: Data disimpan -> {scientific_name} ({confidence})")
            
        except json.JSONDecodeError:
            print(f"[LoRa Listener Warning]: Menangkap data korup/bukan JSON valid -> {line}")
        except Exception as e:
            print(f"[LoRa Listener Error]: Gagal memproses baris data -> {e}")