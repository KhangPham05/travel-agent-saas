from pydantic import BaseModel, Field


class FlightOption(BaseModel):
    id: str
    tenant_id: str
    airline: str
    airline_code: str
    flight_number: str
    from_code: str
    to_code: str
    from_airport_code: str
    to_airport_code: str
    depart_date: str
    departure_time: str
    arrival_time: str
    duration_minutes: int
    duration: str
    stops: int
    price: float
    currency: str = "USD"


class HotelOption(BaseModel):
    id: str
    tenant_id: str
    hotel_code: int
    name: str
    city: str
    address: str | None = None
    room_type: str | None = None
    rating: float | None = None
    price_per_night: float
    currency: str = "USD"


class AttractionOption(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str
    location: str
    category: str | None = None
    rating: float | None = None
    price: float = 0
    currency: str = "USD"


class TripOption(BaseModel):
    id: str
    tenant_id: str
    flight: FlightOption
    hotel: HotelOption
    attractions: list[AttractionOption] = Field(default_factory=list)
    nights: int
    flight_cost: float
    accommodation_cost: float
    activities_cost: float
    total_cost: float
    budget_remaining: float
    within_budget: bool
    formula: str


class TripSearchResponse(BaseModel):
    tenant_id: str
    tenant_name: str
    budget: float
    currency: str
    nights: int
    count: int
    message: str
    flights: list[FlightOption] = Field(default_factory=list)
    hotels: list[HotelOption] = Field(default_factory=list)
    attractions: list[AttractionOption] = Field(default_factory=list)
    results: list[TripOption] = Field(default_factory=list)
