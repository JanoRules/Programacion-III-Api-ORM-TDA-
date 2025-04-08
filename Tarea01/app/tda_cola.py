from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import RecepcionistaPaciente, Paciente_Hospital, EstadoAtencion

class ColaPaciente:
    def __init__(self, db: Session, recepcionista_id: int):  # Corregido de ___init__ a __init__
        self.db = db
        self.recepcionista_id = recepcionista_id
        
    def enqueue(self, paciente_id: int):
        presente = self.db.query(RecepcionistaPaciente).filter(
            RecepcionistaPaciente.recepcionista_id == self.recepcionista_id,
            RecepcionistaPaciente.paciente_id == paciente_id
        ).first()
        if presente:
            return False 
        
        ultima_posicion = self.db.query(func.max(RecepcionistaPaciente.posicion_cola)).filter(
            RecepcionistaPaciente.recepcionista_id == self.recepcionista_id
        ).scalar() or 0
        
        nueva_entrada = RecepcionistaPaciente(
            recepcionista_id=self.recepcionista_id,
            paciente_id=paciente_id,
            posicion_cola=ultima_posicion + 1
        )
        self.db.add(nueva_entrada)
        
        # actualizar el estado del paciente a "en_espera"
        paciente = self.db.query(Paciente_Hospital).filter(Paciente_Hospital.id == paciente_id).first()
        paciente.estado_atencion = EstadoAtencion.ESPERA
        self.db.commit()
        return True
    
    def dequeue(self):
        entrada = self.db.query(RecepcionistaPaciente).filter(
            RecepcionistaPaciente.recepcionista_id == self.recepcionista_id
        ).order_by(RecepcionistaPaciente.posicion_cola).first()
        
        if not entrada:
            return None
        
        paciente_id = entrada.paciente_id
        self.db.delete(entrada) # eliminar el paciente de la cola
        
        entradas_restantes = self.db.query(RecepcionistaPaciente).filter(
            RecepcionistaPaciente.recepcionista_id == self.recepcionista_id,
            RecepcionistaPaciente.posicion_cola > entrada.posicion_cola
        ).all()
        
        for i, entrada in enumerate(entradas_restantes, 1):
            entrada.posicion_cola = i
        
        # Actualizar estado del paciente
        paciente = self.db.query(Paciente_Hospital).filter(Paciente_Hospital.id == paciente_id).first()
        paciente.estado_atencion = EstadoAtencion.ATENDIDO
        self.db.commit()
        return paciente
    
    def first(self): # Ver el próximo paciente a atender sin removerlo de la cola
        entrada = self.db.query(RecepcionistaPaciente).filter(
            RecepcionistaPaciente.recepcionista_id == self.recepcionista_id
        ).order_by(RecepcionistaPaciente.posicion_cola).first()
        
        if not entrada:
            return None
        
        paciente = self.db.query(Paciente_Hospital).filter(Paciente_Hospital.id == entrada.paciente_id).first()
        return paciente
        
    def size(self):
        return self.db.query(RecepcionistaPaciente).filter(
            RecepcionistaPaciente.recepcionista_id == self.recepcionista_id
        ).count()
        
    def is_empty(self):
        return self.size() == 0
    