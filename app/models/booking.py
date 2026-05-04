# ==========================================
# SQLALCHEMY MODELS (Travel booking persistence)
# ==========================================

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    Tenant_Id = Column(String, primary_key=True, index=True)
    Name = Column(String, nullable=False)
    Description = Column(String, nullable=True)

    users = relationship("User", back_populates="tenant")
    bookings = relationship("Booking", back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    User_ID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Tenant_Id = Column(String, ForeignKey("tenants.Tenant_Id"), nullable=True, index=True)
    First_Name = Column(String, nullable=False)
    Last_Name = Column(String, nullable=False)
    Email = Column(String, unique=True, nullable=False, index=True)
    Phone_Number = Column(String)

    tenant = relationship("Tenant", back_populates="users")
    bookings = relationship("Booking", back_populates="user")


class Booking(Base):
    __tablename__ = "bookings"

    Booking_Id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Tenant_Id = Column(String, ForeignKey("tenants.Tenant_Id"), nullable=True, index=True)
    User_Id = Column(Integer, ForeignKey("users.User_ID"), nullable=False)
    Agent_Id = Column(Integer, nullable=True)
    Start_Date = Column(Date, nullable=False)
    End_Date = Column(Date, nullable=False)

    tenant = relationship("Tenant", back_populates="bookings")
    user = relationship("User", back_populates="bookings")
    hotel_reservations = relationship(
        "HotelReservation", back_populates="booking", cascade="all, delete-orphan"
    )
    flight_reservations = relationship(
        "FlightReservation", back_populates="booking", cascade="all, delete-orphan"
    )
    activity_reservations = relationship(
        "ActivityReservation", back_populates="booking", cascade="all, delete-orphan"
    )


class HotelReservation(Base):
    __tablename__ = "hotel_reservations"

    Reservation_No = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Booking_Id = Column(Integer, ForeignKey("bookings.Booking_Id"), nullable=False)
    Hotel_Code = Column(Integer, nullable=False)
    Check_In_Date = Column(Date, nullable=False)
    Check_In_Time = Column(String, nullable=True)
    Check_Out_Date = Column(Date, nullable=False)
    Check_Out_Time = Column(String, nullable=True)
    Rate = Column(Float, nullable=True)

    booking = relationship("Booking", back_populates="hotel_reservations")


class FlightReservation(Base):
    __tablename__ = "flight_reservations"

    Reservation_No = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Booking_Id = Column(Integer, ForeignKey("bookings.Booking_Id"), nullable=False)
    Airline_Code = Column(String, nullable=False)
    Flight_Number = Column(String, nullable=False)
    Departure_Date = Column(Date, nullable=False)
    Departure_Time = Column(String, nullable=False)
    Arrive_Date = Column(Date, nullable=False)
    Arrive_Time = Column(String, nullable=False)
    Rate = Column(Float, nullable=True)
    Origin_Airport_Code = Column(String, nullable=False)
    Destination_Airport_Code = Column(String, nullable=False)

    booking = relationship("Booking", back_populates="flight_reservations")


class ActivityReservation(Base):
    __tablename__ = "activity_reservations"

    Activity_Reservation_Id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Booking_Id = Column(Integer, ForeignKey("bookings.Booking_Id"), nullable=False)
    Activity_Name = Column(String, nullable=False)
    Location = Column(String, nullable=True)
    Activity_Date = Column(Date, nullable=False)
    Price = Column(Float, nullable=True)

    booking = relationship("Booking", back_populates="activity_reservations")
