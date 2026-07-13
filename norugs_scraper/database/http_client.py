import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class HttpClient:
    def __init__(self, timeout: int = 30):
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                "User-Agent": "NoRugs/1.0"
            },
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def get(self, url: str, params: dict | None = None):
        response = self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def close(self):
        self.client.close()