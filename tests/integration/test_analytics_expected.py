
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.services.revops_query_service import (
    OpportunityFilters,
    get_open_pipeline_summary,
)

from app.services.booking_analytics_service import (
    BookingFilters,
    get_bookings_by_month,
    get_bookings_by_product,
)

from app.services.sales_performance_service import (
    SalesPerformanceFilters,
    get_opportunity_conversion_summary,
    get_win_rate_summary,
    get_average_deal_size,
    get_sales_cycle_summary,
)

from app.services.sales_target_analytics_service import (
    QuotaFilters,
    get_salesperson_performance,
    get_team_quota_summary,
)

from app.services.account_analytics_service import (
    AccountSummaryFilters,
    get_account_summaries,
)


TZ = ZoneInfo("Asia/Kolkata")


def booking_filters():
    return BookingFilters(
        start_at=datetime(2026, 1, 1, tzinfo=TZ),
        end_at=datetime(2026, 3, 1, tzinfo=TZ),
    )


def performance_filters():
    return SalesPerformanceFilters(
        start_at=datetime(2026, 1, 1, tzinfo=TZ),
        end_at=datetime(2026, 3, 1, tzinfo=TZ),
    )


def quota_filters():
    return QuotaFilters(
        period_start=date(2026, 1, 1),
        period_end=date(2026, 3, 31),
    )

def test_pipeline_calculations_match_expected(
    pg_session,
    revenue_scenario,
):

    result = get_open_pipeline_summary(
        pg_session,
        OpportunityFilters(),
    )

    assert result["open_pipeline"] == Decimal("500000.00")

    assert result["weighted_pipeline"] == Decimal("300000.00")

def test_monthly_bookings_match_expected(
    pg_session,
    revenue_scenario,
):

    results = get_bookings_by_month(
        pg_session,
        booking_filters(),
    )

    actual = {
        row["month"].month: row["total_bookings"]
        for row in results
    }

    expected = {
        1: Decimal("900000.00"),
        2: Decimal("600000.00"),
    }

    assert actual == expected

def test_product_booking_allocation_matches_expected(
    pg_session,
    revenue_scenario,
):

    results = get_bookings_by_product(
        pg_session,
        booking_filters(),
    )

    actual = {
        row["sku"]: row["allocated_bookings"]
        for row in results
    }

    expected = {
        "TEST-CRM": Decimal("960000.00"),
        "TEST-ANALYTICS": Decimal("540000.00"),
    }

    assert actual == expected

def test_win_rate_matches_expected(
    pg_session,
    revenue_scenario,
):

    result = get_win_rate_summary(
        pg_session,
        performance_filters(),
    )

    assert result["closed_won"] == 2
    assert result["closed_lost"] == 1
    assert result["win_rate_pct"] == Decimal("66.67")


def test_opportunity_conversion_matches_expected(
    pg_session,
    revenue_scenario,
):

    filters = SalesPerformanceFilters(
        start_at=datetime(2026, 1, 1, tzinfo=TZ),
        end_at=datetime(2026, 2, 1, tzinfo=TZ),
    )

    result = get_opportunity_conversion_summary(
        pg_session,
        filters,
    )

    assert result["created_opportunities"] == 4
    assert result["closed_won"] == 2
    assert result["closed_lost"] == 1
    assert result["still_open"] == 1

    assert result["opportunity_conversion_pct"] == Decimal("50.00")
    assert result["opportunity_resolution_pct"] == Decimal("75.00")

def test_average_deal_size_matches_expected(
    pg_session,
    revenue_scenario,
):

    results = get_average_deal_size(
        pg_session,
        performance_filters(),
    )

    assert len(results) == 1

    result = results[0]

    assert result["currency_code"] == "INR"
    assert result["booking_count"] == 2

    assert result["total_booking_value"] == Decimal("1500000.00")

    assert result["average_deal_size"] == Decimal("750000.00")


def test_sales_cycle_matches_expected(
    pg_session,
    revenue_scenario,
):

    result = get_sales_cycle_summary(
        pg_session,
        performance_filters(),
    )

    assert result["won_opportunity_count"] == 2

    assert result["average_sales_cycle_days"] == Decimal("30.00")

    assert result["minimum_sales_cycle_days"] == Decimal("30.00")

    assert result["maximum_sales_cycle_days"] == Decimal("30.00")

def test_salesperson_quota_matches_expected(
    pg_session,
    revenue_scenario,
):

    results = get_salesperson_performance(
        pg_session,
        quota_filters(),
    )

    actual = {
        row["owner_name"]: row["quota_attainment_pct"]
        for row in results
    }

    expected = {
        "Riya Mehta": Decimal("90.0000"),
        "Kabir Singh": Decimal("120.0000"),
    }

    assert actual == expected

def test_team_quota_matches_expected(
    pg_session,
    revenue_scenario,
):

    results = get_team_quota_summary(
        pg_session,
        quota_filters(),
    )

    result = results[0]

    assert result["total_target"] == Decimal("1500000.00")
    assert result["actual_bookings"] == Decimal("1500000.00")

    assert result["quota_attainment_pct"] == Decimal("100.0000")

def test_account_summary_matches_expected(
    pg_session,
    revenue_scenario,
):

    results = get_account_summaries(
        pg_session,
        AccountSummaryFilters(region="North"),
    )

    northstar = next(
        row
        for row in results
        if row["company_name"] == "Test Northstar Logistics"
    )

    assert northstar["open_pipeline"] == Decimal("500000.00")

    assert northstar["weighted_pipeline"] == Decimal("300000.00")

    assert northstar["total_bookings"] == Decimal("900000.00")

    assert northstar["booking_count"] == 1

    assert northstar["closed_won_count"] == 1
    assert northstar["closed_lost_count"] == 1

    assert northstar["contact_count"] == 1
    assert northstar["completed_activity_count"] == 1