from datetime import datetime
from typing import List


def generate_months(start_month: str = None, num_months: int = 3) -> List[str]:
    """Generate a list of month strings in YYYYMM format"""
    if start_month:
        try:
            start = datetime.strptime(start_month, "%Y%m")
        except ValueError:
            start = datetime.now().replace(day=1)
    else:
        start = datetime.now().replace(day=1)

    months = []
    year = start.year
    month = start.month

    for i in range(num_months):
        months.append(f"{year}{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1

    return months


def format_price(price: int) -> str:
    """Format price with thousands separator"""
    return f"{price:,}"
