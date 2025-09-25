from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import threading
import time

from .db import get_db_session, engine, SessionLocal
from . import models
from .dispatch import start_dispatch_worker

app = FastAPI(title="Towing & Roadside Assistance API", version="0.2.0")

# Simple startup: create tables if they don't exist
models.Base.metadata.create_all(bind=engine)


class SignupIn(BaseModel):
    phone: Optional[str]
    email: Optional[str]
    password: Optional[str]


@app.post("/auth/signup")
def signup(payload: SignupIn):
    # Simplified: create a user record (no password hashing in this skeleton)
    db = SessionLocal()
    user = models.User(phone=payload.phone, email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return {"ok": True, "user_id": str(user.id)}


@app.post("/auth/login")
def login(phone: str, password: str):
    # TODO: implement real auth, return JWT
    return {"ok": True, "token": "local-dev-token"}


@app.post("/driver/apply")
def driver_apply(full_name: str, phone: str):
    db = SessionLocal()
    # create a driver profile in pending state
    driver = models.Driver(display_name=full_name, rating=5.0, is_online=False)
    db.add(driver)
    db.commit()
    db.refresh(driver)
    db.close()
    return {"ok": True, "driver_id": str(driver.id)}


@app.post("/driver/{driver_id}/vehicles")
def add_vehicle(driver_id: str, type: str, plate: Optional[str] = None, make: Optional[str] = None, model: Optional[str] = None):
    db = SessionLocal()
    drv = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not drv:
        db.close()
        raise HTTPException(status_code=404, detail="Driver not found")
    vehicle = models.Vehicle(driver_id=driver_id, type=type, plate=plate, make=make, model=model)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    db.close()
    return {"ok": True, "vehicle_id": str(vehicle.id)}


@app.post("/driver/{driver_id}/go_online")
def go_online(driver_id: str, lat: float, lon: float):
    db = SessionLocal()
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not driver:
        db.close()
        raise HTTPException(status_code=404, detail="Driver not found")
    driver.is_online = True
    driver.current_lat = lat
    driver.current_lon = lon
    db.add(driver)
    db.commit()
    db.close()
    return {"ok": True, "driver_id": driver_id, "lat": lat, "lon": lon}


class JobRequest(BaseModel):
    user_id: str
    pickup_lat: float
    pickup_lon: float
    service_type: str
    dropoff_lat: Optional[float] = None
    dropoff_lon: Optional[float] = None


@app.post("/jobs/request")
def create_job(req: JobRequest, background_tasks: BackgroundTasks):
    db = SessionLocal()
    job = models.Job(
        user_id=req.user_id,
        service_type=req.service_type,
        status="requested",
        pickup_lat=req.pickup_lat,
        pickup_lon=req.pickup_lon,
        dropoff_lat=req.dropoff_lat,
        dropoff_lon=req.dropoff_lon,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    db.close()

    # Enqueue job into dispatch worker via Redis pub/sub (dispatch worker listens)
    # For this skeleton we'll call a simple in-process dispatcher function asynchronously
    background_tasks.add_task(start_dispatch_worker, str(job.id), req.pickup_lat, req.pickup_lon, req.service_type)

    return {"ok": True, "job_id": str(job.id), "status": job.status}


# --- WebSocket manager for real-time updates (drivers & users) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        ws = self.active_connections.get(client_id)
        if ws:
            await ws.send_json(message)


manager = ConnectionManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # echo for now
            await manager.send_personal_message({"echo": data}, client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)


# Simple health
@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})
