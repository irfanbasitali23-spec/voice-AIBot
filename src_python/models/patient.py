import re
import uuid
from datetime import datetime, timezone
from src_python.database import get_db
from src_python.logger import logger

US_STATES = [
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
    'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
    'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
    'VA','WA','WV','WI','WY','DC','PR','VI','GU','AS','MP'
]


def _row_to_dict(row):
    """Convert a sqlite3.Row to a plain dict."""
    if row is None:
        return None
    return dict(row)


class PatientModel:
    """Patient data access layer — mirrors the Node.js PatientModel exactly."""

    @staticmethod
    def find_all(last_name=None, date_of_birth=None, phone_number=None, page=1, limit=50):
        """List all patients with optional filters. Excludes soft-deleted records."""
        db = get_db()
        query = "SELECT * FROM patients WHERE deleted_at IS NULL"
        params = []

        if last_name:
            query += " AND LOWER(last_name) = LOWER(?)"
            params.append(last_name)
        if date_of_birth:
            query += " AND date_of_birth = ?"
            params.append(date_of_birth)
        if phone_number:
            cleaned = re.sub(r'\D', '', phone_number)
            query += " AND phone_number = ?"
            params.append(cleaned)

        # Count total for pagination
        count_query = query.replace("SELECT *", "SELECT COUNT(*) as total", 1)
        total_row = db.execute(count_query, params).fetchone()
        total = total_row["total"] if total_row else 0

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, (page - 1) * limit])

        rows = db.execute(query, params).fetchall()
        patients = [_row_to_dict(r) for r in rows]

        return {"patients": patients, "total": total, "page": page, "limit": limit}

    @staticmethod
    def find_by_id(patient_id):
        """Find a patient by UUID. Returns None if not found or soft-deleted."""
        db = get_db()
        row = db.execute(
            "SELECT * FROM patients WHERE patient_id = ? AND deleted_at IS NULL",
            (patient_id,)
        ).fetchone()
        return _row_to_dict(row)

    @staticmethod
    def find_by_phone(phone_number):
        """Find a patient by phone number (for duplicate detection)."""
        db = get_db()
        cleaned = re.sub(r'\D', '', phone_number)
        row = db.execute(
            "SELECT * FROM patients WHERE phone_number = ? AND deleted_at IS NULL",
            (cleaned,)
        ).fetchone()
        return _row_to_dict(row)

    @staticmethod
    def create(data):
        """Create a new patient record. Returns the created patient dict."""
        db = get_db()
        patient_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # Clean phone numbers
        if data.get("phone_number"):
            data["phone_number"] = re.sub(r'\D', '', data["phone_number"])
        if data.get("emergency_contact_phone"):
            data["emergency_contact_phone"] = re.sub(r'\D', '', data["emergency_contact_phone"])
        if data.get("state"):
            data["state"] = data["state"].upper()

        patient = {
            "patient_id": patient_id,
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "date_of_birth": data["date_of_birth"],
            "sex": data["sex"],
            "phone_number": data["phone_number"],
            "email": data.get("email") or None,
            "address_line_1": data["address_line_1"],
            "address_line_2": data.get("address_line_2") or None,
            "city": data["city"],
            "state": data["state"],
            "zip_code": data["zip_code"],
            "insurance_provider": data.get("insurance_provider") or None,
            "insurance_member_id": data.get("insurance_member_id") or None,
            "preferred_language": data.get("preferred_language") or "English",
            "emergency_contact_name": data.get("emergency_contact_name") or None,
            "emergency_contact_phone": data.get("emergency_contact_phone") or None,
            "created_at": now,
            "updated_at": now,
        }

        db.execute("""
            INSERT INTO patients (
                patient_id, first_name, last_name, date_of_birth, sex, phone_number,
                email, address_line_1, address_line_2, city, state, zip_code,
                insurance_provider, insurance_member_id, preferred_language,
                emergency_contact_name, emergency_contact_phone, created_at, updated_at
            ) VALUES (
                :patient_id, :first_name, :last_name, :date_of_birth, :sex, :phone_number,
                :email, :address_line_1, :address_line_2, :city, :state, :zip_code,
                :insurance_provider, :insurance_member_id, :preferred_language,
                :emergency_contact_name, :emergency_contact_phone, :created_at, :updated_at
            )
        """, patient)
        db.commit()

        logger.info(f"Patient created: patient_id={patient_id}, name={data['first_name']} {data['last_name']}")
        return patient

    @staticmethod
    def update(patient_id, data):
        """Update an existing patient. Supports partial updates."""
        db = get_db()
        existing = PatientModel.find_by_id(patient_id)
        if not existing:
            return None

        # Clean phone numbers if provided
        if data.get("phone_number"):
            data["phone_number"] = re.sub(r'\D', '', data["phone_number"])
        if data.get("emergency_contact_phone"):
            data["emergency_contact_phone"] = re.sub(r'\D', '', data["emergency_contact_phone"])
        if data.get("state"):
            data["state"] = data["state"].upper()

        updatable_fields = [
            "first_name", "last_name", "date_of_birth", "sex", "phone_number",
            "email", "address_line_1", "address_line_2", "city", "state", "zip_code",
            "insurance_provider", "insurance_member_id", "preferred_language",
            "emergency_contact_name", "emergency_contact_phone"
        ]

        updates = {}
        for field in updatable_fields:
            if field in data and data[field] is not None:
                updates[field] = data[field]

        if not updates:
            return existing

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        updates["updated_at"] = now

        set_clauses = ", ".join(f"{key} = :{key}" for key in updates)
        updates["patient_id"] = patient_id

        db.execute(f"UPDATE patients SET {set_clauses} WHERE patient_id = :patient_id", updates)
        db.commit()

        logger.info(f"Patient updated: patient_id={patient_id}, fields={list(updates.keys())}")
        return PatientModel.find_by_id(patient_id)

    @staticmethod
    def soft_delete(patient_id):
        """Soft-delete a patient by setting deleted_at timestamp."""
        db = get_db()
        existing = PatientModel.find_by_id(patient_id)
        if not existing:
            return None

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        db.execute(
            "UPDATE patients SET deleted_at = ?, updated_at = ? WHERE patient_id = ?",
            (now, now, patient_id)
        )
        db.commit()

        logger.info(f"Patient soft-deleted: patient_id={patient_id}")
        existing["deleted_at"] = now
        existing["updated_at"] = now
        return existing
