from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from sqlalchemy import Enum as SQLAEnum 

Base = declarative_base()
class EstadoAtencion(enum.Enum):
    ESPERA = "En espera"
    ATENDIDO = "Atendido"
    EN_PROCESO = "En proceso"

class Recepcionista_Hospital(Base):
    __tablename__ = "recepcionista_hospital"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    turno = Column(String(50), nullable=False)
    
    pacientes = relationship("RecepcionistaPaciente", back_populates="recepcionista")

    def __repr__(self):
        return f"<Recepcionista_Hospital(nombre='{self.nombre}', apellido='{self.apellido}', turno='{self.turno}')>"

class Paciente_Hospital(Base):
    __tablename__ = "paciente_hospital"
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    estado_atencion = Column(SQLAEnum(EstadoAtencion), nullable=False, default=EstadoAtencion.ESPERA)
    nivel_prioridad = Column(Integer, default=3)  # ← CAMBIO AQUÍ
    fecha_ingreso = Column(DateTime, default=datetime.utcnow)

    recepcionistas = relationship("RecepcionistaPaciente", back_populates="paciente")

    def __repr__(self):
        return f"<Paciente_Hospital(nombre='{self.nombre}', apellido='{self.apellido}', prioridad='{self.nivel_prioridad}')>"
    
class RecepcionistaPaciente(Base):
    __tablename__ = "recepcionista_paciente"

    recepcionista_id = Column(Integer, ForeignKey("recepcionista_hospital.id"), primary_key=True)
    paciente_id = Column(Integer, ForeignKey("paciente_hospital.id"), primary_key=True)
    posicion_cola = Column(Integer)
    hora_registro = Column(DateTime, default=datetime.utcnow)

    recepcionista = relationship("Recepcionista_Hospital", back_populates="pacientes")
    paciente = relationship("Paciente_Hospital", back_populates="recepcionistas")

       
       