# email_tools.py

"""
Drafts, edits, and sends emails.
- Uses Ollama/Mistral to draft and edit email content
- Uses Microsoft Graph API to send the email
"""

import json
import os
import requests
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from ms_auth import get_access_token

load_dotenv()

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:latest")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)


def _extract_json(text: str) -> dict:
    """
    Try to parse JSON from model output.
    """
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return {}


def draft_email(context: str, recipient_name: str) -> dict:
    """
    Draft a short professional email from spoken context.
    Returns: {"subject": ..., "body": ...}
    """
    prompt = f"""
You are a professional email assistant.

Draft a short professional email from the user's exact intent.

Recipient name: {recipient_name}
User context: {context}

Important rules:
- Preserve the user's meaning accurately
- Do not replace key details with vaguer language
- Do NOT add any new information
- If the user says they are on leave, say they are on leave
- Keep subject short and professional
- Keep body concise and polite
- Do NOT add apologies unless the user explicitly mentions apologizing
- Do NOT add extra politeness or explanations
- Keep the content as close as possible to the original text

Return ONLY valid JSON:
{{
  "subject": "subject here",
  "body": "body here"
}}
"""

    try:
        print("✍️ Drafting email with Mistral...")
        response = llm.invoke(prompt)
        data = _extract_json(response)

        subject = data.get("subject", "").strip()
        body = data.get("body", "").strip()

        if not subject:
            subject = "Following up"
        if not body:
            body = context

        return {"subject": subject, "body": body}

    except Exception as e:
        print(f"❌ Drafting failed: {e}")
        return {
            "subject": "Following up",
            "body": context
        }


def edit_email(current_draft: dict, edit_instructions: str) -> dict:
    """
    Revise an existing draft based on edit instructions.
    Returns: {"subject": ..., "body": ...}
    """
    prompt = f"""
You are a professional email editor.

Current subject: {current_draft["subject"]}
Current body: {current_draft["body"]}

Edit instructions: {edit_instructions}

Return ONLY valid JSON in this exact structure:
{{
  "subject": "revised subject",
  "body": "revised body"
}}

Rules:
- Keep the result professional
- Apply the edit instructions carefully
- Do not include markdown
"""

    try:
        print("✏️ Editing email with Mistral...")
        response = llm.invoke(prompt)
        data = _extract_json(response)

        subject = data.get("subject", current_draft["subject"]).strip()
        body = data.get("body", current_draft["body"]).strip()

        if not subject:
            subject = current_draft["subject"]
        if not body:
            body = current_draft["body"]

        return {"subject": subject, "body": body}

    except Exception as e:
        print(f"❌ Editing failed: {e}")
        return current_draft


def send_email(recipient_email: str, recipient_name: str, subject: str, body: str) -> bool:
    """
    Send email via Microsoft Graph API.
    Returns True on success, False on failure.
    """
    try:
        token = get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        email_payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": body,
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": recipient_email,
                            "name": recipient_name,
                        }
                    }
                ],
            },
            "saveToSentItems": True,
        }

        print(f"📤 Sending email to {recipient_name} ({recipient_email})...")
        response = requests.post(
            f"{GRAPH_BASE}/me/sendMail",
            headers=headers,
            json=email_payload,
            timeout=30,
        )

        if response.status_code == 202:
            print("✅ Email sent successfully!")
            return True

        print(f"❌ Failed to send email: {response.status_code} - {response.text}")
        return False

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False