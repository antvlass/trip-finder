from datetime import datetime
from typing import Dict, List, Optional


class TripFinder:
    @staticmethod
    def effective_normal(price: int, normal_price: Optional[int]) -> int:
        """Returns the normal price if available, otherwise the total price"""
        return normal_price if normal_price is not None else price

    @staticmethod
    def get_leg_prices(detail: Dict, combo_key: str) -> tuple:
        """Get total price and normal price for a flight leg"""
        combi_price = detail.get("combiPrice", {})
        if combi_price and combo_key in combi_price:
            cp = combi_price[combo_key]
            total = cp["totalPrice"]
            normal = TripFinder.effective_normal(total, cp.get("normalPrice"))
            return total, normal

        total = detail["totalPrice"]
        normal = TripFinder.effective_normal(total, detail.get("normalPrice"))
        return total, normal

    @staticmethod
    def is_weekend(outbound: datetime, inbound: datetime) -> bool:
        """Check if a trip occurs on a weekend (Friday-Monday)"""
        return outbound.weekday() in [4, 5] and inbound.weekday() in [  # Friday or Saturday
            6,
            0,
        ]  # Sunday or Monday

    @staticmethod
    def contains(dates: List[str], date: str) -> bool:
        """Check if a date is in the list"""
        return date in dates

    @staticmethod
    def merge_flights_data(data_list: List[Dict]) -> Dict:
        """Merge multiple flight data dictionaries into one"""
        merged = {"outbound": {}, "inbound": {}}

        for data in data_list:
            merged["outbound"].update(data.get("outbound", {}))
            merged["inbound"].update(data.get("inbound", {}))

        return merged

    @staticmethod
    def find_cheapest(
        all_flights: Dict,
        direct_flights: Dict,
        duration_min: int,
        duration_max: int,
        only_weekends: bool = False,
        max_results: int = 10,
    ) -> List[Dict]:
        """Find the cheapest trips matching the criteria"""
        trips = []

        for outbound_date, outbound_details in all_flights.get("outbound", {}).items():
            outbound_month = outbound_date[:6]
            direct_dates = direct_flights.get("outbound", {}).get(outbound_month, [])

            if not direct_dates or outbound_date not in direct_dates:
                continue

            try:
                outbound = datetime.strptime(outbound_date, "%Y%m%d")
            except ValueError:
                continue

            for inbound_date, inbound_details in all_flights.get("inbound", {}).items():
                try:
                    inbound = datetime.strptime(inbound_date, "%Y%m%d")
                except ValueError:
                    continue

                duration = (inbound - outbound).days
                if duration < duration_min or duration > duration_max:
                    continue

                if only_weekends and not TripFinder.is_weekend(outbound, inbound):
                    continue

                inbound_month = inbound_date[:6]
                direct_inbound_dates = direct_flights.get("inbound", {}).get(inbound_month, [])

                if not direct_inbound_dates or inbound_date not in direct_inbound_dates:
                    continue

                outbound_price, outbound_normal = TripFinder.get_leg_prices(
                    outbound_details, inbound_date
                )
                inbound_price, inbound_normal = TripFinder.get_leg_prices(
                    inbound_details, outbound_date
                )

                total_price = outbound_price + inbound_price
                total_normal = outbound_normal + inbound_normal
                discount = 0.0
                if total_normal > 0:
                    discount = 100.0 * (total_normal - total_price) / total_normal

                trips.append(
                    {
                        "outbound": outbound,
                        "inbound": inbound,
                        "price": total_price,
                        "normal_price": total_normal,
                        "discount": discount,
                        "duration": duration,
                    }
                )

        trips.sort(key=lambda x: x["price"])

        if len(trips) > max_results:
            return trips[:max_results]

        return trips
