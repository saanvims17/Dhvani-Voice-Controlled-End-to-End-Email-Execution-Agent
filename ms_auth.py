# ms_auth.py

import os
import msal
from dotenv import load_dotenv

load_dotenv()

MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")
MS_TENANT_ID = os.getenv("MS_TENANT_ID", "consumers")

AUTHORITY = f"https://login.microsoftonline.com/{MS_TENANT_ID}"

SCOPES = ["User.Read", "Contacts.Read", "Mail.Send"]

CACHE_FILE = "token_cache.bin"


def load_cache():
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache.deserialize(f.read())
    return cache


def save_cache(cache):
    if cache.has_state_changed:
        with open(CACHE_FILE, "w") as f:
            f.write(cache.serialize())


def get_access_token() -> str:
    if not MS_CLIENT_ID:
        raise RuntimeError("MS_CLIENT_ID is missing in .env")

    cache = load_cache()

    app = msal.PublicClientApplication(
        client_id=MS_CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache,
    )

    accounts = app.get_accounts()

    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            save_cache(cache)
            return result["access_token"]

    flow = app.initiate_device_flow(scopes=SCOPES)

    if "user_code" not in flow:
        raise RuntimeError(f"Device flow failed: {flow}")

    print("\nSign in to Microsoft:")
    print(flow.get("message", "Open the Microsoft device login page and enter the code."))

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise RuntimeError(f"Login failed: {result}")

    save_cache(cache)
    return result["access_token"]