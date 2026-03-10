import hashlib
import threading
import time

import requests
from django.conf import settings
from django.core.cache import cache

_thread_local = threading.local()


class FlightAPIClient:
    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries

    @property
    def _session(self) -> requests.Session:
        if not hasattr(_thread_local, "session"):
            _thread_local.session = requests.Session()
        return _thread_local.session

    def _fetch_with_retries(self, url: str, params: dict[str, str]) -> dict:
        """Fetch data with exponential backoff retry logic."""
        last_error: str | None = None

        for attempt in range(self.max_retries):
            try:
                response = self._session.get(url, params=params, timeout=60)
                if response.status_code == 200:
                    return response.json()
                last_error = f"HTTP {response.status_code}: {response.reason}"
            except requests.exceptions.RequestException as e:
                last_error = str(e)
            time.sleep(2**attempt)

        raise Exception(f"Failed after {self.max_retries} retries: {last_error}")

    def _fetch_cached(self, url: str | None, params: dict[str, str]) -> dict:
        """Fetch with 1h in-memory cache keyed by url + sorted params."""
        if not url:
            raise ValueError(
                "API endpoint URL is not configured (got None). Check FLIGHT_CALENDAR_ENDPOINT and FLIGHT_SCHEDULE_ENDPOINT in your environment."
            )
        key_str = url + ":" + ":".join(f"{k}={v}" for k, v in sorted(params.items()))
        cache_key = "sas_" + hashlib.md5(key_str.encode()).hexdigest()
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        result = self._fetch_with_retries(url, params)
        cache.set(cache_key, result, 3600)
        return result

    def fetch_monthly_flights(
        self, month: str, inbound: str, outbound: str, promo: str = ""
    ) -> dict:
        """Fetch flight pricing data for a specific month."""
        params = {
            "cepId": promo,
            "flow": "",
            "from": inbound,
            "market": "se-sv",
            "month": f"{month},{month}",
            "product": "All,All",
            "to": outbound,
            "type": "adults-children",
        }
        return self._fetch_cached(settings.FLIGHT_CALENDAR_ENDPOINT, params)

    def fetch_direct_flights(self, inbound: str, outbound: str) -> dict:
        """Fetch direct flight schedules."""
        params = {"market": "se-sv", "from": inbound, "to": outbound, "triptype": "R"}
        return self._fetch_cached(settings.FLIGHT_SCHEDULE_ENDPOINT, params)
