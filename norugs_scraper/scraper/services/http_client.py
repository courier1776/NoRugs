from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class HttpClient:
    def __init__(self, timeout: int = 30) -> None:
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                "User-Agent": "NoRugs/1.0",
                "Accept": "application/json",
            },
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=2,
            max=10,
        ),
        reraise=True,
    )
    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any]:
        response = self.client.get(
            url,
            params=params,
            headers=headers,
        )

        response.raise_for_status()

        return response.json()

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()