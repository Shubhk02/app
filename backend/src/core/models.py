from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from src.core.database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    PATIENT = "patient"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(Enum(UserRole))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    appointments = relationship("Appointment", back_populates="patient")
    doctor_appointments = relationship("Appointment", back_populates="doctor", foreign_keys="Appointment.doctor_id")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))
    appointment_date = Column(DateTime)
    reason = Column(String)
    status = Column(String)  # Scheduled, Completed, Cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("User", back_populates="appointments", foreign_keys=[patient_id])
    doctor = relationship("User", back_populates="doctor_appointments", foreign_keys=[doctor_id])