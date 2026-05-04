from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.rapidapi_client import RapidApiError, get_rapidapi_client
from app.services.rapidapi_service import RapidApiService
from app.services.trip_service import sample_attractions, sample_flights, sample_hotels

router = APIRouter(prefix="", tags=["rapidapi"])


def get_optional_rapidapi_service() -> RapidApiService | None:
    try:
        return RapidApiService(get_rapidapi_client())
    except RapidApiError:
        return None


def _demo_location_from_destination_id(dest_id: str) -> str:
    london_ids = {"-553173", "20088325", "london", "lon", "lhr"}
    return "London" if str(dest_id).strip().lower() in london_ids else str(dest_id)


@router.get("/attractions/search", summary="Search attractions")
async def search_attractions(
    start_date: str = Query(..., description="Format: YYYY-MM-DD"),
    end_date: str = Query(..., description="Format: YYYY-MM-DD"),
    dest_id: str = Query(..., description="Destination ID, e.g. 20088325"),
    locale: str = Query("en-gb"),
    page_number: int = Query(0, ge=0),
    currency: str = Query("USD"),
    order_by: str = Query("attr_book_score"),
    tenant_id: str = Query("tenant_a"),
    allow_sample_data: bool = Query(True),
    service: RapidApiService | None = Depends(get_optional_rapidapi_service),
):
    if service is not None:
        try:
            return service.search_attractions(
                start_date=start_date,
                end_date=end_date,
                dest_id=dest_id,
                locale=locale,
                page_number=page_number,
                currency=currency,
                order_by=order_by,
            )
        except RapidApiError as error:
            if not allow_sample_data:
                raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    if not allow_sample_data:
        raise HTTPException(status_code=500, detail="RAPIDAPI_KEY is not configured.")

    return {
        "source": "sample_data",
        "message": "RapidAPI is unavailable or not configured; returning tenant-scoped demo attractions.",
        "products": sample_attractions(tenant_id, _demo_location_from_destination_id(dest_id)),
    }


@router.get("/hotels/search", summary="Search hotels")
async def search_hotels(
    page_number: int = Query(0, ge=0),
    dest_type: str = Query("city"),
    dest_id: str = Query(..., description="Example: -553173"),
    units: str = Query("metric"),
    children_number: int = Query(0, ge=0),
    locale: str = Query("en-gb"),
    categories_filter_ids: str | None = Query(None),
    children_ages: str | None = Query(None, description="Comma-separated ages, e.g. 5,0"),
    include_adjacency: bool = Query(True),
    filter_by_currency: str = Query("USD"),
    order_by: str = Query("popularity"),
    checkin_date: str = Query(..., description="Format: YYYY-MM-DD"),
    checkout_date: str = Query(..., description="Format: YYYY-MM-DD"),
    room_number: int = Query(1, ge=1),
    adults_number: int = Query(1, ge=1),
    tenant_id: str = Query("tenant_a"),
    allow_sample_data: bool = Query(True),
    service: RapidApiService | None = Depends(get_optional_rapidapi_service),
):
    if service is not None:
        try:
            return service.search_hotels(
                page_number=page_number,
                dest_type=dest_type,
                dest_id=dest_id,
                units=units,
                children_number=children_number,
                locale=locale,
                categories_filter_ids=categories_filter_ids,
                children_ages=children_ages,
                include_adjacency=include_adjacency,
                filter_by_currency=filter_by_currency,
                order_by=order_by,
                checkin_date=checkin_date,
                checkout_date=checkout_date,
                room_number=room_number,
                adults_number=adults_number,
            )
        except RapidApiError as error:
            if not allow_sample_data:
                raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    if not allow_sample_data:
        raise HTTPException(status_code=500, detail="RAPIDAPI_KEY is not configured.")

    return {
        "source": "sample_data",
        "message": "RapidAPI is unavailable or not configured; returning tenant-scoped demo hotels.",
        "hotels": sample_hotels(tenant_id, _demo_location_from_destination_id(dest_id)),
    }


@router.get("/flights/search", summary="Search flights")
async def search_flights(
    depart_date: str = Query(..., description="Format: YYYY-MM-DD"),
    from_code: str = Query(..., description="Example: SFO or SFO.AIRPORT"),
    to_code: str = Query(..., description="Example: LON, LHR, or LON.CITY"),
    adults: int = Query(1, ge=1),
    locale: str = Query("en-gb"),
    page_number: int = Query(0, ge=0),
    currency: str = Query("USD"),
    order_by: str = Query("BEST"),
    flight_type: str = Query("ONEWAY"),
    cabin_class: str = Query("ECONOMY"),
    children_ages: str | None = Query(None, description="Comma-separated ages, e.g. 5,0"),
    return_date: str | None = Query(None, description="Format: YYYY-MM-DD"),
    tenant_id: str = Query("tenant_a"),
    allow_sample_data: bool = Query(True),
    service: RapidApiService | None = Depends(get_optional_rapidapi_service),
):
    if service is not None:
        try:
            return service.search_flights(
                depart_date=depart_date,
                from_code=from_code,
                to_code=to_code,
                adults=adults,
                locale=locale,
                page_number=page_number,
                currency=currency,
                order_by=order_by,
                flight_type=flight_type,
                cabin_class=cabin_class,
                children_ages=children_ages,
                return_date=return_date,
            )
        except RapidApiError as error:
            if not allow_sample_data:
                raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    if not allow_sample_data:
        raise HTTPException(status_code=500, detail="RAPIDAPI_KEY is not configured.")

    return {
        "source": "sample_data",
        "message": "RapidAPI is unavailable or not configured; returning tenant-scoped demo flights.",
        "flights": sample_flights(tenant_id, from_code, to_code, depart_date),
    }
