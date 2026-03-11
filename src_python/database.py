import os
import sqlite3
from pathlib import Path
from src_python.config import config
from src_python.logger import logger

_db_connection = None


def get_db():
    """Get the database connection (thread-local for Flask)."""
    global _db_connection
    if _db_connection is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_connection


def init_database():
    """Initialize the SQLite database connection and create tables if they don't exist."""
    global _db_connection

    db_path = os.path.abspath(config["database"]["path"])
    db_dir = os.path.dirname(db_path)

    # Ensure the data directory exists
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        logger.info(f"Created database directory: {db_dir}")

    _db_connection = sqlite3.connect(db_path, check_same_thread=False)
    _db_connection.row_factory = sqlite3.Row

    # Enable WAL mode for better concurrent read performance
    _db_connection.execute("PRAGMA journal_mode = WAL")
    _db_connection.execute("PRAGMA foreign_keys = ON")

    logger.info(f"Database connected at: {db_path}")

    # Run migrations
    _create_tables()

    return _db_connection


def _create_tables():
    """Create all required tables with proper types and constraints."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL CHECK(length(first_name) BETWEEN 1 AND 50),
            last_name TEXT NOT NULL CHECK(length(last_name) BETWEEN 1 AND 50),
            date_of_birth TEXT NOT NULL,
            sex TEXT NOT NULL CHECK(sex IN ('Male', 'Female', 'Other', 'Decline to Answer')),
            phone_number TEXT NOT NULL,
            email TEXT,
            address_line_1 TEXT NOT NULL,
            address_line_2 TEXT,
            city TEXT NOT NULL CHECK(length(city) BETWEEN 1 AND 100),
            state TEXT NOT NULL CHECK(length(state) = 2),
            zip_code TEXT NOT NULL,
            insurance_provider TEXT,
            insurance_member_id TEXT,
            preferred_language TEXT DEFAULT 'English',
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            deleted_at TEXT DEFAULT NULL
        );

        CREATE TABLE IF NOT EXISTS call_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT,
            patient_id TEXT,
            caller_phone TEXT,
            transcript TEXT,
            summary TEXT,
            status TEXT DEFAULT 'completed',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        );

        CREATE INDEX IF NOT EXISTS idx_patients_last_name ON patients(last_name);
        CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone_number);
        CREATE INDEX IF NOT EXISTS idx_patients_dob ON patients(date_of_birth);
        CREATE INDEX IF NOT EXISTS idx_patients_deleted ON patients(deleted_at);
        CREATE INDEX IF NOT EXISTS idx_call_logs_patient ON call_logs(patient_id);
    """)

    logger.info("Database tables and indexes created/verified")


def close_database():
    """Close the database connection gracefully."""
    global _db_connection
    if _db_connection:
        _db_connection.close()
        _db_connection = None
        logger.info("Database connection closed")
