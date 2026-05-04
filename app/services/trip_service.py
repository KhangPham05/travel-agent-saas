from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from itertools import product
from typing import Any


DEFAULT_CURRENCY = "USD"

# Deterministic tenant-scoped demo inventory.  The same flights/hotels can have
# different prices for different agencies, which demonstrates the Phase 1 SaaS
# multi-tenancy requirement even when RapidAPI credentials are not available.
TENANT_INVENTORY: dict[str, dict[str, Any]] = {
    "tenant_a": {
        "name": "Tenant A - Campus Budget Travel",
        "flights": [
            {
                "id": "ta-flight-001",
                "airline": "BudgetAir Student",
                "airline_code": "BA",
                "flight_number": "BA131",
                "from_code": "SFO",
                "to_code": "LON",
                "from_airport_code": "SFO",
                "to_airport_code": "LHR",
                "departure_time": "08:00",
                "arrival_time": "18:45",
                "duration_minutes": 645,
                "stops": 0,
                "price": 520.00,
            },
            {
                "id": "ta-flight-002",
                "airline": "StudentJet",
                "airline_code": "SJ",
                "flight_number": "SJ204",
                "from_code": "SFO",
                "to_code": "LON",
                "from_airport_code": "SFO",
                "to_airport_code": "LGW",
                "departure_time": "13:25",
                "arrival_time": "07:10",
                "duration_minutes": 705,
                "stops": 1,
                "price": 610.00,
            },
            {
                "id": "ta-flight-003",
                "airline": "Atlantic Saver",
                "airline_code": "AS",
                "flight_number": "AS515",
                "from_code": "SFO",
                "to_code": "LON",
                "from_airport_code": "SFO",
                "to_airport_code": "LHR",
                "departure_time": "20:20",
                "arrival_time": "15:00",
                "duration_minutes": 760,
                "stops": 1,
                "price": 455.00,
            },
            {
                "id": "ta-flight-004",
                "airline": "BudgetAir Student",
                "airline_code": "BA",
                "flight_number": "BA190",
                "from_code": "NYC",
                "to_code": "LON",
                "from_airport_code": "JFK",
                "to_airport_code": "LHR",
                "departure_time": "18:30",
                "arrival_time": "06:30",
                "duration_minutes": 420,
                "stops": 0,
                "price": 390.00,
            },
        ],
        "hotels": [
            {
                "id": "ta-hotel-101",
                "hotel_code": 101,
                "name": "Camden Backpacker Hostel",
                "city": "London",
                "address": "12 Camden High Street",
                "room_type": "Shared dorm bed",
                "rating": 4.1,
                "price_per_night": 42.00,
            },
            {
                "id": "ta-hotel-102",
                "hotel_code": 102,
                "name": "Southbank Student Pods",
                "city": "London",
                "address": "20 Belvedere Road",
                "room_type": "Budget pod",
                "rating": 4.3,
                "price_per_night": 58.00,
            },
            {
                "id": "ta-hotel-103",
                "hotel_code": 103,
                "name": "Zone 2 Value Hostel",
                "city": "London",
                "address": "88 Hackney Road",
                "room_type": "Private micro room",
                "rating": 3.9,
                "price_per_night": 72.00,
            },
        ],
        "attractions": [
            {
                "id": "ta-activity-201",
                "name": "Free Westminster Walking Tour",
                "description": "Student-friendly walking tour covering Big Ben, Westminster, and river views.",
                "location": "Westminster, London",
                "category": "Free tour",
                "rating": 4.6,
                "price": 0.00,
            },
            {
                "id": "ta-activity-202",
                "name": "British Museum Highlights",
                "description": "Low-cost self-guided museum visit with suggested backpacker route.",
                "location": "Bloomsbury, London",
                "category": "Museum",
                "rating": 4.7,
                "price": 0.00,
            },
            {
                "id": "ta-activity-203",
                "name": "Thames Clipper Student Fare",
                "description": "Budget river ride for skyline views without a premium cruise price.",
                "location": "Central London",
                "category": "Sightseeing",
                "rating": 4.4,
                "price": 16.00,
            },
            {
                "id": "ta-activity-204",
                "name": "Tower Bridge Exhibition",
                "description": "Discounted entry for bridge walkways and engine rooms.",
                "location": "Tower Bridge, London",
                "category": "Landmark",
                "rating": 4.5,
                "price": 15.00,
            },
        ],
    },
    "tenant_b": {
        "name": "Tenant B - City Explorer Agency",
        "flights": [
            {
                "id": "tb-flight-001",
                "airline": "BudgetAir Student",
                "airline_code": "BA",
                "flight_number": "BA131",
                "from_code": "SFO",
                "to_code": "LON",
                "from_airport_code": "SFO",
                "to_airport_code": "LHR",
                "departure_time": "08:00",
                "arrival_time": "18:45",
                "duration_minutes": 645,
                "stops": 0,
                "price": 575.00,
            },
            {
                "id": "tb-flight-002",
                "airline": "StudentJet",
                "airline_code": "SJ",
                "flight_number": "SJ204",
                "from_code": "SFO",
                "to_code": "LON",
                "from_airport_code": "SFO",
                "to_airport_code": "LGW",
                "departure_time": "13:25",
                "arrival_time": "07:10",
                "duration_minutes": 705,
                "stops": 1,
                "price": 635.00,
            },
            {
                "id": "tb-flight-003",
                "airline": "Atlantic Saver",
                "airline_code": "AS",
                "flight_number": "AS515",
                "from_code": "SFO",
                "to_code": "LON",
                "from_airport_code": "SFO",
                "to_airport_code": "LHR",
                "departure_time": "20:20",
                "arrival_time": "15:00",
                "duration_minutes": 760,
                "stops": 1,
                "price": 500.00,
            },
            {
                "id": "tb-flight-004",
                "airline": "BudgetAir Student",
                "airline_code": "BA",
                "flight_number": "BA190",
                "from_code": "NYC",
                "to_code": "LON",
                "from_airport_code": "JFK",
                "to_airport_code": "LHR",
                "departure_time": "18:30",
                "arrival_time": "06:30",
                "duration_minutes": 420,
                "stops": 0,
                "price": 430.00,
            },
        ],
        "hotels": [
            {
                "id": "tb-hotel-101",
                "hotel_code": 201,
                "name": "Camden Backpacker Hostel",
                "city": "London",
                "address": "12 Camden High Street",
                "room_type": "Shared dorm bed",
                "rating": 4.1,
                "price_per_night": 49.00,
            },
            {
                "id": "tb-hotel-102",
                "hotel_code": 202,
                "name": "Southbank Student Pods",
                "city": "London",
                "address": "20 Belvedere Road",
                "room_type": "Budget pod",
                "rating": 4.3,
                "price_per_night": 64.00,
            },
            {
                "id": "tb-hotel-103",
                "hotel_code": 203,
                "name": "Zone 2 Value Hostel",
                "city": "London",
                "address": "88 Hackney Road",
                "room_type": "Private micro room",
                "rating": 3.9,
                "price_per_night": 82.00,
            },
        ],
        "attractions": [
            {
                "id": "tb-activity-201",
                "name": "Free Westminster Walking Tour",
                "description": "Student-friendly walking tour covering Big Ben, Westminster, and river views.",
                "location": "Westminster, London",
                "category": "Free tour",
                "rating": 4.6,
                "price": 0.00,
            },
            {
                "id": "tb-activity-202",
                "name": "British Museum Highlights",
                "description": "Low-cost self-guided museum visit with suggested backpacker route.",
                "location": "Bloomsbury, London",
                "category": "Museum",
                "rating": 4.7,
                "price": 0.00,
            },
            {
                "id": "tb-activity-203",
                "name": "Thames Clipper Student Fare",
                "description": "Budget river ride for skyline views without a premium cruise price.",
                "location": "Central London",
                "category": "Sightseeing",
                "rating": 4.4,
                "price": 19.00,
            },
            {
                "id": "tb-activity-204",
                "name": "Tower Bridge Exhibition",
                "description": "Discounted entry for bridge walkways and engine rooms.",
                "location": "Tower Bridge, London",
                "category": "Landmark",
                "rating": 4.5,
                "price": 18.00,
            },
        ],
    },
}

CITY_ALIASES = {
    "LON": "LONDON",
    "LHR": "LONDON",
    "LGW": "LONDON",
    "LONDON": "LONDON",
    "NYC": "NEW YORK",
    "JFK": "NEW YORK",
    "SFO": "SAN FRANCISCO",
    "SAN FRANCISCO": "SAN FRANCISCO",
}


def canonical_code(value: str | None) -> str:
    if not value:
        return ""
    cleaned = value.strip().upper().replace(".AIRPORT", "").replace(".CITY", "")
    return cleaned.split("-")[0].strip()


def canonical_city(value: str | None) -> str:
    code = canonical_code(value)
    return CITY_ALIASES.get(code, code)


def parse_nights(check_in: str, check_out: str) -> int:
    try:
        start = datetime.strptime(check_in, "%Y-%m-%d").date()
        end = datetime.strptime(check_out, "%Y-%m-%d").date()
        return max((end - start).days, 1)
    except ValueError:
        # FastAPI query validation is intentionally permissive here so the UI can
        # show a usable error-free demo. Fall back to the Phase 1 test-case style
        # five-night trip if a date is malformed.
        return 5


def duration_label(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins:02d}m"


def tenant_ids() -> list[str]:
    return list(TENANT_INVENTORY.keys())


def tenant_name(tenant_id: str) -> str:
    tenant = TENANT_INVENTORY.get(tenant_id, TENANT_INVENTORY["tenant_a"])
    return tenant["name"]


def _with_common_fields(item: dict[str, Any], tenant_id: str, depart_date: str | None = None) -> dict[str, Any]:
    enriched = deepcopy(item)
    enriched["tenant_id"] = tenant_id
    enriched["currency"] = DEFAULT_CURRENCY
    if "duration_minutes" in enriched:
        enriched["duration"] = duration_label(int(enriched["duration_minutes"]))
    if depart_date is not None:
        enriched["depart_date"] = depart_date
    return enriched


def sample_flights(tenant_id: str, from_code: str, to_code: str, depart_date: str) -> list[dict[str, Any]]:
    tenant_key = tenant_id if tenant_id in TENANT_INVENTORY else "tenant_a"
    origin = canonical_city(from_code)
    destination = canonical_city(to_code)
    flights: list[dict[str, Any]] = []
    for flight in TENANT_INVENTORY[tenant_key]["flights"]:
        if canonical_city(flight["from_code"]) == origin and canonical_city(flight["to_code"]) == destination:
            flights.append(_with_common_fields(flight, tenant_key, depart_date))
    return flights


def sample_hotels(tenant_id: str, location: str) -> list[dict[str, Any]]:
    tenant_key = tenant_id if tenant_id in TENANT_INVENTORY else "tenant_a"
    destination = canonical_city(location)
    hotels: list[dict[str, Any]] = []
    for hotel in TENANT_INVENTORY[tenant_key]["hotels"]:
        if canonical_city(hotel["city"]) == destination:
            hotels.append(_with_common_fields(hotel, tenant_key))
    return hotels


def sample_attractions(tenant_id: str, location: str) -> list[dict[str, Any]]:
    tenant_key = tenant_id if tenant_id in TENANT_INVENTORY else "tenant_a"
    destination = canonical_city(location)
    attractions: list[dict[str, Any]] = []
    for attraction in TENANT_INVENTORY[tenant_key]["attractions"]:
        if destination in canonical_city(attraction["location"]):
            attractions.append(_with_common_fields(attraction, tenant_key))
    if not attractions and destination == "LONDON":
        return [_with_common_fields(item, tenant_key) for item in TENANT_INVENTORY[tenant_key]["attractions"]]
    return attractions


def build_trip_option(
    tenant_id: str,
    flight: dict[str, Any],
    hotel: dict[str, Any],
    attractions: list[dict[str, Any]],
    nights: int,
    budget: float,
) -> dict[str, Any]:
    flight_cost = round(float(flight["price"]), 2)
    accommodation_cost = round(float(hotel["price_per_night"]) * nights, 2)
    activities_cost = round(sum(float(activity.get("price", 0) or 0) for activity in attractions), 2)
    total_cost = round(flight_cost + accommodation_cost + activities_cost, 2)
    return {
        "id": f"{flight['id']}__{hotel['id']}__{'-'.join(a['id'] for a in attractions) or 'no-activity'}",
        "tenant_id": tenant_id,
        "flight": flight,
        "hotel": hotel,
        "attractions": attractions,
        "nights": nights,
        "flight_cost": flight_cost,
        "accommodation_cost": accommodation_cost,
        "activities_cost": activities_cost,
        "total_cost": total_cost,
        "budget_remaining": round(budget - total_cost, 2),
        "within_budget": total_cost <= budget,
        "formula": f"{flight_cost:.2f} + ({float(hotel['price_per_night']):.2f} x {nights} nights) + {activities_cost:.2f}",
    }


def search_budget_trips(
    *,
    tenant_id: str,
    from_code: str,
    to_code: str,
    depart_date: str,
    check_in: str,
    check_out: str,
    budget: float,
    location: str | None = None,
    limit: int = 30,
) -> dict[str, Any]:
    tenant_key = tenant_id if tenant_id in TENANT_INVENTORY else "tenant_a"
    destination = location or to_code
    nights = parse_nights(check_in, check_out)
    safe_budget = max(float(budget), 0.0)

    flights = sample_flights(tenant_key, from_code, to_code, depart_date)
    hotels = sample_hotels(tenant_key, destination)
    attractions = sample_attractions(tenant_key, destination)

    results: list[dict[str, Any]] = []
    if safe_budget > 0:
        for flight, hotel, attraction in product(flights, hotels, attractions or [[]]):
            selected_activities = [] if attraction == [] else [attraction]
            option = build_trip_option(
                tenant_id=tenant_key,
                flight=flight,
                hotel=hotel,
                attractions=selected_activities,
                nights=nights,
                budget=safe_budget,
            )
            if option["within_budget"]:
                results.append(option)

    # Phase 1: cheapest total first. Tie-breaker: shortest flight duration.
    results.sort(key=lambda item: (item["total_cost"], item["flight"]["duration_minutes"]))
    results = results[: max(limit, 1)]

    if safe_budget <= 0:
        message = "No results available. Enter a budget above $0."
    elif not flights:
        message = "No results available for this origin/destination. Try SFO to LON for the demo dataset."
    elif not hotels:
        message = "No results available because no hostel data matches this destination."
    elif not attractions:
        message = "No results available because no activities match this destination."
    elif not results:
        message = "No results available within this budget. Increase the budget or choose cheaper trip components."
    else:
        message = f"{len(results)} budget-friendly trip combinations found. Cheapest total cost is ${results[0]['total_cost']:.2f}."

    return {
        "tenant_id": tenant_key,
        "tenant_name": tenant_name(tenant_key),
        "budget": safe_budget,
        "currency": DEFAULT_CURRENCY,
        "nights": nights,
        "count": len(results),
        "message": message,
        "flights": flights,
        "hotels": hotels,
        "attractions": attractions,
        "results": results,
    }
