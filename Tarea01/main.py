from fastapi import FastAPI
from app.database import engine
from app.models import Base  # ← usa import absoluto
from app.api import router

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Crear la aplicación
app = FastAPI(
    title="Sistema de Recepción Hospitalaria",
    description="API para gestionar la cola de pacientes en un hospital utilizando TDA Cola (FIFO)",
    version="1.0.0"
)

# Incluir los endpoints
app.include_router(router, prefix="/api")

# Ruta de inicio opcional
@app.get("/")
def read_root():
    return {
        "mensaje": "Bienvenido al Sistema de Recepción Hospitalaria",
        "documentación": "/docs"
    }
