from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from .base import BaseDBModel, PyObjectId

class DepartmentModel(BaseDBModel):
    name: str
    description: Optional[str] = None
    head_doctor_id: Optional[PyObjectId] = None
    staff_ids: List[PyObjectId] = []
    location: Optional[str] = None
    contact_info: Optional[dict] = None

class RoomModel(BaseDBModel):
    number: str
    department_id: PyObjectId
    type: str  # ward, operation_theater, consultation, etc.
    capacity: int
    status: str = "available"  # available, occupied, maintenance
    equipment: List[dict] = []
    current_patients: List[PyObjectId] = []

class InventoryItemModel(BaseDBModel):
    name: str
    category: str
    quantity: int
    unit: str
    department_id: Optional[PyObjectId] = None
    minimum_quantity: int
    supplier_info: Optional[dict] = None
    last_restocked: Optional[datetime] = None
    status: str = "available"

class BillingModel(BaseDBModel):
    patient_id: PyObjectId
    appointment_id: Optional[PyObjectId] = None
    services: List[dict]
    total_amount: float
    insurance_coverage: Optional[float] = None
    payment_status: str = "pending"
    payment_method: Optional[str] = None
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None