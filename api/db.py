from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "mock"
DB_PATH = DATA_DIR / "portal.db"


def get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS anglers (
            angler_id TEXT PRIMARY KEY,
            home_port TEXT,
            experience_level TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trips (
            trip_id TEXT PRIMARY KEY,
            angler_id TEXT NOT NULL,
            trip_date TEXT NOT NULL,
            launch_site TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            target_species TEXT NOT NULL,
            consent_version TEXT NOT NULL,
            created_at TEXT NOT NULL,
            source_type TEXT NOT NULL,
            schema_version TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS catches (
            catch_id TEXT PRIMARY KEY,
            trip_id TEXT NOT NULL,
            species_code TEXT NOT NULL,
            count INTEGER NOT NULL,
            kept_count INTEGER NOT NULL,
            released_count INTEGER NOT NULL,
            avg_length_cm REAL NOT NULL,
            catch_lat REAL NOT NULL,
            catch_lon REAL NOT NULL,
            catch_time TEXT NOT NULL,
            created_at TEXT NOT NULL,
            source_type TEXT NOT NULL,
            schema_version TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tag_reports (
            tag_report_id TEXT PRIMARY KEY,
            trip_id TEXT NOT NULL,
            tag_code TEXT NOT NULL,
            event_type TEXT NOT NULL,
            species_code TEXT NOT NULL,
            event_datetime TEXT NOT NULL,
            event_lat REAL NOT NULL,
            event_lon REAL NOT NULL,
            condition TEXT NOT NULL,
            photo_url TEXT,
            created_at TEXT NOT NULL,
            source_type TEXT NOT NULL,
            schema_version TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS recapture_events (
            recapture_id TEXT PRIMARY KEY,
            tag_code TEXT NOT NULL,
            previous_event_id TEXT NOT NULL,
            current_event_id TEXT NOT NULL,
            days_at_liberty INTEGER NOT NULL,
            distance_km REAL NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS qa_flags (
            flag_id TEXT PRIMARY KEY,
            record_type TEXT NOT NULL,
            record_id TEXT NOT NULL,
            flag_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            score REAL NOT NULL,
            status TEXT NOT NULL,
            notes TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()
