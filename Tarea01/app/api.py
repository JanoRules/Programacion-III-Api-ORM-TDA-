from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .database import get_db
from .models import Recepcionista_Hospital, Paciente_Hospital, EstadoAtencion, RecepcionistaPaciente
from .schemas import Recepcionista_HospitalCreate, Recepcionista_HospitalResponse, Paciente_HospitalCreate, Paciente_HospitalResponse
from .tda_cola import ColaPaciente

app = FastAPI(title="Sistema de Gestión de Hospital", 
              description="API para gestionar recepcionistas y pacientes en un hospital")

router = APIRouter(tags=["Hospital"])

# Endpoints para recepcionistas
@router.post("/recepcionistas/", response_model=Recepcionista_HospitalResponse)
def crear_recepcionista(recepcionista: Recepcionista_HospitalCreate, db: Session = Depends(get_db)):
    db_recepcionista = Recepcionista_Hospital(
        nombre=recepcionista.nombre,
        apellido=recepcionista.apellido,
        turno=recepcionista.turno
    )
    db.add(db_recepcionista)
    db.commit()
    db.refresh(db_recepcionista)
    return db_recepcionista

@router.get("/recepcionistas/", response_model=List[Recepcionista_HospitalResponse])
def listar_recepcionistas(db: Session = Depends(get_db)):
    recepcionistas = db.query(Recepcionista_Hospital).all()
    return recepcionistas

# Endpoints para pacientes
@router.post("/pacientes/", response_model=Paciente_HospitalResponse)
def crear_paciente(paciente: Paciente_HospitalCreate, db: Session = Depends(get_db)):
    db_paciente = Paciente_Hospital(
        nombre=paciente.nombre,
        apellido=paciente.apellido,
        nivel_prioridad=paciente.nivel_prioridad
    )
    db.add(db_paciente)
    db.commit()
    db.refresh(db_paciente)
    return db_paciente

@router.get("/pacientes/", response_model=List[Paciente_HospitalResponse])
def obtener_pacientes(db: Session = Depends(get_db)):
    return db.query(Paciente_Hospital).order_by(Paciente_Hospital.nivel_prioridad).all()

# Gestión de la cola de pacientes
@router.post("/cola/agregar/{recepcionista_id}/{paciente_id}")
def encolar_paciente(recepcionista_id: int, paciente_id: int, db: Session = Depends(get_db)):
    # Verificar que existan recepcionista y paciente
    recepcionista = db.query(Recepcionista_Hospital).filter(Recepcionista_Hospital.id == recepcionista_id).first()
    if not recepcionista:
        raise HTTPException(status_code=404, detail="Recepcionista no encontrado")
    
    paciente = db.query(Paciente_Hospital).filter(Paciente_Hospital.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    # Instanciar la cola y agregar el paciente
    cola = ColaPaciente(db, recepcionista_id)
    resultado = cola.enqueue(paciente_id)
    
    if resultado:
        return {
            "message": f"Paciente {paciente.nombre} {paciente.apellido} añadido a la cola del recepcionista {recepcionista.nombre}"
        }
    else:
        return {
            "message": f"El paciente ya está en la cola del recepcionista {recepcionista.nombre}"
        }

@router.post("/recepcionistas/{recepcionista_id}/atender")
def atender_paciente(recepcionista_id: int, db: Session = Depends(get_db)):
    # Verificar que exista el recepcionista
    recepcionista = db.query(Recepcionista_Hospital).filter(Recepcionista_Hospital.id == recepcionista_id).first()
    if not recepcionista:
        raise HTTPException(status_code=404, detail="Recepcionista no encontrado")
    
    # Instanciar la cola y obtener el siguiente paciente
    cola = ColaPaciente(db, recepcionista_id)
    if cola.is_empty():
        raise HTTPException(status_code=404, detail="No hay pacientes en la cola")
    
    paciente = cola.dequeue()
    if not paciente:
        raise HTTPException(status_code=404, detail="Error al obtener el paciente")
    
    return {
        "message": f"Paciente {paciente.nombre} {paciente.apellido} atendido por recepcionista {recepcionista.nombre} {recepcionista.apellido}",
        "paciente_id": paciente.id,
    }

@router.get("/recepcionistas/{recepcionista_id}/proximo")
def ver_proximo_paciente(recepcionista_id: int, db: Session = Depends(get_db)):
    # Verificar que exista el recepcionista
    recepcionista = db.query(Recepcionista_Hospital).filter(Recepcionista_Hospital.id == recepcionista_id).first()
    if not recepcionista:
        raise HTTPException(status_code=404, detail="Recepcionista no encontrado")
    
    # Instanciar la cola y obtener el próximo paciente
    cola = ColaPaciente(db, recepcionista_id)
    if cola.is_empty():
        raise HTTPException(status_code=404, detail="No hay pacientes en la cola")
    
    paciente = cola.first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Error al obtener el paciente")
    
    return {
        "message": f"Próximo paciente a atender",
        "paciente": {
            "id": paciente.id,
            "nombre": paciente.nombre,
            "apellido": paciente.apellido,
            "nivel_prioridad": paciente.nivel_prioridad
        }
    }

@router.get("/recepcionistas/{recepcionista_id}/cola")
def listar_pacientes_en_espera(recepcionista_id: int, db: Session = Depends(get_db)):
    # Verificar que exista el recepcionista
    recepcionista = db.query(Recepcionista_Hospital).filter(Recepcionista_Hospital.id == recepcionista_id).first()
    if not recepcionista:
        raise HTTPException(status_code=404, detail="Recepcionista no encontrado")
    
    # Obtener pacientes en orden FIFO
    entradas = db.query(RecepcionistaPaciente).filter(
        RecepcionistaPaciente.recepcionista_id == recepcionista_id
    ).order_by(RecepcionistaPaciente.posicion_cola).all()
    
    pacientes = []
    for entrada in entradas:
        paciente = db.query(Paciente_Hospital).filter(Paciente_Hospital.id == entrada.paciente_id).first()
        if paciente:
            pacientes.append({
                "id": paciente.id,
                "nombre": paciente.nombre,
                "apellido": paciente.apellido,
                "nivel_prioridad": paciente.nivel_prioridad,
                "posicion_cola": entrada.posicion_cola
            })
    
    return {"pacientes_en_cola": pacientes, "total": len(pacientes)}

@router.get("/recepcionistas/{recepcionista_id}/tamaño_cola")
def tamaño_cola(recepcionista_id: int, db: Session = Depends(get_db)):
    recepcionista = db.query(Recepcionista_Hospital).filter(Recepcionista_Hospital.id == recepcionista_id).first()
    if not recepcionista:
        raise HTTPException(status_code=404, detail="Recepcionista no encontrado")
    
    cola = ColaPaciente(db, recepcionista_id)
    return {
        "recepcionista": f"{recepcionista.nombre} {recepcionista.apellido}", 
        "tamaño_cola": cola.size()
    }


# Incluir el router en la aplicación
app.include_router(router, prefix="/api")