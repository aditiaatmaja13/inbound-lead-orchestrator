import time
from typing import Any

import requests


def get_json(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: int = 20,
    retries: int = 3,
    backoff_seconds: int = 2,
) -> Any:
    """
    Centralized HTTP GET helper with retry support.

    Returns parsed JSON on success.
    Returns {} if all attempts fail.
    """

    for attempt in range(retries + 1):
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
            print(f"[HTTP] Request failed on attempt {attempt + 1}: {exc}")

            if attempt < retries:
                time.sleep(backoff_seconds)

    return {}