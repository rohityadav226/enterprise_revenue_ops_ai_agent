
from datetime import date, timedelta
from sqlalchemy import select
from app.database import SessionLocal
from app.models import ProductModel
from app.services.revops_query_service import (
    OpportunityFilters,
    get_opportunity_details,
    get_open_pipeline_summary,
)


def main():

    with SessionLocal() as db:

        product = db.scalar(
            select(ProductModel).where(
                ProductModel.sku == "NFX-REV"
            )
        )

        if product is None:
            raise RuntimeError(
                "NFX-REV product not found. "
                "Check whether the RevOps seed data exists."
            )

        filters = OpportunityFilters(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            product_ids=(product.product_id,),
        )

        opportunities = get_opportunity_details(
            db,
            filters,
            open_only=True,
        )

        pipeline = get_open_pipeline_summary(
            db,
            filters,
        )

        print("\nFILTERED OPPORTUNITIES")

        for opportunity in opportunities:
            print(opportunity)

        print("\nPIPELINE SUMMARY")

        print("Opportunity count:", pipeline["opportunity_count"])
        print("Open pipeline:", pipeline["open_pipeline"])
        print("Weighted pipeline:", pipeline["weighted_pipeline"])


if __name__ == "__main__":
    main()
