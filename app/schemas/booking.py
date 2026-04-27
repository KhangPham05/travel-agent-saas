# ==========================================
# PYDANTIC SCHEMAS (Data Validation)
# ==========================================

from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class HotelReservationCreate(BaseModel):
    Hotel_Code: int
    Check_In_Date: date
    Check_In_Time: Optional[str] = None
    Check_Out_Date: date
    Check_Out_Time: Optional[str] = None
    Rate: Optional[float] = None


class FlightReservationCreate(BaseModel):
    Airline_Code: str
    Flight_Number: str
    Departure_Date: date
    Departure_Time: str
    Arrive_Date: date
    Arrive_Time: str
    Rate: Optional[float] = None
    Origin_Airport_Code: str
    Destination_Airport_Code: str


class HotelReservationUpdate(BaseModel):
    Hotel_Code: Optional[int] = None
    Check_In_Date: Optional[date] = None
    Check_In_Time: Optional[str] = None
    Check_Out_Date: Optional[date] = None
    Check_Out_Time: Optional[str] = None
    Rate: Optional[float] = None


class FlightReservationUpdate(BaseModel):
    Airline_Code: Optional[str] = None
    Flight_Number: Optional[str] = None
    Departure_Date: Optional[date] = None
    Departure_Time: Optional[str] = None
    Arrive_Date: Optional[date] = None
    Arrive_Time: Optional[str] = None
    Rate: Optional[float] = None
    Origin_Airport_Code: Optional[str] = None
    Destination_Airport_Code: Optional[str] = None


class HotelReservationResponse(HotelReservationCreate):
    Reservation_No: int

    class Config:
        from_attributes = True


class FlightReservationResponse(FlightReservationCreate):
    Reservation_No: int

    class Config:
        from_attributes = True


# Base schema (fields shared by Create and Response)
class BookingBase(BaseModel):
    User_Id: int
    Agent_Id: Optional[int] = None
    Start_Date: date
    End_Date: date

# Schema used when CREATING a new Booking (Request Body)
class BookingCreate(BookingBase):
    hotel_reservations: list[HotelReservationCreate] = Field(default_factory=list)
    flight_reservations: list[FlightReservationCreate] = Field(default_factory=list)

# Schema used when UPDATING an existing Booking (Request Body)
class BookingUpdate(BaseModel):
    Start_Date: Optional[date] = None
    End_Date: Optional[date] = None
    Agent_Id: Optional[int] = None

# Schema used when RETURNING a Booking (Response Body)
class BookingResponse(BookingBase):
    Booking_Id: int

    class Config:
        from_attributes = True

# Helper schema to show User details alongside Bookings
class UserResponse(BaseModel):
    First_Name: str
    Last_Name: str
    Email: EmailStr

    class Config:
        from_attributes = True

# Advanced Response schema including User information and computed total cost
class BookingDetailResponse(BookingResponse):
    user: UserResponse
    hotel_reservations: list[HotelReservationResponse] = Field(default_factory=list)
    flight_reservations: list[FlightReservationResponse] = Field(default_factory=list)
    total_cost: Optional[float] = Field(
        default=None,
        description="Total trip cost = sum of all flight rates + (hotel rate × nights) + activities"
    )

    @classmethod
    def from_orm_with_total(cls, booking):
        """
        Build the response and compute total_cost automatically.
        Formula: Total = Flight rates + (Hotel rate × nights) + Activity prices
        """
        obj = cls.model_validate(booking)

        total = 0.0

        # Sum all flight rates
        for flight in obj.flight_reservations:
            if flight.Rate is not None:
                total += flight.Rate

        # Sum hotel rates × number of nights
        for hotel in obj.hotel_reservations:
            if hotel.Rate is not None:
                nights = (hotel.Check_Out_Date - hotel.Check_In_Date).days
                total += hotel.Rate * max(nights, 1)

        obj.total_cost = round(total, 2)
        return obj