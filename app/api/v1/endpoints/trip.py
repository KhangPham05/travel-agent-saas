from fastapi import APIRouter, Header, Query

from app.schemas.trip import TripSearchResponse
from app.services.trip_service import search_budget_trips, tenant_ids

router = APIRouter(prefix="", tags=["trip-planner"])


@router.get("/trip-tenants", summary="List demo travel-agency tenants")
def list_tenants():
    """Return available tenants so the UI can demonstrate agency-level pricing isolation."""
    return {
        "tenants": [
            {"tenant_id": tenant_id, "label": tenant_id.replace("_", " ").title()}
            for tenant_id in tenant_ids()
        ]
    }


@router.get(
    "/trips/search",
    response_model=TripSearchResponse,
    summary="Search budget trip combinations",
)
def search_trips(
    from_code: str = Query("SFO", description="Origin airport/city code, e.g. SFO"),
    to_code: str = Query("LON", description="Destination airport/city code, e.g. LON"),
    depart_date: str = Query("2026-05-01", description="Format: YYYY-MM-DD"),
    check_in: str = Query("2026-05-01", description="Format: YYYY-MM-DD"),
    check_out: str = Query("2026-05-06", description="Format: YYYY-MM-DD"),
    budget: float = Query(1500, ge=0, description="Maximum total trip budget"),
    location: str | None = Query(None, description="Destination name, defaults to to_code"),
    tenant_id: str = Query("tenant_a", description="Travel agency tenant ID"),
    limit: int = Query(30, ge=1, le=100),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
):
    """
    Combine flights, hostels, and activities into complete backpacker trip plans.

    This endpoint implements the Phase 1 acceptance criteria:
    budget input, total-cost calculation, budget filtering, cheapest-first sorting,
    tie-breaking by shortest flight duration, and SaaS tenant pricing isolation.
    """
    requested_tenant = x_tenant_id or tenant_id
    return search_budget_trips(
        tenant_id=requested_tenant,
        from_code=from_code,
        to_code=to_code,
        depart_date=depart_date,
        check_in=check_in,
        check_out=check_out,
        budget=budget,
        location=location,
        limit=limit,
    )
