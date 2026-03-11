from flask import Blueprint, request, jsonify
from src_python.models.patient import PatientModel
from src_python.validation import validate_create_patient, validate_update_patient, validate_patient_id
from src_python.logger import logger

patients_bp = Blueprint("patients", __name__)


@patients_bp.route("/", methods=["GET"])
def list_patients():
    """GET /patients — List all patients with optional filters."""
    try:
        last_name = request.args.get("last_name", "").strip() or None
        date_of_birth = request.args.get("date_of_birth", "").strip() or None
        phone_number = request.args.get("phone_number", "").strip() or None
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 50, type=int)

        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 50

        result = PatientModel.find_all(
            last_name=last_name,
            date_of_birth=date_of_birth,
            phone_number=phone_number,
            page=page,
            limit=limit,
        )
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error listing patients: {e}")
        return jsonify({"error": "Internal server error"}), 500


@patients_bp.route("/<patient_id>", methods=["GET"])
def get_patient(patient_id):
    """GET /patients/:id — Retrieve a single patient by patient_id (UUID)."""
    try:
        errors = validate_patient_id(patient_id)
        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 400

        patient = PatientModel.find_by_id(patient_id)
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        return jsonify(patient), 200
    except Exception as e:
        logger.error(f"Error retrieving patient: {e}, id={patient_id}")
        return jsonify({"error": "Internal server error"}), 500


@patients_bp.route("/", methods=["POST"])
def create_patient():
    """POST /patients — Create a new patient record."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        errors = validate_create_patient(data)
        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 400

        patient = PatientModel.create(data)
        return jsonify(patient), 201
    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        if "CHECK constraint" in str(e):
            return jsonify({"error": "Invalid data: constraint violation", "details": str(e)}), 400
        return jsonify({"error": "Internal server error"}), 500


@patients_bp.route("/<patient_id>", methods=["PUT"])
def update_patient(patient_id):
    """PUT /patients/:id — Update an existing patient record. Partial updates allowed."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        errors = validate_update_patient(patient_id, data)
        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 400

        patient = PatientModel.update(patient_id, data)
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        return jsonify(patient), 200
    except Exception as e:
        logger.error(f"Error updating patient: {e}, id={patient_id}")
        return jsonify({"error": "Internal server error"}), 500


@patients_bp.route("/<patient_id>", methods=["DELETE"])
def delete_patient(patient_id):
    """DELETE /patients/:id — Soft-delete a patient record."""
    try:
        errors = validate_patient_id(patient_id)
        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 400

        patient = PatientModel.soft_delete(patient_id)
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        return jsonify({"message": "Patient record soft-deleted", "patient": patient}), 200
    except Exception as e:
        logger.error(f"Error deleting patient: {e}, id={patient_id}")
        return jsonify({"error": "Internal server error"}), 500
