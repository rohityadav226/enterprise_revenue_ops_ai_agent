
from datetime import datetime, timezone
from pprint import pprint

from app.database import SessionLocal

from app.services.revops_query_service import (
    OpportunityFilters,
)

from app.services.pipeline_analytics_service import (
    get_pipeline_overview,
    get_pipeline_stage_distribution,
    get_opportunity_ageing,
    get_opportunity_ageing_summary,
    get_at_risk_opportunities,
)


def main():

    # No filters means all open opportunities.
    filters = OpportunityFilters()

    as_of = datetime.now(timezone.utc)

    with SessionLocal() as db:

        print("\n========== PIPELINE OVERVIEW ==========")

        overview = get_pipeline_overview(
            db,
            filters,
        )

        pprint(overview)

        print("\n========== PIPELINE STAGE DISTRIBUTION ==========")

        stage_distribution = get_pipeline_stage_distribution(
            db,
            filters,
        )

        pprint(stage_distribution)

        print("\n========== OPPORTUNITY AGEING ==========")

        ageing = get_opportunity_ageing(
            db,
            filters,
            as_of=as_of,
        )

        pprint(ageing)

        print("\n========== AGEING SUMMARY ==========")

        ageing_summary = get_opportunity_ageing_summary(
            db,
            filters,
            as_of=as_of,
        )

        pprint(ageing_summary)

        print("\n========== AT-RISK OPPORTUNITIES ==========")

        at_risk = get_at_risk_opportunities(
            db,
            filters,
            min_age_days=60,
            as_of=as_of,
        )

        pprint(at_risk)


if __name__ == "__main__":
    main()
