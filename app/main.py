from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import date, time, datetime, timedelta
from decimal import Decimal

from app.config import get_settings
from app.database import init_db, get_db
from app.models import Doctor, Patient, Service, Schedule, Slot, Appointment
from pydantic import BaseModel

# ==================== Pydantic Models ====================
class DoctorCreate(BaseModel):
    full_name: str
    specialization: str
    phone: Optional[str] = None

class DoctorUpdate(BaseModel):
    full_name: Optional[str] = None
    specialization: Optional[str] = None
    phone: Optional[str] = None

class DoctorResponse(BaseModel):
    id: int
    full_name: str
    specialization: str
    phone: Optional[str] = None
    model_config = {"from_attributes": True}

class PatientCreate(BaseModel):
    full_name: str
    birth_date: date
    phone: Optional[str] = None
    email: Optional[str] = None

class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class PatientResponse(BaseModel):
    id: int
    full_name: str
    birth_date: date
    phone: Optional[str] = None
    email: Optional[str] = None
    model_config = {"from_attributes": True}

class ServiceCreate(BaseModel):
    name: str
    price: Decimal
    duration: int
    specialization: str

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    duration: Optional[int] = None
    specialization: Optional[str] = None

class ServiceResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    duration: int
    specialization: str
    model_config = {"from_attributes": True}

class ScheduleCreate(BaseModel):
    doctor_id: int
    date: date
    start_time: time
    end_time: time

class ScheduleUpdate(BaseModel):
    doctor_id: Optional[int] = None
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class ScheduleResponse(BaseModel):
    id: int
    doctor_id: int
    date: date
    start_time: time
    end_time: time
    model_config = {"from_attributes": True}

class SlotResponse(BaseModel):
    id: int
    schedule_id: int
    start_time: time
    end_time: time
    is_blocked: bool
    model_config = {"from_attributes": True}

class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    service_id: int
    slot_id: int

class AppointmentUpdate(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    service_id: Optional[int] = None
    slot_id: Optional[int] = None

class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    service_id: int
    slot_id: int
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}

# ==================== FastAPI App ====================
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("БД готова")
    yield

app = FastAPI(title=settings.app_title, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== DOCTORS ====================
@app.post("/doctors/", response_model=DoctorResponse)
async def create_doctor(data: DoctorCreate, db: AsyncSession = Depends(get_db)):
    obj = Doctor(**data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj

@app.get("/doctors/", response_model=List[DoctorResponse])
async def get_doctors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor))
    return result.scalars().all()

@app.get("/doctors/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
    doctor = await db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(404, "Врач не найден")
    return doctor

@app.put("/doctors/{doctor_id}", response_model=DoctorResponse)
async def update_doctor(doctor_id: int, data: DoctorUpdate, db: AsyncSession = Depends(get_db)):
    doctor = await db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(404, "Врач не найден")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(doctor, key, value)
    await db.flush()
    await db.refresh(doctor)
    return doctor

@app.delete("/doctors/{doctor_id}")
async def delete_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
    # Сначала удаляем все записи этого врача
    from sqlalchemy import delete as sql_delete
    await db.execute(sql_delete(Appointment).where(Appointment.doctor_id == doctor_id))
    
    # Потом удаляем врача
    doctor = await db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(404, "Врач не найден")
    await db.delete(doctor)
    await db.flush()
    return {"ok": True}

# ==================== PATIENTS ====================
@app.post("/patients/", response_model=PatientResponse)
async def create_patient(data: PatientCreate, db: AsyncSession = Depends(get_db)):
    obj = Patient(**data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj

@app.get("/patients/", response_model=List[PatientResponse])
async def get_patients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patient))
    return result.scalars().all()

@app.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_db)):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Пациент не найден")
    return patient

@app.put("/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: int, data: PatientUpdate, db: AsyncSession = Depends(get_db)):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Пациент не найден")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)
    await db.flush()
    await db.refresh(patient)
    return patient

@app.delete("/patients/{patient_id}")
async def delete_patient(patient_id: int, db: AsyncSession = Depends(get_db)):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Пациент не найден")
    await db.delete(patient)
    await db.flush()
    return {"ok": True}

# ==================== SERVICES ====================
@app.post("/services/", response_model=ServiceResponse)
async def create_service(data: ServiceCreate, db: AsyncSession = Depends(get_db)):
    obj = Service(**data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj

@app.get("/services/", response_model=List[ServiceResponse])
async def get_services(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Service))
    return result.scalars().all()

@app.get("/services/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: int, db: AsyncSession = Depends(get_db)):
    service = await db.get(Service, service_id)
    if not service:
        raise HTTPException(404, "Услуга не найдена")
    return service

@app.put("/services/{service_id}", response_model=ServiceResponse)
async def update_service(service_id: int, data: ServiceUpdate, db: AsyncSession = Depends(get_db)):
    service = await db.get(Service, service_id)
    if not service:
        raise HTTPException(404, "Услуга не найдена")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(service, key, value)
    await db.flush()
    await db.refresh(service)
    return service

@app.delete("/services/{service_id}")
async def delete_service(service_id: int, db: AsyncSession = Depends(get_db)):
    service = await db.get(Service, service_id)
    if not service:
        raise HTTPException(404, "Услуга не найдена")
    await db.delete(service)
    await db.flush()
    return {"ok": True}

# ==================== SCHEDULES ====================
@app.post("/schedules/", response_model=ScheduleResponse)
async def create_schedule(data: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    obj = Schedule(**data.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj

@app.get("/schedules/", response_model=List[ScheduleResponse])
async def get_schedules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Schedule))
    return result.scalars().all()

@app.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    schedule = await db.get(Schedule, schedule_id)
    if not schedule:
        raise HTTPException(404, "Расписание не найдено")
    return schedule

@app.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(schedule_id: int, data: ScheduleUpdate, db: AsyncSession = Depends(get_db)):
    schedule = await db.get(Schedule, schedule_id)
    if not schedule:
        raise HTTPException(404, "Расписание не найдено")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(schedule, key, value)
    await db.flush()
    await db.refresh(schedule)
    return schedule

@app.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    schedule = await db.get(Schedule, schedule_id)
    if not schedule:
        raise HTTPException(404, "Расписание не найдено")
    await db.delete(schedule)
    await db.flush()
    return {"ok": True}

# ==================== SLOTS (ВАЖЕН ПОРЯДОК!) ====================
@app.post("/schedules/{schedule_id}/generate-slots")
async def generate_slots(schedule_id: int, slot_duration: int = 30, db: AsyncSession = Depends(get_db)):
    schedule = await db.get(Schedule, schedule_id)
    if not schedule:
        raise HTTPException(404, "Расписание не найдено")
    
    old_slots = await db.execute(select(Slot).where(Slot.schedule_id == schedule_id))
    for slot in old_slots.scalars().all():
        await db.delete(slot)
    
    start = datetime.combine(schedule.date, schedule.start_time)
    end = datetime.combine(schedule.date, schedule.end_time)
    current = start
    
    while current + timedelta(minutes=slot_duration) <= end:
        slot_end = current + timedelta(minutes=slot_duration)
        slot = Slot(
            schedule_id=schedule_id,
            start_time=current.time(),
            end_time=slot_end.time(),
            is_blocked=False
        )
        db.add(slot)
        current = slot_end
    
    await db.flush()
    result = await db.execute(select(Slot).where(Slot.schedule_id == schedule_id).order_by(Slot.start_time))
    return result.scalars().all()

# /available ДОЛЖЕН быть перед /{schedule_id}
@app.get("/slots/available", response_model=List[SlotResponse])
async def get_available_slots(doctor_id: int, date_from: str, date_to: str, db: AsyncSession = Depends(get_db)):
    try:
        d_from = date.fromisoformat(date_from[:10])
        d_to = date.fromisoformat(date_to[:10])
    except:
        raise HTTPException(400, "Неверный формат даты")
    
    schedule_result = await db.execute(
        select(Schedule.id).where(
            Schedule.doctor_id == doctor_id,
            Schedule.date >= d_from,
            Schedule.date <= d_to
        )
    )
    schedule_ids = [row[0] for row in schedule_result.fetchall()]
    if not schedule_ids:
        return []
    result = await db.execute(
        select(Slot).where(Slot.schedule_id.in_(schedule_ids), Slot.is_blocked == False).order_by(Slot.start_time)
    )
    return result.scalars().all()

@app.get("/slots/{schedule_id}", response_model=List[SlotResponse])
async def get_slots(schedule_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Slot).where(Slot.schedule_id == schedule_id).order_by(Slot.start_time))
    return result.scalars().all()

@app.delete("/slots/{slot_id}")
async def delete_slot(slot_id: int, db: AsyncSession = Depends(get_db)):
    slot = await db.get(Slot, slot_id)
    if not slot:
        raise HTTPException(404, "Слот не найден")
    await db.delete(slot)
    await db.flush()
    return {"ok": True}

# ==================== APPOINTMENTS ====================
@app.post("/appointments/", response_model=AppointmentResponse)
async def create_appointment(data: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    slot = await db.get(Slot, data.slot_id)
    if not slot:
        raise HTTPException(404, "Слот не найден")
    if slot.is_blocked:
        raise HTTPException(409, "Слот уже занят")
    
    patient = await db.get(Patient, data.patient_id)
    doctor = await db.get(Doctor, data.doctor_id)
    service = await db.get(Service, data.service_id)
    
    if not patient: raise HTTPException(404, "Пациент не найден")
    if not doctor: raise HTTPException(404, "Врач не найден")
    if not service: raise HTTPException(404, "Услуга не найдена")
    
    obj = Appointment(**data.model_dump())
    db.add(obj)
    slot.is_blocked = True
    await db.flush()
    await db.refresh(obj)
    return obj

@app.get("/appointments/", response_model=List[AppointmentResponse])
async def get_appointments(status_filter: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Appointment).order_by(Appointment.created_at.desc())
    if status_filter:
        query = query.where(Appointment.status == status_filter)
    result = await db.execute(query)
    return result.scalars().all()

@app.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    appointment = await db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, "Запись не найдена")
    return appointment

@app.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(appointment_id: int, data: AppointmentUpdate, db: AsyncSession = Depends(get_db)):
    appointment = await db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, "Запись не найдена")
    
    old_slot_id = appointment.slot_id
    update_data = data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(appointment, key, value)
    
    if 'slot_id' in update_data and update_data['slot_id'] != old_slot_id:
        old_slot = await db.get(Slot, old_slot_id)
        if old_slot:
            old_slot.is_blocked = False
        new_slot = await db.get(Slot, update_data['slot_id'])
        if new_slot:
            new_slot.is_blocked = True
    
    await db.flush()
    await db.refresh(appointment)
    return appointment

@app.patch("/appointments/{appointment_id}/status")
async def update_appointment_status(appointment_id: int, status: str, db: AsyncSession = Depends(get_db)):
    appointment = await db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, "Запись не найдена")
    
    old_status = appointment.status
    appointment.status = status
    
    if status in ['cancelled', 'no_show'] and old_status not in ['cancelled', 'no_show']:
        slot = await db.get(Slot, appointment.slot_id)
        if slot:
            slot.is_blocked = False
    
    await db.flush()
    await db.refresh(appointment)
    return appointment

@app.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    appointment = await db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, "Запись не найдена")
    slot = await db.get(Slot, appointment.slot_id)
    if slot:
        slot.is_blocked = False
    await db.delete(appointment)
    await db.flush()
    return {"ok": True}

app.mount("/", StaticFiles(directory="static", html=True), name="static")
