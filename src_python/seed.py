"""
Seed the database with sample patient records for demonstration.

Usage: python -m src_python.seed
"""
import uuid
from src_python.database import init_database, get_db, close_database
from src_python.logger import logger


def seed():
    init_database()
    db = get_db()

    seed_patients = [
        {
            "patient_id": str(uuid.uuid4()),
            "first_name": "Jane",
            "last_name": "Doe",
            "date_of_birth": "1985-03-15",
            "sex": "Female",
            "phone_number": "5551234567",
            "email": "jane.doe@example.com",
            "address_line_1": "123 Main Street",
            "address_line_2": "Apt 4B",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "insurance_provider": "Blue Cross Blue Shield",
            "insurance_member_id": "BCBS-987654",
            "preferred_language": "English",
            "emergency_contact_name": "John Doe",
            "emergency_contact_phone": "5559876543",
        },
        {
            "patient_id": str(uuid.uuid4()),
            "first_name": "Carlos",
            "last_name": "Rivera",
            "date_of_birth": "1992-11-28",
            "sex": "Male",
            "phone_number": "5555678901",
            "email": "carlos.r@example.com",
            "address_line_1": "456 Oak Avenue",
            "address_line_2": None,
            "city": "Miami",
            "state": "FL",
            "zip_code": "33101",
            "insurance_provider": "Aetna",
            "insurance_member_id": "AET-123456",
            "preferred_language": "Spanish",
            "emergency_contact_name": "Maria Rivera",
            "emergency_contact_phone": "5551112222",
        },
    ]

    for patient in seed_patients:
        db.execute("""
            INSERT OR IGNORE INTO patients (
                patient_id, first_name, last_name, date_of_birth, sex, phone_number,
                email, address_line_1, address_line_2, city, state, zip_code,
                insurance_provider, insurance_member_id, preferred_language,
                emergency_contact_name, emergency_contact_phone
            ) VALUES (
                :patient_id, :first_name, :last_name, :date_of_birth, :sex, :phone_number,
                :email, :address_line_1, :address_line_2, :city, :state, :zip_code,
                :insurance_provider, :insurance_member_id, :preferred_language,
                :emergency_contact_name, :emergency_contact_phone
            )
        """, patient)

    db.commit()
    logger.info(f"Seeded {len(seed_patients)} patient records")

    close_database()


if __name__ == "__main__":
    seed()
