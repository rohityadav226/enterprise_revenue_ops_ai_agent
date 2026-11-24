
from datetime import datetime
from zoneinfo import ZoneInfo
from pprint import pprint

from app.database import SessionLocal

from app.services.sales_performance_service import (
    SalesPerformanceFilters,
    get_opportunity_conversion_summary,
    get_win_rate_summary,
    get_win_rate_by_region,
    get_win_rate_by_owner,
    get_average_deal_size,
    get_average_deal_size_by_region,
    get_average_deal_size_by_owner,
    get_sales_cycle_summary,
    get_sales_cycle_by_region,
    get_sales_cycle_by_owner,
    get_invalid_sales_cycle_records,
)


def main():

    reporting_timezone = ZoneInfo("Asia/Kolkata")

    filters = SalesPerformanceFilters(
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

        print("\n========== OPPORTUNITY CONVERSION ==========")

        conversion = get_opportunity_conversion_summary(
            db,
            filters,
        )

        pprint(conversion)

        print("\n========== WIN RATE ==========")

        win_rate = get_win_rate_summary(
            db,
            filters,
        )

        pprint(win_rate)

        print("\n========== WIN RATE BY REGION ==========")

        pprint(
            get_win_rate_by_region(db, filters)
        )

        print("\n========== WIN RATE BY OWNER ==========")

        pprint(
            get_win_rate_by_owner(db, filters)
        )

        print("\n========== AVERAGE DEAL SIZE ==========")

        pprint(
            get_average_deal_size(db, filters)
        )

        print("\n========== AVERAGE DEAL SIZE BY REGION ==========")

        pprint(
            get_average_deal_size_by_region(db, filters)
        )

        print("\n========== AVERAGE DEAL SIZE BY OWNER ==========")

        pprint(
            get_average_deal_size_by_owner(db, filters)
        )

        print("\n========== INVALID SALES CYCLE RECORDS ==========")

        invalid_records = get_invalid_sales_cycle_records(
            db,
            filters,
        )

        pprint(invalid_records)

        if invalid_records:
            print(
                "\nWARNING: Correct invalid timestamps "
                "before trusting sales cycle results."
            )
        else:

            print("\n========== SALES CYCLE ==========")

            pprint(
                get_sales_cycle_summary(db, filters)
            )

            print(
                "\n========== SALES CYCLE BY REGION =========="
            )

            pprint(
                get_sales_cycle_by_region(db, filters)
            )

            print(
                "\n========== SALES CYCLE BY OWNER =========="
            )

            pprint(
                get_sales_cycle_by_owner(db, filters)
            )


if __name__ == "__main__":
    main()
