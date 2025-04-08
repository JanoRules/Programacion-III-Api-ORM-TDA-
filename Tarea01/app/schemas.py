from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ---------- PACIENTE ----------
class Paciente_HospitalBase(BaseModel):
    nombre: str
    apellido: str
    estado_atencion: Optional[str] = "En espera"
    nivel_prioridad: int  # Cambié a "prioridad" para que coincida con tu lógica de atención

class Paciente_HospitalCreate(Paciente_HospitalBase):
    pass

class Paciente_HospitalResponse(Paciente_HospitalBase):
    id: int
    fecha_ingreso: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- RECEPCIONISTA ----------
class Recepcionista_HospitalBase(BaseModel):
    nombre: str
    apellido: str
    turno: str

class Recepcionista_HospitalCreate(Recepcionista_HospitalBase):
    pass

class Recepcionista_HospitalResponse(Recepcionista_HospitalBase):
    id: int

    class Config:
        from_attributes = True
