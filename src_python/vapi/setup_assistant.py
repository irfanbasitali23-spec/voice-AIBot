"""
Vapi Assistant Setup Script

Run this script once to create the Vapi assistant and configure it
to use your webhook server. This avoids using the assistant-request
webhook and instead creates a persistent assistant in Vapi.

Usage: python -m src_python.vapi.setup_assistant <YOUR_WEBHOOK_BASE_URL>
Example: python -m src_python.vapi.setup_assistant https://your-app.onrender.com
"""
import sys
import json
import requests
from src_python.config import config
from src_python.vapi.system_prompt import SYSTEM_PROMPT
from src_python.vapi.tool_definitions import get_tool_definitions


def setup_assistant(webhook_base_url):
    if not config["vapi"]["api_key"]:
        print("Error: VAPI_API_KEY not set in .env file")
        sys.exit(1)

    if not webhook_base_url:
        print("Usage: python -m src_python.vapi.setup_assistant <WEBHOOK_BASE_URL>")
        print("Example: python -m src_python.vapi.setup_assistant https://your-app.onrender.com")
        sys.exit(1)

    server_url = f"{webhook_base_url}/vapi/webhook"
    print(f"Setting up Vapi assistant with webhook: {server_url}")

    assistant_payload = {
        "name": "Patient Registration Assistant",
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
        "firstMessage": "Hi there! Thank you for calling our clinic. I'm Sarah, and I'll help you get registered as a new patient today. This will just take a few minutes. Let's get started — could I have your first and last name, please?",
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
        "serverUrl": server_url,
    }

    if config["vapi"]["webhook_secret"]:
        assistant_payload["serverUrlSecret"] = config["vapi"]["webhook_secret"]

    try:
        resp = requests.post(
            "https://api.vapi.ai/assistant",
            headers={
                "Authorization": f"Bearer {config['vapi']['api_key']}",
                "Content-Type": "application/json",
            },
            json=assistant_payload,
        )

        if resp.status_code >= 400:
            raise Exception(f"Vapi API error {resp.status_code}: {resp.text}")

        assistant = resp.json()
        print(f"\nAssistant created successfully!")
        print(f"   Assistant ID: {assistant['id']}")
        print(f"   Name: {assistant['name']}")
        print(f"   Webhook URL: {server_url}")

        # Now link the assistant to the phone number if configured
        phone_number_id = config["vapi"]["phone_number_id"]
        if phone_number_id:
            print(f"\nLinking assistant to phone number {phone_number_id}...")

            phone_resp = requests.patch(
                f"https://api.vapi.ai/phone-number/{phone_number_id}",
                headers={
                    "Authorization": f"Bearer {config['vapi']['api_key']}",
                    "Content-Type": "application/json",
                },
                json={"assistantId": assistant["id"]},
            )

            if phone_resp.status_code >= 400:
                print(f"Warning: Could not link to phone number: {phone_resp.text}")
                print("You can manually link the assistant to a phone number in the Vapi dashboard.")
            else:
                phone_data = phone_resp.json()
                print(f"Assistant linked to phone number: {phone_data.get('number', phone_number_id)}")
        else:
            print("\nNote: No VAPI_PHONE_NUMBER_ID set. Link the assistant to a phone number in the Vapi dashboard.")
            print("Or buy a new number via Vapi dashboard and set VAPI_PHONE_NUMBER_ID in your .env")

        print("\n--- Setup Complete ---")
        print(f"Save this Assistant ID in your records: {assistant['id']}")

        return assistant

    except Exception as e:
        print(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else None
    setup_assistant(url)
