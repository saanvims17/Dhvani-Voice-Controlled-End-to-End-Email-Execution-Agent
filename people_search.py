# people_search.py

import json
import os
import requests
from ms_auth import get_access_token

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def search_contacts(query: str) -> list[dict]:
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    response = requests.get(
        f"{GRAPH_BASE}/me/contacts?$top=200",
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    results = []
    q = query.strip().lower()

    for contact in data.get("value", []):
        name = (contact.get("displayName") or "").strip()
        emails = contact.get("emailAddresses", []) or []

        email = ""
        if emails and isinstance(emails, list):
            first = emails[0]
            if isinstance(first, dict):
                email = (first.get("address") or "").strip()

        haystacks = [name.lower(), email.lower()]
        if any(q in h for h in haystacks if h):
            results.append({
                "name": name,
                "email": email,
                "job_title": "",
                "department": "",
            })

    return results


def search_local_contacts(name: str) -> list[dict]:
    if not os.path.exists("contacts.json"):
        return []

    with open("contacts.json", "r") as f:
        contacts = json.load(f)

    key = name.strip().lower()
    if key in contacts:
        return [{
            "name": name,
            "email": contacts[key],
            "job_title": "",
            "department": "",
        }]

    return []


def resolve_recipient(name: str) -> list[dict]:
    matches = search_contacts(name)

    clean_matches = [m for m in matches if m.get("email")]
    if clean_matches:
        return clean_matches

    return search_local_contacts(name)