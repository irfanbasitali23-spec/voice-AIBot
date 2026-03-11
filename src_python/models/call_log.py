from src_python.database import get_db
from src_python.logger import logger


def _row_to_dict(row):
    """Convert a sqlite3.Row to a plain dict."""
    if row is None:
        return None
    return dict(row)


class CallLogModel:
    """Call log data access layer — mirrors the Node.js CallLogModel exactly."""

    @staticmethod
    def create(call_id=None, patient_id=None, caller_phone=None, transcript=None, summary=None, status="completed"):
        """Create a call log entry linked to a patient."""
        db = get_db()
        cursor = db.execute(
            "INSERT INTO call_logs (call_id, patient_id, caller_phone, transcript, summary, status) VALUES (?, ?, ?, ?, ?, ?)",
            (call_id, patient_id, caller_phone, transcript, summary, status)
        )
        db.commit()

        last_id = cursor.lastrowid
        logger.info(f"Call log created: call_id={call_id}, patient_id={patient_id}")
        return {"id": last_id, "call_id": call_id, "patient_id": patient_id}

    @staticmethod
    def find_by_patient_id(patient_id):
        """Get call logs for a specific patient."""
        db = get_db()
        rows = db.execute(
            "SELECT * FROM call_logs WHERE patient_id = ? ORDER BY created_at DESC",
            (patient_id,)
        ).fetchall()
        return [_row_to_dict(r) for r in rows]

    @staticmethod
    def find_all(limit=50):
        """Get all call logs."""
        db = get_db()
        rows = db.execute(
            "SELECT * FROM call_logs ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
