from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from datetime import date
from .base import BaseDBModel, PyObjectId

class UserRole(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    PATIENT = "patient"
    STAFF = "staff"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class UserBase(BaseDBModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE
    profile_image: Optional[str] = None

class PatientModel(UserBase):
    date_of_birth: date
    blood_group: Optional[str] = None
    allergies: List[str] = []
    emergency_contact: Optional[dict] = None
    medical_history: List[str] = []
    insurance_info: Optional[dict] = None

class MedicalStaffModel(UserBase):
    specialization: Optional[str] = None
    qualifications: List[str] = []
    license_number: str
    department_id: PyObjectId
    schedule: Optional[dict] = None
    years_of_experience: Optional[int] = None

class AdminModel(UserBase):
    department: Optional[str] = None
    access_level: int = 1
    permissions: List[str] = []