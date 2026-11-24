
from datetime import datetime
from zoneinfo import ZoneInfo
from pprint import pprint

from app.database import SessionLocal

from app.services.booking_analytics_service import (
    BookingFilters,
    get_bookings_by_month,
    get_bookings_by_region,
    get_bookings_by_product,
    get_bookings_by_month_region_product,
    get_unallocated_bookings_summary,
)


def main():

    # Reporting period: calendar year 2026
    reporting_timezone = ZoneInfo("Asia/Kolkata")

    filters = BookingFilters(
        start_at=datetime(
            2026, 1, 1,
            tzinfo=reporting_timezone,
        ),

        end_at=datetime(
            2027, 1, 1,
            tzinfo=reporting_timezone,
        ),
    )

    with SessionLocal() as db:

        print("\n========== MONTHLY BOOKINGS ==========")

        monthly = get_bookings_by_month(
            db,
            filters,
        )

        pprint(monthly)

        print("\n========== REGIONAL BOOKINGS ==========")

        regional = get_bookings_by_region(
            db,
            filters,
        )

        pprint(regional)

        print("\n========== PRODUCT BOOKINGS ==========")

        products = get_bookings_by_product(
            db,
            filters,
        )

        pprint(products)

        print("\n========== MONTH + REGION + PRODUCT ==========")

        combined = get_bookings_by_month_region_product(
            db,
            filters,
        )

        pprint(combined)

        print("\n========== UNALLOCATED BOOKINGS ==========")

        unallocated = get_unallocated_bookings_summary(
            db,
            filters,
        )

        pprint(unallocated)


if __name__ == "__main__":
    main()
