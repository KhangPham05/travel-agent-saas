from typing import List
from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.core.database import get_db
from app.models.booking import Booking, User, HotelReservation, FlightReservation
from app.schemas.booking import (
    BookingResponse,
    BookingDetailResponse,
    BookingCreate,
    BookingUpdate,
    HotelReservationResponse,
    FlightReservationResponse,
    HotelReservationUpdate,
    FlightReservationUpdate,
)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


router = APIRouter(prefix="", tags=["booking"])


# ==========================================
# ENDPOINTS (CRUD)
# ==========================================

# 1. READ: Get all Bookings (with pagination)
@router.get("/bookings/", response_model=List[BookingResponse], summary="List all bookings")
def read_bookings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of bookings. Use 'skip' and 'limit' for pagination.
    """
    bookings = db.query(Booking).offset(skip).limit(limit).all()
    return bookings


# 2. READ: Get a specific Booking by ID (with full details + total cost)
@router.get("/bookings/{booking_id}", response_model=BookingDetailResponse, summary="Get booking details")
def read_booking(booking_id: int, db: Session = Depends(get_db)):
    """
    Retrieve detailed information about a specific booking,
    including user details and computed total trip cost.

    **Total Cost Formula:**
    `Total = sum(flight rates) + sum(hotel rate × nights) + sum(activity prices)`
    """
    db_booking = db.query(Booking).filter(Booking.Booking_Id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found")
    return BookingDetailResponse.from_orm_with_total(db_booking)


# 3. Helper: Seed a test user
@router.get("/setup-seed-data/", include_in_schema=False)
def seed_data(db: Session = Depends(get_db)):
    """Helper endpoint to seed a test user."""
    existing_user = db.query(User).filter(User.Email == "test@example.com").first()
    if existing_user:
        return {"message": f"Seed User already exists (ID: {existing_user.User_ID})"}

    new_user = User(
        First_Name="Test",
        Last_Name="Subject",
        Email="test@example.com",
        Phone_Number="555-0100"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"Test User created successfully (ID: {new_user.User_ID}). Use this User_Id to create bookings."}


# 4. CREATE: Add a new Booking (accepts RapidAPI data directly, no master table FK checks)
@router.post("/bookings/", response_model=BookingDetailResponse, status_code=status.HTTP_201_CREATED, summary="Create a new booking")
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    """
    Create a new travel booking and persist it to the database.

    - **User_Id** must refer to an existing User.
    - **hotel_reservations** and **flight_reservations** accept data directly
      from RapidAPI search results — no master table validation required.
    - Returns the full booking with a computed **total_cost**:
      `Total = sum(flight rates) + sum(hotel rate × nights)`

    **Example RapidAPI booking flow:**
    1. Call `GET /flights/search` → copy the flight details from the result
    2. Call `GET /hotels/search` → copy the hotel details from the result
    3. POST both here to save the booking
    """
    # Verify the user exists
    user_exists = db.query(User).filter(User.User_ID == booking.User_Id).first()
    if not user_exists:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot create booking. User_Id {booking.User_Id} does not exist."
        )

    booking_data = booking.model_dump(exclude={"hotel_reservations", "flight_reservations"})
    db_booking = Booking(**booking_data)
    db.add(db_booking)
    db.flush()  # Get Booking_Id before inserting children

    # Save hotel reservations directly — no Hotel_Master FK validation
    for hotel in booking.hotel_reservations:
        db.add(
            HotelReservation(
                Booking_Id=db_booking.Booking_Id,
                **hotel.model_dump(),
            )
        )

    # Save flight reservations directly — no Airline/Airport Master FK validation
    for flight in booking.flight_reservations:
        db.add(
            FlightReservation(
                Booking_Id=db_booking.Booking_Id,
                **flight.model_dump(),
            )
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Database error: check your User_Id and date formats.") from exc

    db.refresh(db_booking)
    return BookingDetailResponse.from_orm_with_total(db_booking)


# 5. UPDATE: Modify an existing Booking
# @router.patch("/bookings/{booking_id}", response_model=BookingResponse, summary="Update an existing booking")
def update_booking(booking_id: int, booking_update: BookingUpdate, db: Session = Depends(get_db)):
    """
    Update specific fields (dates or agent) of an existing booking.
    Only fields provided in the request body will be changed.
    """
    db_booking = db.query(Booking).filter(Booking.Booking_Id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found")

    update_data = booking_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_booking, key, value)

    db.commit()
    db.refresh(db_booking)
    return db_booking


# 6. DELETE: Remove an existing Booking
# @router.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a booking")
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    """Permanently delete a booking from the system."""
    db_booking = db.query(Booking).filter(Booking.Booking_Id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found")

    db.delete(db_booking)
    db.commit()
    return None


# 7. UPDATE: Modify a hotel reservation under a booking
# @router.patch("/bookings/{booking_id}/hotel-reservations/{reservation_no}", ...)
def update_hotel_reservation(
    booking_id: int,
    reservation_no: int,
    reservation_update: HotelReservationUpdate = Body(...),
    db: Session = Depends(get_db),
):
    db_reservation = (
        db.query(HotelReservation)
        .filter(
            HotelReservation.Reservation_No == reservation_no,
            HotelReservation.Booking_Id == booking_id,
        )
        .first()
    )
    if db_reservation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Hotel reservation {reservation_no} not found for booking {booking_id}",
        )

    update_data = reservation_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_reservation, key, value)

    db.commit()
    db.refresh(db_reservation)
    return db_reservation


# 8. DELETE: Remove a hotel reservation under a booking
# @router.delete("/bookings/{booking_id}/hotel-reservations/{reservation_no}", ...)
def delete_hotel_reservation(booking_id: int, reservation_no: int, db: Session = Depends(get_db)):
    db_reservation = (
        db.query(HotelReservation)
        .filter(
            HotelReservation.Reservation_No == reservation_no,
            HotelReservation.Booking_Id == booking_id,
        )
        .first()
    )
    if db_reservation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Hotel reservation {reservation_no} not found for booking {booking_id}",
        )

    db.delete(db_reservation)
    db.commit()
    return None


# 9. UPDATE: Modify a flight reservation under a booking
# @router.patch("/bookings/{booking_id}/flight-reservations/{reservation_no}", ...)
def update_flight_reservation(
    booking_id: int,
    reservation_no: int,
    reservation_update: FlightReservationUpdate = Body(...),
    db: Session = Depends(get_db),
):
    db_reservation = (
        db.query(FlightReservation)
        .filter(
            FlightReservation.Reservation_No == reservation_no,
            FlightReservation.Booking_Id == booking_id,
        )
        .first()
    )
    if db_reservation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Flight reservation {reservation_no} not found for booking {booking_id}",
        )

    update_data = reservation_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_reservation, key, value)

    db.commit()
    db.refresh(db_reservation)
    return db_reservation


# 10. DELETE: Remove a flight reservation under a booking
# @router.delete("/bookings/{booking_id}/flight-reservations/{reservation_no}", ...)
def delete_flight_reservation(booking_id: int, reservation_no: int, db: Session = Depends(get_db)):
    db_reservation = (
        db.query(FlightReservation)
        .filter(
            FlightReservation.Reservation_No == reservation_no,
            FlightReservation.Booking_Id == booking_id,
        )
        .first()
    )
    if db_reservation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Flight reservation {reservation_no} not found for booking {booking_id}",
        )

    db.delete(db_reservation)
    db.commit()
    return None