
from datetime import date
from pprint import pprint

from app.database import SessionLocal

from app.services.sales_target_analytics_service import (
    QuotaFilters,
    get_salesperson_performance,
    get_quota_attainment_by_region,
    get_team_quota_summary,
    get_sales_reps_without_target,
)

from app.services.account_analytics_service import (
    AccountSummaryFilters,
    get_account_summaries,
)


def main():

    # Must match the exact target period in sales_targets.
    quota_filters = QuotaFilters(
        period_start=date(2026, 1, 1),
        period_end=date(2026, 12, 31),
    )

    with SessionLocal() as db:

        print("\n========== SALESPERSON PERFORMANCE ==========")

        pprint(
            get_salesperson_performance(
                db,
                quota_filters,
            )
        )

        print("\n========== REGIONAL QUOTA ATTAINMENT ==========")

        pprint(
            get_quota_attainment_by_region(
                db,
                quota_filters,
            )
        )

        print("\n========== TEAM QUOTA SUMMARY ==========")

        pprint(
            get_team_quota_summary(
                db,
                quota_filters,
            )
        )

        print("\n========== SALES REPS WITHOUT TARGETS ==========")

        pprint(
            get_sales_reps_without_target(
                db,
                quota_filters,
            )
        )

        print("\n========== ACCOUNT SUMMARIES ==========")

        account_filters = AccountSummaryFilters()

        pprint(
            get_account_summaries(
                db,
                account_filters,
            )
        )


if __name__ == "__main__":
    main()
