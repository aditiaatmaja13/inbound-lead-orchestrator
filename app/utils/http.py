import requests


def get_json(url: str, params: dict | None = None, headers: dict | None = None, timeout: int = 10) -> dict:
    """
    Centralized HTTP GET helper.

    Handles:
    - headers
    - timeout
    - JSON parsing
    - consistent error handling
    """
    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        print(f"[HTTP] Request failed: {exc}")
        return {}