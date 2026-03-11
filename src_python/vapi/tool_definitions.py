"""
Tool definitions for the Vapi voice agent.

These tools are called by the LLM during the phone conversation
to interact with our backend (check duplicates, save patient data).

Vapi custom tool format:
- type: "function"
- function: { name, description, parameters }
- server: { url } — Vapi sends tool-calls to this URL

When used in the assistant-request webhook response, the server URL
is the same webhook URL (tools are routed through the same endpoint).

Docs: https://docs.vapi.ai/tools/custom-tools
"""


def get_tool_definitions(server_url):
    """Generate tool definitions with the server URL injected.

    Args:
        server_url: The webhook URL where Vapi sends tool-call events.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "check_existing_patient",
                "description": "Check if a patient already exists in the system by their phone number. Call this at the start of the conversation to detect returning callers and offer to update their record instead of creating a new one.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone_number": {
                            "type": "string",
                            "description": "The 10-digit U.S. phone number to look up (digits only, no formatting)",
                        },
                    },
                    "required": ["phone_number"],
                },
            },
            "server": {"url": server_url},
        },
        {
            "type": "function",
            "function": {
                "name": "save_patient",
                "description": "Save a new patient registration record to the database. Call this AFTER the caller has confirmed all their information is correct. All required fields must be provided.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "first_name": {
                            "type": "string",
                            "description": "Patient first name (1-50 chars, letters/hyphens/apostrophes)",
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Patient last name (1-50 chars, letters/hyphens/apostrophes)",
                        },
                        "date_of_birth": {
                            "type": "string",
                            "description": "Date of birth in YYYY-MM-DD format",
                        },
                        "sex": {
                            "type": "string",
                            "enum": ["Male", "Female", "Other", "Decline to Answer"],
                            "description": "Patient sex for medical records",
                        },
                        "phone_number": {
                            "type": "string",
                            "description": "10-digit U.S. phone number (digits only)",
                        },
                        "address_line_1": {
                            "type": "string",
                            "description": "Street address",
                        },
                        "address_line_2": {
                            "type": "string",
                            "description": "Apartment, suite, or unit number (optional)",
                        },
                        "city": {
                            "type": "string",
                            "description": "City name",
                        },
                        "state": {
                            "type": "string",
                            "description": "2-letter U.S. state abbreviation (e.g., TX, CA, NY)",
                        },
                        "zip_code": {
                            "type": "string",
                            "description": "5-digit or ZIP+4 U.S. ZIP code",
                        },
                        "email": {
                            "type": "string",
                            "description": "Email address (optional)",
                        },
                        "insurance_provider": {
                            "type": "string",
                            "description": "Insurance company name (optional)",
                        },
                        "insurance_member_id": {
                            "type": "string",
                            "description": "Insurance member/subscriber ID (optional)",
                        },
                        "preferred_language": {
                            "type": "string",
                            "description": "Preferred language, defaults to English (optional)",
                        },
                        "emergency_contact_name": {
                            "type": "string",
                            "description": "Emergency contact full name (optional)",
                        },
                        "emergency_contact_phone": {
                            "type": "string",
                            "description": "Emergency contact 10-digit phone number (optional)",
                        },
                    },
                    "required": [
                        "first_name", "last_name", "date_of_birth", "sex",
                        "phone_number", "address_line_1", "city", "state", "zip_code",
                    ],
                },
            },
            "server": {"url": server_url},
        },
        {
            "type": "function",
            "function": {
                "name": "update_patient",
                "description": "Update an existing patient record. Use this when a returning caller wants to update their information. Only provide the fields that need to be changed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "The UUID of the existing patient to update",
                        },
                        "first_name": {"type": "string", "description": "Updated first name"},
                        "last_name": {"type": "string", "description": "Updated last name"},
                        "date_of_birth": {"type": "string", "description": "Updated DOB in YYYY-MM-DD"},
                        "sex": {"type": "string", "enum": ["Male", "Female", "Other", "Decline to Answer"]},
                        "phone_number": {"type": "string", "description": "Updated 10-digit phone"},
                        "address_line_1": {"type": "string"},
                        "address_line_2": {"type": "string"},
                        "city": {"type": "string"},
                        "state": {"type": "string"},
                        "zip_code": {"type": "string"},
                        "email": {"type": "string"},
                        "insurance_provider": {"type": "string"},
                        "insurance_member_id": {"type": "string"},
                        "preferred_language": {"type": "string"},
                        "emergency_contact_name": {"type": "string"},
                        "emergency_contact_phone": {"type": "string"},
                    },
                    "required": ["patient_id"],
                },
            },
            "server": {"url": server_url},
        },
    ]
