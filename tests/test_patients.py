"""
Tests for the Patient API — mirrors the Node.js test suite exactly.

Run: python -m pytest tests/test_patients.py -v
"""
import os
import json
import pytest

# Override database path for testing BEFORE imports
os.environ["DATABASE_PATH"] = "./data/test_patients.db"

from src_python.database import init_database, close_database
from src_python.app import create_app


@pytest.fixture(scope="module")
def client():
    """Create a test client with a fresh test database."""
    init_database()
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client

    close_database()

    # Clean up test database
    for suffix in ("", "-wal", "-shm"):
        path = f"./data/test_patients.db{suffix}"
        try:
            os.unlink(path)
        except OSError:
            pass


VALID_PATIENT = {
    "first_name": "John",
    "last_name": "Smith",
    "date_of_birth": "1990-05-15",
    "sex": "Male",
    "phone_number": "5551234567",
    "email": "john.smith@test.com",
    "address_line_1": "789 Test Street",
    "address_line_2": "Suite 100",
    "city": "Dallas",
    "state": "TX",
    "zip_code": "75201",
    "insurance_provider": "UnitedHealth",
    "insurance_member_id": "UH-999888",
    "preferred_language": "English",
    "emergency_contact_name": "Jane Smith",
    "emergency_contact_phone": "5559876543",
}

# Use a mutable container so state persists across test classes
state = {"created_patient_id": None}


class TestPostPatients:
    def test_create_patient_with_valid_data(self, client):
        resp = client.post("/patients", json=VALID_PATIENT)
        assert resp.status_code == 201

        data = resp.get_json()
        assert "patient_id" in data
        assert data["first_name"] == "John"
        assert data["last_name"] == "Smith"
        assert data["date_of_birth"] == "1990-05-15"
        assert data["sex"] == "Male"
        assert data["phone_number"] == "5551234567"
        assert data["city"] == "Dallas"
        assert data["state"] == "TX"
        state["created_patient_id"] = data["patient_id"]

    def test_reject_missing_required_fields(self, client):
        resp = client.post("/patients", json={"first_name": "John"})
        assert resp.status_code == 400

        data = resp.get_json()
        assert data["error"] == "Validation failed"
        assert len(data["details"]) > 0

    def test_reject_future_date_of_birth(self, client):
        patient = {**VALID_PATIENT, "date_of_birth": "2099-01-01"}
        resp = client.post("/patients", json=patient)
        assert resp.status_code == 400

        data = resp.get_json()
        assert any(d["field"] == "date_of_birth" for d in data["details"])

    def test_reject_invalid_phone_number(self, client):
        patient = {**VALID_PATIENT, "phone_number": "123"}
        resp = client.post("/patients", json=patient)
        assert resp.status_code == 400

        data = resp.get_json()
        assert any(d["field"] == "phone_number" for d in data["details"])

    def test_reject_invalid_state_abbreviation(self, client):
        patient = {**VALID_PATIENT, "state": "XX"}
        resp = client.post("/patients", json=patient)
        assert resp.status_code == 400

        data = resp.get_json()
        assert any(d["field"] == "state" for d in data["details"])

    def test_reject_invalid_zip_code(self, client):
        patient = {**VALID_PATIENT, "zip_code": "123"}
        resp = client.post("/patients", json=patient)
        assert resp.status_code == 400

        data = resp.get_json()
        assert any(d["field"] == "zip_code" for d in data["details"])

    def test_reject_invalid_sex_value(self, client):
        patient = {**VALID_PATIENT, "sex": "InvalidValue"}
        resp = client.post("/patients", json=patient)
        assert resp.status_code == 400

        data = resp.get_json()
        assert any(d["field"] == "sex" for d in data["details"])

    def test_accept_zip_plus_4_format(self, client):
        patient = {**VALID_PATIENT, "zip_code": "75201-1234", "phone_number": "5550001111"}
        resp = client.post("/patients", json=patient)
        assert resp.status_code == 201

        data = resp.get_json()
        assert data["zip_code"] == "75201-1234"


class TestGetPatients:
    def test_list_all_patients(self, client):
        resp = client.get("/patients")
        assert resp.status_code == 200

        data = resp.get_json()
        assert "patients" in data
        assert "total" in data
        assert len(data["patients"]) > 0

    def test_filter_by_last_name(self, client):
        resp = client.get("/patients?last_name=Smith")
        assert resp.status_code == 200

        data = resp.get_json()
        assert all(p["last_name"] == "Smith" for p in data["patients"])

    def test_filter_by_phone_number(self, client):
        resp = client.get("/patients?phone_number=5551234567")
        assert resp.status_code == 200

        data = resp.get_json()
        assert len(data["patients"]) > 0

    def test_empty_results_for_nonexistent_filter(self, client):
        resp = client.get("/patients?last_name=NonExistentName")
        assert resp.status_code == 200

        data = resp.get_json()
        assert len(data["patients"]) == 0


class TestGetPatientById:
    def test_return_patient_by_id(self, client):
        pid = state["created_patient_id"]
        resp = client.get(f"/patients/{pid}")
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["patient_id"] == pid
        assert data["first_name"] == "John"

    def test_return_404_for_nonexistent_patient(self, client):
        resp = client.get("/patients/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_return_400_for_invalid_uuid(self, client):
        resp = client.get("/patients/not-a-uuid")
        assert resp.status_code == 400


class TestPutPatients:
    def test_update_patient_partially(self, client):
        pid = state["created_patient_id"]
        resp = client.put(
            f"/patients/{pid}",
            json={"first_name": "Jonathan", "email": "jonathan.smith@test.com"},
        )
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["first_name"] == "Jonathan"
        assert data["email"] == "jonathan.smith@test.com"
        assert data["last_name"] == "Smith"  # unchanged

    def test_return_404_for_nonexistent_patient(self, client):
        resp = client.put(
            "/patients/00000000-0000-0000-0000-000000000000",
            json={"first_name": "Test"},
        )
        assert resp.status_code == 404


class TestDeletePatients:
    def test_soft_delete_patient(self, client):
        pid = state["created_patient_id"]
        resp = client.delete(f"/patients/{pid}")
        assert resp.status_code == 200

        data = resp.get_json()
        assert "deleted_at" in data["patient"]
        assert data["patient"]["deleted_at"] is not None

    def test_not_find_soft_deleted_patient_via_get(self, client):
        pid = state["created_patient_id"]
        resp = client.get(f"/patients/{pid}")
        assert resp.status_code == 404

    def test_not_include_soft_deleted_in_list(self, client):
        resp = client.get("/patients")
        assert resp.status_code == 200

        data = resp.get_json()
        found = [p for p in data["patients"] if p["patient_id"] == state["created_patient_id"]]
        assert len(found) == 0


class TestHealthCheck:
    def test_return_healthy_status(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "uptime" in data
