import hashlib
import threading
import time
from typing import Dict

import requests
from django.conf import settings
from django.core.cache import cache

_thread_local = threading.local()


class FlightAPIClient:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    @property
    def _session(self):
        if not hasattr(_thread_local, "session"):
            _thread_local.session = requests.Session()
        return _thread_local.session

    def _fetch_with_retries(self, url: str, params: Dict) -> Dict:
        """Fetch data with exponential backoff retry logic"""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self._session.get(url, params=params, timeout=60)

                if response.status_code == 200:
                    return response.json()

                last_error = f"HTTP {response.status_code}: {response.reason}"
                wait_time = 2**attempt
                time.sleep(wait_time)

            except requests.exceptions.RequestException as e:
                last_error = str(e)
                wait_time = 2**attempt
                time.sleep(wait_time)

        raise Exception(f"Failed after {self.max_retries} retries: {last_error}")

    def _fetch_cached(self, url: str, params: Dict) -> Dict:
        """Fetch with 1h in-memory cache keyed by url + params"""
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
    ) -> Dict:
        """Fetch flight pricing data for a specific month"""
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

    def fetch_direct_flights(self, inbound: str, outbound: str) -> Dict:
        """Fetch direct flight schedules"""
        params = {"market": "se-sv", "from": inbound, "to": outbound, "triptype": "R"}

        return self._fetch_cached(settings.FLIGHT_SCHEDULE_ENDPOINT, params)
