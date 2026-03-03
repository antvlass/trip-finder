import time
from typing import Dict

import requests


class FlightAPIClient:
    def __init__(self, base_url: str, max_retries: int = 3):
        self.base_url = base_url
        self.session = requests.Session()
        self.max_retries = max_retries

    def _fetch_with_retries(self, endpoint: str, params: Dict) -> Dict:
        """Fetch data with exponential backoff retry logic"""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url, params=params, timeout=60)

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

        return self._fetch_with_retries("/flights/calendar/prices", params)

    def fetch_direct_flights(self, inbound: str, outbound: str) -> Dict:
        """Fetch direct flight schedules"""
        params = {"market": "se-sv", "from": inbound, "to": outbound, "triptype": "R"}

        return self._fetch_with_retries("/flights/schedule/direct", params)
