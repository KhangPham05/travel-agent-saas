from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.booking import (
    ActivityReservation,
    Booking,
    FlightReservation,
    HotelReservation,
    Tenant,
    User,
)
from app.schemas.booking import (
    ActivityReservationUpdate,
    BookingCreate,
    BookingDetailResponse,
    BookingResponse,
    BookingUpdate,
    FlightReservationUpdate,
    HotelReservationUpdate,
    TenantResponse,
)
from app.services.trip_service import tenant_ids, tenant_name

router = APIRouter(prefix="", tags=["booking"])


def _ensure_tenant(db: Session, tenant_id: str | None) -> Tenant:
    tenant_id = tenant_id or "tenant_a"
    db_tenant = db.query(Tenant).filter(Tenant.Tenant_Id == tenant_id).first()
    if db_tenant:
        return db_tenant

    if tenant_id not in tenant_ids():
        raise HTTPException(status_code=400, detail=f"Unknown Tenant_Id '{tenant_id}'.")

    db_tenant = Tenant(
        Tenant_Id=tenant_id,
        Name=tenant_name(tenant_id),
        Description="Demo tenant for Phase 1 SaaS pricing isolation.",
    )
    db.add(db_tenant)
    db.flush()
    return db_tenant


def _ensure_demo_user(db: Session, tenant_id: str) -> User:
    _ensure_tenant(db, tenant_id)
    email = f"demo.{tenant_id}@thriftybackpacker.example"
    user = db.query(User).filter(User.Email == email).first()
    if user:
        return user

    user = User(
        Tenant_Id=tenant_id,
        First_Name="Max",
        Last_Name="Johnson",
        Email=email,
        Phone_Number="555-0100",
    )
    db.add(user)
    db.flush()
    return user


@router.get("/tenants", response_model=list[TenantResponse], summary="List configured tenants")
def read_tenants(db: Session = Depends(get_db)):
    """Return the tenant catalog used for SaaS pricing isolation."""
    for tenant_id in tenant_ids():
        if not db.query(Tenant).filter(Tenant.Tenant_Id == tenant_id).first():
            db.add(
                Tenant(
                    Tenant_Id=tenant_id,
                    Name=tenant_name(tenant_id),
                    Description="Demo tenant for Phase 1 SaaS pricing isolation.",
                )
            )
    db.commit()
    return db.query(Tenant).order_by(Tenant.Tenant_Id).all()


@router.get("/setup-seed-data/", include_in_schema=False)
def seed_data(tenant_id: str = "tenant_a", db: Session = Depends(get_db)):
    """Helper endpoint used by the frontend demo to seed a tenant and user."""
    try:
        user = _ensure_demo_user(db, tenant_id)
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Unable to seed demo user.") from exc

    return {
        "message": "Demo tenant and user are ready.",
        "tenant_id": tenant_id,
        "user_id": user.User_ID,
        "email": user.Email,
    }


@router.get("/bookings/", response_model=List[BookingResponse], summary="List bookings")
def read_bookings(
    skip: int = 0,
    limit: int = 100,
    tenant_id: str | None = Query(None, description="Optional tenant filter for data isolation."),
    db: Session = Depends(get_db),
):
    """Retrieve bookings. Passing tenant_id returns only that tenant's bookings."""
    query = db.query(Booking)
    if tenant_id:
        query = query.filter(Booking.Tenant_Id == tenant_id)
    return query.order_by(Booking.Booking_Id.desc()).offset(skip).limit(limit).all()


@router.get("/bookings/{booking_id}", response_model=BookingDetailResponse, summary="Get booking details")
def read_booking(
    booking_id: int,
    tenant_id: str | None = Query(None, description="Optional tenant guard for data isolation."),
    db: Session = Depends(get_db),
):
    """
    Retrieve detailed booking information with total trip cost.

    Total = sum(flight rates) + sum(hotel rate × nights) + sum(activity prices)
    """
    query = db.query(Booking).filter(Booking.Booking_Id == booking_id)
    if tenant_id:
        query = query.filter(Booking.Tenant_Id == tenant_id)
    db_booking = query.first()
    if db_booking is None:
        raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found")
    return BookingDetailResponse.from_orm_with_total(db_booking)


@router.post(
    "/bookings/",
    response_model=BookingDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking",
)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    """
    Persist the selected trip from the UI.

    The request stores flight, hotel, and activity selections in the database and
    returns a detailed booking response with the computed total cost.
    """
    _ensure_tenant(db, booking.Tenant_Id)

    user_exists = db.query(User).filter(User.User_ID == booking.User_Id).first()
    if not user_exists:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot create booking. User_Id {booking.User_Id} does not exist.",
        )

    booking_data = booking.model_dump(
        exclude={"hotel_reservations", "flight_reservations", "activity_reservations"}
    )
    db_booking = Booking(**booking_data)
    db.add(db_booking)
    db.flush()

    for hotel in booking.hotel_reservations:
        db.add(HotelReservation(Booking_Id=db_booking.Booking_Id, **hotel.model_dump()))

    for flight in booking.flight_reservations:
        db.add(FlightReservation(Booking_Id=db_booking.Booking_Id, **flight.model_dump()))

    for activity in booking.activity_reservations:
        db.add(ActivityReservation(Booking_Id=db_booking.Booking_Id, **activity.model_dump()))

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Database error: check User_Id, Tenant_Id, and date formats.",
        ) from exc

    db.refresh(db_booking)
    return BookingDetailResponse.from_orm_with_total(db_booking)


@router.patch("/bookings/{booking_id}", response_model=BookingResponse, summary="Update a booking")
def update_booking(booking_id: int, booking_update: BookingUpdate, db: Session = Depends(get_db)):
    db_booking = db.query(Booking).filter(Booking.Booking_Id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found")

    update_data = booking_update.model_dump(exclude_unset=True)
    if "Tenant_Id" in update_data:
        _ensure_tenant(db, update_data["Tenant_Id"])
    for key, value in update_data.items():
        setattr(db_booking, key, value)

    db.commit()
    db.refresh(db_booking)
    return db_booking


@router.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a booking")
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    db_booking = db.query(Booking).filter(Booking.Booking_Id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found")

    db.delete(db_booking)
    db.commit()
    return None


@router.patch(
    "/bookings/{booking_id}/hotel-reservations/{reservation_no}",
    summary="Update a hotel reservation",
)
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

    for key, value in reservation_update.model_dump(exclude_unset=True).items():
        setattr(db_reservation, key, value)

    db.commit()
    db.refresh(db_reservation)
    return db_reservation


@router.patch(
    "/bookings/{booking_id}/flight-reservations/{reservation_no}",
    summary="Update a flight reservation",
)
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

    for key, value in reservation_update.model_dump(exclude_unset=True).items():
        setattr(db_reservation, key, value)

    db.commit()
    db.refresh(db_reservation)
    return db_reservation


@router.patch(
    "/bookings/{booking_id}/activity-reservations/{activity_reservation_id}",
    summary="Update an activity reservation",
)
def update_activity_reservation(
    booking_id: int,
    activity_reservation_id: int,
    reservation_update: ActivityReservationUpdate = Body(...),
    db: Session = Depends(get_db),
):
    db_reservation = (
        db.query(ActivityReservation)
        .filter(
            ActivityReservation.Activity_Reservation_Id == activity_reservation_id,
            ActivityReservation.Booking_Id == booking_id,
        )
        .first()
    )
    if db_reservation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Activity reservation {activity_reservation_id} not found for booking {booking_id}",
        )

    for key, value in reservation_update.model_dump(exclude_unset=True).items():
        setattr(db_reservation, key, value)

    db.commit()
    db.refresh(db_reservation)
    return db_reservation
