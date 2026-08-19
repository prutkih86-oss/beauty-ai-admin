"""
Thin client for the Beauty AI backend API.

Handles JWT login and authenticated API requests.
"""

import requests

from config import (
    API_BASE_URL,
    API_EMAIL,
    API_PASSWORD,
    VERIFY_SSL,
)


class ApiAuthError(Exception):
    """Raised when login fails or credentials are missing."""


_access_token: str | None = None


def _login() -> str:
    global _access_token

    if not API_EMAIL or not API_PASSWORD:
        raise ApiAuthError(
            "API_EMAIL / API_PASSWORD are not set in .env"
        )

    response = requests.post(
        f"{API_BASE_URL}/api/users/token/",
        json={
            "email": API_EMAIL,
            "password": API_PASSWORD,
        },
        timeout=10,
        verify=VERIFY_SSL,
    )

    response.raise_for_status()

    data = response.json()

    _access_token = (
        data.get("access")
        or data.get("access_token")
    )

    if not _access_token:
        raise ApiAuthError(
            f"Login succeeded but no access token in response: {data}"
        )

    return _access_token


def _headers() -> dict:
    global _access_token

    if _access_token is None:
        _login()

    return {
        "Authorization": f"Bearer {_access_token}",
        "Accept": "application/json",
    }


def _request(
    method: str,
    path: str,
    **kwargs
) -> requests.Response:

    global _access_token

    url = f"{API_BASE_URL}{path}"

    response = requests.request(
        method,
        url,
        headers=_headers(),
        timeout=10,
        verify=VERIFY_SSL,
        **kwargs,
    )

    # Якщо JWT протух — отримуємо новий і повторюємо запит
    if response.status_code == 401:
        _access_token = None

        response = requests.request(
            method,
            url,
            headers=_headers(),
            timeout=10,
            verify=VERIFY_SSL,
            **kwargs,
        )

    response.raise_for_status()

    return response


def api_get(
    path: str,
    params: dict | None = None
):
    return _request(
        "GET",
        path,
        params=params or {},
    ).json()


def api_post(
    path: str,
    payload: dict
):
    response = _request(
        "POST",
        path,
        json=payload,
    )

    if not response.content:
        return {}

    return response.json()


def api_put(
    path: str,
    payload: dict
):
    response = _request(
        "PUT",
        path,
        json=payload,
    )

    if not response.content:
        return {}

    return response.json()


def api_patch(
    path: str,
    payload: dict
):
    response = _request(
        "PATCH",
        path,
        json=payload,
    )

    if not response.content:
        return {}

    return response.json()


def api_delete(
    path: str
) -> None:

    _request(
        "DELETE",
        path,
    )