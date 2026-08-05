from __future__ import annotations

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter


class ApiClient:
    def __init__(self, timeout_seconds: float = 30) -> None:
        self.client = httpx.Client(
            timeout=timeout_seconds,
            headers={"User-Agent": "NoRugs/1.0 (cryptocurrency risk research)"},
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=1, max=20),
        reraise=True,
    )
    def get_json(
        self,
        url: str,
        *,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> object:
        response = self.client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
