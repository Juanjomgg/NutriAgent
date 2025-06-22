# ========================================
# app/main.py - FastAPI Application
# ========================================

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import os
from typing import List
import json
import logging

from .database.connection import engine, get_db
from .models import user, conversation, plans
from .api import auth, chat, plans as plans_api
from .services.memory_service import MemoryService
from .agents.orchestrator import AgentOrchestrator

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Manager para WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: dict = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections.remove(websocket)
        if user_id in self.user_connections:
            del self.user_connections[user_id]

    async def send_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            await self.user_connections[user_id].send_text(message)

manager = ConnectionManager()

# Startup event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas
    user.Base.metadata.create_all(bind=engine)
    conversation.Base.metadata.create_all(bind=engine)
    plans.Base.metadata.create_all(bind=engine)
    
    # Inicializar servicios
    memory_service = MemoryService()
    orchestrator = AgentOrchestrator()
    
    yield
    
    # Cleanup
    await memory_service.close()

app = FastAPI(
    title="Nutrition & Fitness AI Agent",
    description="Agente especializado en nutrición y fitness con IA",
    version="1.0.0",
    lifespan=lifespan
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Incluir routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(plans_api.router, prefix="/api/plans", tags=["plans"])

@app.get("/")
async def get_frontend():
    with open("frontend/index.html") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    orchestrator = AgentOrchestrator()
    
    try:
        while True:
            # Recibir mensaje del usuario
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            logger.info(f"Mensaje recibido de {user_id}: {message_data}")
            
            # Procesar con el orquestador
            response = await orchestrator.process_message(
                user_id=user_id,
                message=message_data["message"],
                context=message_data.get("context", {})
            )
            
            # Enviar respuesta
            await manager.send_message(json.dumps(response), user_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"Usuario {user_id} desconectado")