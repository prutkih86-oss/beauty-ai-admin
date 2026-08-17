"""
Thin client for the Beauty AI backend API.

Handles JWT login (POST /api/users/token/) and wraps GET/POST/PUT/PATCH/DELETE
with the Authorization header attached. Caches the access token in memory
for the lifetime of the running app; re-authenticates if a request comes
back 401.
"""

import requests

from config import API_BASE_URL, API_EMAIL, API_PASSWORD


class ApiAuthError(Exception):
    """Raised when login fails or credentials are missing."""


_access_token: str | None = None


def _login() -> str:
    global _access_token

    if not API_EMAIL or not API_PASSWORD:
        raise ApiAuthError(
            "API_EMAIL / API_PASSWORD are not set. "
            "Ask the backend for admin credentials, then set them as "
            "environment variables before starting the app."
        )

    response = requests.post(
        f"{API_BASE_URL}/api/users/token/",
        json={"email": API_EMAIL, "password": API_PASSWORD},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    # Adjust the key name here once we see the real response shape
    # (commonly "access", sometimes "access_token").
    _access_token = data.get("access") or data.get("access_token")
    if not _access_token:
        raise ApiAuthError(f"Login succeeded but no access token in response: {data}")

    return _access_token


def _headers() -> dict:
    global _access_token
    if _access_token is None:
        _login()
    return {"Authorization": f"Bearer {_access_token}"}


def _request(method: str, path: str, **kwargs) -> requests.Response:
    global _access_token
    url = f"{API_BASE_URL}{path}"

    response = requests.request(method, url, headers=_headers(), timeout=10, **kwargs)

    if response.status_code == 401:
        # Token expired or invalid — re-login once and retry.
        _access_token = None
        response = requests.request(method, url, headers=_headers(), timeout=10, **kwargs)

    response.raise_for_status()
    return response


def api_get(path: str, params: dict | None = None) -> dict:
    return _request("GET", path, params=params or {}).json()


def api_post(path: str, payload: dict) -> dict:
    return _request("POST", path, json=payload).json()


def api_put(path: str, payload: dict) -> dict:
    return _request("PUT", path, json=payload).json()


def api_patch(path: str, payload: dict) -> dict:
    return _request("PATCH", path, json=payload).json()


def api_delete(path: str) -> None:
    _request("DELETE", path)