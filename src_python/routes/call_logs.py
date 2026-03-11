from flask import Blueprint, request, jsonify
from src_python.models.call_log import CallLogModel
from src_python.logger import logger

call_logs_bp = Blueprint("call_logs", __name__)


@call_logs_bp.route("/", methods=["GET"])
def list_call_logs():
    """GET /call-logs — List all call logs."""
    try:
        limit = request.args.get("limit", 50, type=int)
        logs = CallLogModel.find_all(limit=limit)
        return jsonify(logs), 200
    except Exception as e:
        logger.error(f"Error listing call logs: {e}")
        return jsonify({"error": "Internal server error"}), 500


@call_logs_bp.route("/patient/<patient_id>", methods=["GET"])
def get_call_logs_by_patient(patient_id):
    """GET /call-logs/patient/:patientId — Get call logs for a specific patient."""
    try:
        logs = CallLogModel.find_by_patient_id(patient_id)
        return jsonify(logs), 200
    except Exception as e:
        logger.error(f"Error retrieving call logs: {e}")
        return jsonify({"error": "Internal server error"}), 500
