import re
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from src_python.models.patient import PatientModel
from src_python.models.call_log import CallLogModel
from src_python.vapi.system_prompt import SYSTEM_PROMPT
from src_python.vapi.tool_definitions import get_tool_definitions
from src_python.config import config
from src_python.logger import logger

vapi_webhook_bp = Blueprint("vapi_webhook", __name__)


@vapi_webhook_bp.route("/webhook", methods=["POST"])
def webhook():
    """
    POST /vapi/webhook

    Main webhook endpoint for Vapi. Handles multiple event types:
    - assistant-request: Returns agent configuration when a call comes in
    - tool-calls: Handles tool calls (check_existing_patient, save_patient, update_patient)
    - end-of-call-report: Logs the call transcript/summary after call ends
    - status-update: Handles call status changes

    Vapi webhook docs: https://docs.vapi.ai/server-url/events
    """
    try:
        body = request.get_json(force=True, silent=True) or {}
        message = body.get("message")

        if not message:
            logger.warning(f"Received webhook with no message: {json.dumps(body)}")
            return jsonify({"error": "No message in request body"}), 400

        msg_type = message.get("type", "")
        call_id = (message.get("call") or {}).get("id")
        logger.info(f"Vapi webhook received: {msg_type}, callId={call_id}")

        if msg_type == "assistant-request":
            return handle_assistant_request()
        elif msg_type == "tool-calls":
            return handle_tool_calls(message)
        elif msg_type == "end-of-call-report":
            return handle_end_of_call_report(message)
        elif msg_type == "status-update":
            return handle_status_update(message)
        elif msg_type == "hang":
            logger.info("Call hang event received")
            return jsonify({}), 200
        elif msg_type in ("speech-update", "transcript", "conversation-update", "phone-call-control"):
            return jsonify({}), 200
        else:
            logger.info(f"Unhandled webhook type: {msg_type}")
            return jsonify({}), 200

    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        return jsonify({"error": "Internal webhook error"}), 500


def handle_assistant_request():
    """
    Handle assistant-request: Return the full agent configuration.
    This is called when a new call comes in and Vapi needs to know
    how to configure the assistant for this call.
    """
    logger.info("Returning assistant configuration for new call")

    # Determine our server URL for tool callbacks
    proto = request.headers.get("X-Forwarded-Proto", request.scheme or "http")
    host = request.headers.get("X-Forwarded-Host", request.headers.get("Host", f"localhost:{config['port']}"))
    server_url = f"{proto}://{host}/vapi/webhook"

    logger.info(f"Assistant server URL for tools: {server_url}")

    assistant_config = {
        "assistant": {
            "model": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                ],
                "tools": get_tool_definitions(server_url),
                "temperature": 0.7,
                "maxTokens": 500,
            },
            "voice": {
                "provider": "vapi",
                "voiceId": "Clara",
            },
            "firstMessage": "Hi there! Thank you for calling our clinic. I'm Sarah, and I'll help you get registered as a new patient today. This will just take a few minutes. Could I have your first and last name, please?",
            "endCallFunctionEnabled": True,
            "endCallMessage": "Thank you for registering with us! Have a wonderful day. Goodbye!",
            "transcriber": {
                "provider": "deepgram",
                "model": "nova-2",
                "language": "en-US",
            },
            "recordingEnabled": True,
            "silenceTimeoutSeconds": 30,
            "maxDurationSeconds": 600,
            "backgroundSound": "office",
            "name": "Patient Registration Assistant",
            "serverUrl": server_url,
        },
    }

    return jsonify(assistant_config), 200


def handle_tool_calls(message):
    """
    Handle tool-calls: Process tool calls from the LLM.

    Vapi sends { message: { type: "tool-calls", toolCallList: [...], call: {...} } }
    We must respond with { results: [{ name, toolCallId, result }] }
    See: https://docs.vapi.ai/server-url/events#function-calling-tools
    """
    tool_call_list = message.get("toolCallList") or []
    tool_with_tool_call_list = message.get("toolWithToolCallList") or []
    call = message.get("call") or {}
    call_id = call.get("id")

    # Debug: log raw payload structure to understand Vapi's format
    logger.info(f"Raw tool-calls payload: "
                f"hasToolCallList={bool(tool_call_list)}, "
                f"toolCallListLength={len(tool_call_list)}, "
                f"toolCallListSample={json.dumps(tool_call_list[0]) if tool_call_list else 'none'}, "
                f"hasToolWithToolCallList={bool(tool_with_tool_call_list)}, "
                f"toolWithToolCallListLength={len(tool_with_tool_call_list)}, "
                f"toolWithToolCallListSample={json.dumps(tool_with_tool_call_list[0])[:500] if tool_with_tool_call_list else 'none'}")

    # Normalize Vapi payload formats into a consistent shape
    # toolCallList[]: { id, name, parameters }
    # toolWithToolCallList[]: { name, toolCall: { id, parameters } }
    tool_calls = []

    if tool_call_list:
        for tc in tool_call_list:
            func = tc.get("function") or {}
            func_args = func.get("arguments", {})
            if isinstance(func_args, str):
                try:
                    func_args = json.loads(func_args)
                except (json.JSONDecodeError, TypeError):
                    func_args = {}

            tool_calls.append({
                "id": tc.get("id"),
                "name": tc.get("name") or func.get("name"),
                "arguments": tc.get("parameters") or tc.get("arguments") or func_args or {},
            })
    elif tool_with_tool_call_list:
        for t in tool_with_tool_call_list:
            tool_call = t.get("toolCall") or {}
            func = tool_call.get("function") or {}
            func_args = func.get("arguments", {})
            if isinstance(func_args, str):
                try:
                    func_args = json.loads(func_args)
                except (json.JSONDecodeError, TypeError):
                    func_args = {}

            tool_calls.append({
                "id": tool_call.get("id"),
                "name": func.get("name") or t.get("name"),
                "arguments": tool_call.get("parameters") or func_args or {},
            })

    if not tool_calls:
        logger.warning("Tool-calls event with no tool calls")
        return jsonify({"results": []}), 200

    results = []
    for tc in tool_calls:
        tool_call_id = tc["id"]
        name = tc["name"]
        args = tc["arguments"]
        logger.info(f"Tool call: {name}, toolCallId={tool_call_id}, args={json.dumps(args)}")

        try:
            if name == "check_existing_patient":
                result = _handle_check_existing_patient(args)
            elif name == "save_patient":
                result = _handle_save_patient(args, call_id)
            elif name == "update_patient":
                result = _handle_update_patient(args, call_id)
            else:
                logger.warning(f"Unknown tool: {name}")
                result = {"error": f"Unknown tool: {name}"}

            results.append({
                "toolCallId": tool_call_id,
                "result": json.dumps(result),
            })
        except Exception as e:
            logger.error(f"Tool call error: {name}, error={e}, args={json.dumps(args)}")
            results.append({
                "toolCallId": tool_call_id,
                "result": json.dumps({
                    "success": False,
                    "error": f"Failed to execute {name}: {str(e)}. Please inform the caller there was a temporary issue and ask them to try again.",
                }),
            })

    return jsonify({"results": results}), 200


def _handle_check_existing_patient(params):
    """Check if a patient already exists by phone number. Supports duplicate detection."""
    phone_number = params.get("phone_number")

    if not phone_number:
        return {"exists": False, "message": "No phone number provided"}

    cleaned = re.sub(r'\D', '', phone_number)
    existing = PatientModel.find_by_phone(cleaned)

    if existing:
        logger.info(f"Existing patient found by phone: patient_id={existing['patient_id']}, name={existing['first_name']} {existing['last_name']}")
        return {
            "exists": True,
            "patient_id": existing["patient_id"],
            "first_name": existing["first_name"],
            "last_name": existing["last_name"],
            "message": f"A patient named {existing['first_name']} {existing['last_name']} is already registered with this phone number. Ask if they'd like to update their information instead of creating a new record.",
        }

    return {"exists": False, "message": "No existing patient found. Proceed with new registration."}


def _handle_save_patient(params, call_id):
    """Save a new patient record to the database."""
    # Validate required fields
    required_fields = ["first_name", "last_name", "date_of_birth", "sex", "phone_number", "address_line_1", "city", "state", "zip_code"]
    missing = [f for f in required_fields if not params.get(f)]

    if missing:
        return {
            "success": False,
            "error": f"Missing required fields: {', '.join(missing)}. Please collect these from the caller before saving.",
        }

    # Validate date of birth
    try:
        dob = datetime.strptime(params["date_of_birth"], "%Y-%m-%d")
        if dob > datetime.now():
            return {
                "success": False,
                "error": "Invalid date of birth. Please ask the caller to provide a valid date that is not in the future.",
            }
    except (ValueError, TypeError):
        return {
            "success": False,
            "error": "Invalid date of birth. Please ask the caller to provide a valid date that is not in the future.",
        }

    # Validate phone number
    clean_phone = re.sub(r'\D', '', params["phone_number"])
    if len(clean_phone) != 10:
        return {
            "success": False,
            "error": "Invalid phone number. Must be exactly 10 digits. Please ask the caller to repeat their phone number.",
        }

    # Validate zip code
    if not re.match(r'^\d{5}(-\d{4})?$', params["zip_code"]):
        return {
            "success": False,
            "error": "Invalid ZIP code format. Must be 5 digits or ZIP+4 (e.g., 12345 or 12345-6789).",
        }

    patient = PatientModel.create(params)

    # Log the call
    CallLogModel.create(
        call_id=call_id,
        patient_id=patient["patient_id"],
        caller_phone=clean_phone,
        summary=f"New patient registration: {params['first_name']} {params['last_name']}",
        status="completed",
    )

    logger.info(f"Patient saved via voice agent: patient_id={patient['patient_id']}, call_id={call_id}")

    return {
        "success": True,
        "patient_id": patient["patient_id"],
        "message": f"Successfully registered {params['first_name']} {params['last_name']}. Patient ID: {patient['patient_id']}",
    }


def _handle_update_patient(params, call_id):
    """Update an existing patient record."""
    patient_id = params.get("patient_id")

    if not patient_id:
        return {"success": False, "error": "Patient ID is required for updates."}

    update_data = {k: v for k, v in params.items() if k != "patient_id"}
    patient = PatientModel.update(patient_id, update_data)

    if not patient:
        return {"success": False, "error": "Patient not found. Cannot update."}

    # Log the call
    CallLogModel.create(
        call_id=call_id,
        patient_id=patient_id,
        caller_phone=patient.get("phone_number"),
        summary=f"Patient record updated: {patient['first_name']} {patient['last_name']}. Fields: {', '.join(update_data.keys())}",
        status="completed",
    )

    logger.info(f"Patient updated via voice agent: patient_id={patient_id}, call_id={call_id}")

    return {
        "success": True,
        "patient_id": patient_id,
        "message": f"Successfully updated the record for {patient['first_name']} {patient['last_name']}.",
    }


def handle_end_of_call_report(message):
    """
    Handle end-of-call-report: Store transcript and summary.

    Vapi payload:
    {
      message: {
        type: "end-of-call-report",
        endedReason: "hangup",
        call: { id, ... },
        artifact: {
          transcript: "AI: ... User: ...",
          messages: [{ role, message }],
          recording: { ... }
        }
      }
    }
    """
    call = message.get("call") or {}
    artifact = message.get("artifact") or {}
    ended_reason = message.get("endedReason")

    transcript = artifact.get("transcript")
    messages = artifact.get("messages") or []
    summary = f"Call ended: {ended_reason}. {len(messages)} messages exchanged." if ended_reason else None

    logger.info(f"End of call report received: callId={call.get('id')}, endedReason={ended_reason}, "
                f"transcriptLength={len(transcript) if transcript else 0}, messageCount={len(messages)}")

    # Store transcript linked to patient call log
    if call.get("id"):
        try:
            from src_python.database import get_db
            db = get_db()

            # Update existing call log with transcript
            existing = db.execute("SELECT * FROM call_logs WHERE call_id = ?", (call["id"],)).fetchone()

            if existing:
                db.execute(
                    "UPDATE call_logs SET transcript = ?, summary = ? WHERE call_id = ?",
                    (transcript, summary, call["id"])
                )
                db.commit()
            else:
                # Create a new call log entry if none exists
                customer = call.get("customer") or {}
                caller_phone_raw = customer.get("number", "")
                caller_phone = re.sub(r'\D', '', caller_phone_raw) if caller_phone_raw else None
                CallLogModel.create(
                    call_id=call["id"],
                    caller_phone=caller_phone,
                    transcript=transcript,
                    summary=summary,
                    status="completed",
                )
        except Exception as e:
            logger.error(f"Error saving call report: {e}")

    return jsonify({}), 200


def handle_status_update(message):
    """Handle status-update: Log call status changes."""
    status = message.get("status")
    logger.info(f"Call status update: {status}")
    return jsonify({}), 200
