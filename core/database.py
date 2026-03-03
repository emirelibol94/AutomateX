import sqlite3
import json
import os
import logging
from core.scenario import Scenario, Action

from core.config import DB_PATH

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.logger = logging.getLogger("DatabaseManager")
        self._initialize_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _initialize_db(self):
        """Veritabanı tablolarının oluşturulması (Eğer yoksa)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Senaryolar tablosu
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scenarios (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Aksiyonlar tablosu
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS actions (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        scenario_id INTEGER,
                        type TEXT NOT NULL,
                        params TEXT,
                        description TEXT,
                        order_index INTEGER,
                        FOREIGN KEY (scenario_id) REFERENCES scenarios (id) ON DELETE CASCADE
                    )
                """)
                conn.commit()
            self.logger.info("Database initialized successfully.")
        except Exception as e:
            # SQLite tam olarak AUTO_INCREMENT anahtar kelimesini desteklemez, INTEGER PRIMARY KEY zaten otomatiktir.
            # Standart SQLite sözdizimi için düzeltme yapılıyor.
            self._fix_initialization()

    def _fix_initialization(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Senaryolar tablosu: Paylod sütunu JSON verisini saklar
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scenarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        payload TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS actions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scenario_id INTEGER,
                        type TEXT NOT NULL,
                        params TEXT,
                        description TEXT,
                        order_index INTEGER,
                        FOREIGN KEY (scenario_id) REFERENCES scenarios (id) ON DELETE CASCADE
                    )
                """)
                # Varlıklar (Assets) tablosu: Görsel verilerini (binary) saklar
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS assets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        data BLOB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Suite tablosu: Test Süitlerini JSON olarak saklar
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS suites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        payload TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Suite Geçmişi tablosu: Süit çalışma analizlerini tutar
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS suite_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        suite_id INTEGER,
                        start_time TEXT,
                        end_time TEXT,
                        total_scenarios INTEGER,
                        successful_scenarios INTEGER,
                        failed_scenarios INTEGER,
                        FOREIGN KEY (suite_id) REFERENCES suites (id) ON DELETE CASCADE
                    )
                """)
                conn.commit()
        except Exception as e:
            self.logger.error(f"Veritabanı başlatılamadı: {e}")

    def save_scenario(self, scenario: Scenario):
        """Senaryoyu veritabanına kaydeder veya günceller."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                payload = json.dumps(scenario.as_dict())
                
                # Check if UPDATE is needed or INSERT
                start_fresh_insert = False

                if scenario.id:
                    # Mevcut olanı GÜNCELLE
                    cursor.execute(
                        "UPDATE scenarios SET name=?, description=?, payload=? WHERE id=?",
                        (scenario.name, scenario.description, payload, scenario.id)
                    )
                    
                    if cursor.rowcount == 0:
                        # RECORD NOT FOUND! (Deleted externally)
                        # We should re-create it as a new record
                        self.logger.warning(f"Scenario ID {scenario.id} not found in DB (probably deleted). Saving as new.")
                        start_fresh_insert = True
                    else:
                        # Aksiyonlar tablosu için: Eski aksiyonları silip yenilerini ekle
                        cursor.execute("DELETE FROM actions WHERE scenario_id=?", (scenario.id,))
                        scenario_id = scenario.id

                else:
                    start_fresh_insert = True

                if start_fresh_insert:
                     # Yeni KAYIT
                    cursor.execute(
                        "INSERT INTO scenarios (name, description, payload) VALUES (?, ?, ?)",
                        (scenario.name, scenario.description, payload)
                    )
                    scenario_id = cursor.lastrowid
                    scenario.id = scenario_id # Nesne ID'sini güncelle
                
                # Aksiyonları ekle (senkronize)
                for idx, action in enumerate(scenario.actions):
                    cursor.execute(
                        "INSERT INTO actions (scenario_id, type, params, description, order_index) VALUES (?, ?, ?, ?, ?)",
                        (scenario_id, action.type, json.dumps(action.params), action.description, idx)
                    )
                    
                conn.commit()
                return scenario_id
        except Exception as e:
            self.logger.error(f"Senaryo kaydedilirken hata: {e}")
            return None

    def list_scenarios(self):
        """Tüm senaryoların listesini döndürür."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, description, created_at FROM scenarios ORDER BY created_at DESC")
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Senaryolar listelenirken hata: {e}")
            return []

    def load_scenario_by_id(self, scenario_id):
        """ID'ye göre senaryo nesnesini tam olarak yükler."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Varsa JSON payload üzerinden yüklemeyi tercih et
                cursor.execute("SELECT name, description, payload FROM scenarios WHERE id = ?", (scenario_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                
                if row[2]: # Payload varsa
                    sc = Scenario.from_dict(json.loads(row[2]))
                    sc.id = scenario_id # v70: ID'nin set edildiğinden emin ol
                    return sc
                
                # Payload yoksa actions tablosundan manuel topla (Eski yöntem)
                scenario = Scenario(name=row[0], description=row[1], id=scenario_id) # v70: ID set et
                cursor.execute(
                    "SELECT type, params, description FROM actions WHERE scenario_id = ? ORDER BY order_index ASC",
                    (scenario_id,)
                )
                for action_row in cursor.fetchall():
                    scenario.add_action(Action(
                        type=action_row[0],
                        params=json.loads(action_row[1]),
                        description=action_row[2]
                    ))
                return scenario
        except Exception as e:
            self.logger.error(f"Senaryo yüklenirken hata: {e}")
            return None

    def delete_scenario(self, scenario_id):
        """Senaryoyu veritabanından siler."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Senaryo silinirken hata: {e}")
            return False

    # --- Varlık (Asset) Yönetimi ---
    def save_asset(self, name, file_path_or_bytes):
        """Yeni bir varlık (resim vb.) kaydeder. Dosya yolu VEYA bytes kabul eder."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Binary veriyi oku
                img_data = None
                
                if isinstance(file_path_or_bytes, bytes):
                    img_data = file_path_or_bytes
                elif os.path.exists(file_path_or_bytes):
                    with open(file_path_or_bytes, 'rb') as f:
                        img_data = f.read()
                
                cursor.execute(
                    "INSERT INTO assets (name, data) VALUES (?, ?)",
                    (name, sqlite3.Binary(img_data) if img_data else None)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Varlık kaydedilirken hata: {e}")
            return None

    def list_assets(self):
        """Tüm varlıkları listeler."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, created_at, data FROM assets ORDER BY created_at DESC")
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Varlıklar listelenirken hata: {e}")
            return []

    def get_asset_by_name(self, name):
        """İsme göre varlık (asset) döndürür."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, data, created_at FROM assets WHERE name = ?", (name,))
                return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Varlık aranırken hata: {e}")
            return None

    def delete_asset(self, asset_id):
        """Varlığı veritabanından siler."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Varlık silinirken hata: {e}")
            return False

    def get_asset_data(self, name):
        """İsme göre varlığın binary verisini getirir."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT data FROM assets WHERE name = ?", (name,))
                row = cursor.fetchone()
                if row:
                    return row[0]
                return None
        except Exception as e:
            self.logger.error(f"Varlık verisi alınırken hata: {e}")
            return None

    # --- SUITE YÖNETİMİ ---

    def save_suite(self, name: str, payload: dict, suite_id: int = None) -> int:
        """Suite kaydeder. Yeni ise ID döndürür, varsa günceller."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                payload_str = json.dumps(payload)
                if suite_id:
                    cursor.execute("UPDATE suites SET name=?, payload=? WHERE id=?", (name, payload_str, suite_id))
                    if cursor.rowcount == 0:
                        cursor.execute("INSERT INTO suites (name, payload) VALUES (?, ?)", (name, payload_str))
                        suite_id = cursor.lastrowid
                else:
                    cursor.execute("INSERT INTO suites (name, payload) VALUES (?, ?)", (name, payload_str))
                    suite_id = cursor.lastrowid
                conn.commit()
                return suite_id
        except Exception as e:
            self.logger.error(f"Suite kaydedilemedi: {e}")
            return None

    def list_suites(self):
        """Tüm suitleri listeler (id, name, created_at)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, created_at FROM suites ORDER BY created_at DESC")
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Suitler listelenemedi: {e}")
            return []

    def load_suite_by_id(self, suite_id: int):
        """ID'ye göre Suite payloadunu döndürür."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, payload FROM suites WHERE id = ?", (suite_id,))
                row = cursor.fetchone()
                if not row: return None
                return {"id": row[0], "name": row[1], "payload": json.loads(row[2])}
        except Exception as e:
            self.logger.error(f"Suite yüklenemedi (ID: {suite_id}): {e}")
            return None

    def delete_suite(self, suite_id: int) -> bool:
        """Suite'i siler."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM suites WHERE id=?", (suite_id,))
                conn.commit()
            self.logger.info(f"Suite silindi. ID: {suite_id}")
            return True
        except Exception as e:
            self.logger.error(f"Suite silinemedi (ID: {suite_id}): {e}")
            return False

    def save_suite_history(self, suite_id: int, start_time: str, end_time: str, total: int, success: int, failed: int):
        """Süit çalışma istatistiklerini kaydeder."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO suite_history (suite_id, start_time, end_time, total_scenarios, successful_scenarios, failed_scenarios)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (suite_id, start_time, end_time, total, success, failed))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Suite history kaydedilemedi: {e}")
            return None

    def get_suite_history(self, suite_id: int):
        """Süitin tüm geçmiş çalışmalarını (en yenisi en üstte) döndürür."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, start_time, end_time, total_scenarios, successful_scenarios, failed_scenarios
                    FROM suite_history
                    WHERE suite_id = ?
                    ORDER BY id DESC
                """, (suite_id,))
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Suite history listelenemedi: {e}")
            return []
