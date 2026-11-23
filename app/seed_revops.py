
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from secrets import token_urlsafe

from sqlalchemy import select

from app.database import SessionLocal
from app.models import (
    UserModel,
    AccountModel,
    ContactModel,
    ProductModel,
    OpportunityModel,
    OpportunityLineItemModel,
    SalesActivityModel,
    SalesTargetModel,
    BookingModel,
)
from app.security import hash_password


def get_or_create(db, model, lookup, values):
    """
    Retrieve an existing record or create a new one.

    This makes the seed script safe to run more than once.
    """
    record = db.scalar(
        select(model).filter_by(**lookup)
    )

    if record is not None:
        return record

    record = model(**lookup, **values)
    db.add(record)
    db.flush()

    return record


def seed_users(db):
    manager = get_or_create(
        db,
        UserModel,
        {"username": "demo_manager"},
        {
            "hashed_password": hash_password(token_urlsafe(32)),
            "full_name": "Aarav Sharma",
            "role": "sales_manager",
            "region": "North",
            "is_active": True,
        },
    )

    sales_people = {}

    demo_reps = [
        ("demo_rep_01", "Riya Mehta", "North"),
        ("demo_rep_02", "Kabir Singh", "West"),
        ("demo_rep_03", "Ananya Rao", "South"),
    ]

    for username, full_name, region in demo_reps:
        rep = get_or_create(
            db,
            UserModel,
            {"username": username},
            {
                "hashed_password": hash_password(token_urlsafe(32)),
                "full_name": full_name,
                "role": "sales_rep",
                "region": region,
                "manager_id": manager.user_id,
                "is_active": True,
            },
        )

        sales_people[username] = rep

    return manager, sales_people


def seed_accounts(db, sales_people):
    account_data = [
        ("Northstar Logistics", "Logistics", "India", "customer"),
        ("BluePeak Analytics", "Technology", "India", "prospect"),
        ("Meridian Health Systems", "Healthcare", "India", "prospect"),
        ("Vertex Manufacturing", "Manufacturing", "India", "customer"),
        ("CloudHarbor Financial", "Financial Services", "India", "prospect"),
        ("Summit Retail Group", "Retail", "India", "customer"),
        ("Orion Energy Solutions", "Energy", "India", "prospect"),
        ("MapleWorks Consulting", "Professional Services", "India", "customer"),
    ]

    reps = list(sales_people.values())
    accounts = {}

    for index, (name, industry, country, status) in enumerate(account_data):
        rep = reps[index % len(reps)]

        account = get_or_create(
            db,
            AccountModel,
            {"company_name": name},
            {
                "industry": industry,
                "country": country,
                "account_status": status,
                "owner_id": rep.user_id,
                "website": (
                    "https://"
                    + name.lower().replace(" ", "")
                    + ".example"
                ),
            },
        )

        accounts[name] = account

    return accounts


def seed_contacts(db, accounts):
    contact_data = [
        ("Aditi", "Shah", "Chief Technology Officer"),
        ("Rahul", "Verma", "VP of Operations"),
    ]

    contacts = {}

    for account_name, account in accounts.items():
        account_contacts = []

        for first_name, last_name, job_title in contact_data:
            email = (
                f"{first_name.lower()}.{last_name.lower()}."
                f"{account_name.lower().replace(' ', '')}@example.com"
            )

            contact = get_or_create(
                db,
                ContactModel,
                {
                    "account_id": account.account_id,
                    "email": email,
                },
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "job_title": job_title,
                    "is_primary": first_name == "Aditi",
                },
            )

            account_contacts.append(contact)

        contacts[account_name] = account_contacts

    return contacts


def seed_products(db):
    product_data = [
        ("NFX-CRM", "NexusFlow CRM", "Customer relationship management", "CRM", "450000.00"),
        ("NFX-REV", "Revenue Intelligence", "Revenue analytics platform", "Analytics", "650000.00"),
        ("NFX-FORE", "Forecasting Pro", "Sales forecasting software", "Forecasting", "800000.00"),
        ("NFX-DATA", "Data Integration Suite", "Enterprise data integration", "Integration", "550000.00"),
        ("NFX-WORK", "Workflow Automation", "Business workflow automation", "Automation", "350000.00"),
    ]

    products = {}

    for sku, name, description, category, price in product_data:
        product = get_or_create(
            db,
            ProductModel,
            {"sku": sku},
            {
                "product_name": name,
                "description": description,
                "category": category,
                "list_price": Decimal(price),
                "currency_code": "INR",
                "is_active": True,
            },
        )

        products[sku] = product

    return products


def seed_opportunities(
    db,
    accounts,
    contacts,
    sales_people,
    products,
    manager,
):
    now = datetime.now(timezone.utc)

    opportunity_data = [
        (
            "Northstar Logistics",
            "demo_rep_01",
            "CRM Transformation 2026",
            "closed_won",
            "100.00",
            "NFX-CRM",
            50,
            "420000.00",
            45,
        ),
        (
            "BluePeak Analytics",
            "demo_rep_02",
            "Revenue Intelligence Rollout",
            "proposal",
            "60.00",
            "NFX-REV",
            10,
            "600000.00",
            30,
        ),
        (
            "Meridian Health Systems",
            "demo_rep_03",
            "Forecasting Pilot",
            "discovery",
            "30.00",
            "NFX-FORE",
            5,
            "750000.00",
            60,
        ),
        (
            "Vertex Manufacturing",
            "demo_rep_01",
            "Data Integration Deployment",
            "closed_won",
            "100.00",
            "NFX-DATA",
            15,
            "500000.00",
            35,
        ),
        (
            "CloudHarbor Financial",
            "demo_rep_02",
            "Workflow Automation Program",
            "negotiation",
            "85.00",
            "NFX-WORK",
            30,
            "320000.00",
            20,
        ),
        (
            "Summit Retail Group",
            "demo_rep_03",
            "CRM Expansion",
            "closed_lost",
            "0.00",
            "NFX-CRM",
            12,
            "400000.00",
            55,
        ),
        (
            "Orion Energy Solutions",
            "demo_rep_01",
            "Revenue Intelligence Deployment",
            "qualification",
            "10.00",
            "NFX-REV",
            8,
            "580000.00",
            75,
        ),
        (
            "MapleWorks Consulting",
            "demo_rep_02",
            "Forecasting Enterprise Package",
            "closed_won",
            "100.00",
            "NFX-FORE",
            8,
            "700000.00",
            65,
        ),
        (
            "Northstar Logistics",
            "demo_rep_03",
            "Workflow Expansion",
            "proposal",
            "60.00",
            "NFX-WORK",
            15,
            "300000.00",
            40,
        ),
        (
            "BluePeak Analytics",
            "demo_rep_01",
            "Data Platform Modernization",
            "discovery",
            "30.00",
            "NFX-DATA",
            6,
            "480000.00",
            50,
        ),
    ]

    opportunities = []

    for (
        account_name,
        owner_username,
        opportunity_name,
        stage,
        probability,
        sku,
        quantity,
        unit_price,
        days_offset,
    ) in opportunity_data:

        account = accounts[account_name]
        owner = sales_people[owner_username]
        product = products[sku]

        is_closed = stage in ("closed_won", "closed_lost")
        closed_at = (
            now - timedelta(days=days_offset)
            if is_closed
            else None
        )

        opportunity = get_or_create(
            db,
            OpportunityModel,
            {
                "account_id": account.account_id,
                "opportunity_name": opportunity_name,
            },
            {
                "owner_id": owner.user_id,
                "stage": stage,
                "probability_pct": Decimal(probability),
                "expected_close_date": (
                    date.today() - timedelta(days=days_offset)
                    if is_closed
                    else date.today() + timedelta(days=days_offset)
                ),
                "currency_code": "INR",
                "closed_at": closed_at,
            },
        )

        get_or_create(
            db,
            OpportunityLineItemModel,
            {
                "opportunity_id": opportunity.opportunity_id,
                "product_id": product.product_id,
            },
            {
                "quantity": quantity,
                "agreed_unit_price": Decimal(unit_price),
            },
        )

        opportunities.append(opportunity)

        if stage == "closed_won":
            contract_value = (
                Decimal(quantity) * Decimal(unit_price)
            )

            get_or_create(
                db,
                BookingModel,
                {"opportunity_id": opportunity.opportunity_id},
                {
                    "recorded_by_id": manager.user_id,
                    "contract_value": contract_value,
                    "currency_code": "INR",
                    "booked_at": closed_at,
                },
            )

    return opportunities


def seed_activities(db, opportunities, contacts, accounts):
    now = datetime.now(timezone.utc)

    for opportunity in opportunities:
        account = accounts[
            db.get(AccountModel, opportunity.account_id).company_name
        ]

        contact = contacts[account.company_name][0]

        meeting_subject = (
            f"Discovery meeting: {opportunity.opportunity_name}"
        )

        get_or_create(
            db,
            SalesActivityModel,
            {
                "account_id": account.account_id,
                "subject": meeting_subject,
            },
            {
                "opportunity_id": opportunity.opportunity_id,
                "contact_id": contact.contact_id,
                "owner_id": opportunity.owner_id,
                "activity_type": "meeting",
                "notes": "Discussed business requirements and next steps.",
                "activity_status": "completed",
                "due_at": now - timedelta(days=7),
                "completed_at": now - timedelta(days=7),
            },
        )


def seed_targets(db, sales_people):
    period_start = date.today().replace(month=1, day=1)
    period_end = date.today().replace(month=12, day=31)

    target_amounts = {
        "demo_rep_01": "12000000.00",
        "demo_rep_02": "10000000.00",
        "demo_rep_03": "11000000.00",
    }

    for username, rep in sales_people.items():
        get_or_create(
            db,
            SalesTargetModel,
            {
                "user_id": rep.user_id,
                "period_start": period_start,
            },
            {
                "period_end": period_end,
                "target_amount": Decimal(target_amounts[username]),
                "currency_code": "INR",
            },
        )


def run_seed():
    db = SessionLocal()

    try:
        manager, sales_people = seed_users(db)
        db.flush()

        accounts = seed_accounts(db, sales_people)
        contacts = seed_contacts(db, accounts)
        products = seed_products(db)

        db.flush()

        opportunities = seed_opportunities(
            db,
            accounts,
            contacts,
            sales_people,
            products,
            manager,
        )

        db.flush()

        seed_activities(db, opportunities, contacts, accounts)
        seed_targets(db, sales_people)

        db.commit()

        print("NexusFlow RevOps seed completed successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
