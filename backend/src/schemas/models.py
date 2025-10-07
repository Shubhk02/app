from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = Field(..., regex='^(admin|doctor|nurse|patient)$')
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AppointmentBase(BaseModel):
    patient_id: PyObjectId
    doctor_id: PyObjectId
    date: datetime
    reason: str
    status: str = Field(..., regex='^(scheduled|completed|cancelled)$')

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentDB(AppointmentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class MedicalRecordBase(BaseModel):
    patient_id: PyObjectId
    doctor_id: PyObjectId
    diagnosis: str
    prescription: Optional[str] = None
    notes: Optional[str] = None
    attachments: Optional[List[str]] = None

class MedicalRecordCreate(MedicalRecordBase):
    pass

class MedicalRecordDB(MedicalRecordBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}