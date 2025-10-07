from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from .base import BaseDBModel, PyObjectId

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class AppointmentModel(BaseDBModel):
    patient_id: PyObjectId
    doctor_id: PyObjectId
    date_time: datetime
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    reason: str
    notes: Optional[str] = None
    duration_minutes: int = 30
    room_id: Optional[PyObjectId] = None

class MedicalRecordModel(BaseDBModel):
    patient_id: PyObjectId
    doctor_id: PyObjectId
    appointment_id: Optional[PyObjectId] = None
    diagnosis: str
    symptoms: List[str]
    treatment: str
    prescription: Optional[List[dict]] = None
    notes: Optional[str] = None
    attachments: List[str] = []

class PrescriptionModel(BaseDBModel):
    medical_record_id: PyObjectId
    patient_id: PyObjectId
    doctor_id: PyObjectId
    medications: List[dict]
    instructions: str
    start_date: datetime
    end_date: Optional[datetime] = None
    refills: int = 0
    status: str = "active"