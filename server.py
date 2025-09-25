from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Road Guard API (minimal)")

# Keep CORS open for now; we'll tighten later to your Base44 domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}
# --- WebSocket endpoint ---
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        # Send a hello so the frontend knows it's connected
        await ws.send_json({"type": "hello", "msg": "road-guard ws connected"})
        # Echo any message back for basic testing
        while True:
            msg = await ws.receive_text()
            await ws.send_json({"type": "echo", "msg": msg})
    except WebSocketDisconnect:
        pass
# --- WebSocket endpoint (simple hello + echo) ---
from fastapi import WebSocket, WebSocketDisconnect

ACTIVE_SOCKETS = []

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ACTIVE_SOCKETS.append(ws)
    try:
        await ws.send_json({"type": "hello", "msg": "road-guard ws connected"})
        while True:
            # keep alive; echo any text messages
            msg = await ws.receive_text()
            await ws.send_json({"type": "echo", "msg": msg})
    except WebSocketDisconnect:
        pass
    finally:
        if ws in ACTIVE_SOCKETS:
            ACTIVE_SOCKETS.remove(ws)

# helper to push events to all connected clients
async def broadcast(msg: dict):
    dead = []
    for s in ACTIVE_SOCKETS:
        try:
            await s.send_json(msg)
        except Exception:
            dead.append(s)
    for s in dead:
        if s in ACTIVE_SOCKETS:
            ACTIVE_SOCKETS.remove(s)
            # --- Pricing & helpers (no DB; all in-memory) ---
from enum import Enum
from math import radians, sin, cos, asin, sqrt
from typing import Optional, Dict, Any
from pydantic import BaseModel
import time, uuid, asyncio

APP_CUT = 0.20  # app+tax cut = 20%

class VehicleClass(str, Enum):
    FLATBED = "flatbed"
    WHEEL_LIFT = "wheel_lift"
    SERVICE_TRUCK = "service_truck"  # can't tow

class ServiceType(str, Enum):
    REGULAR_TOW = "regular_tow"
    ACCIDENT_TOW = "accident_tow"
    MOTO_TOW = "motorcycle_tow"
    FLAT_TIRE_SEDAN = "flat_tire_sedan"
    FLAT_TIRE_TRUCK = "flat_tire_truck"
    FLAT_TIRE_DUALLY = "flat_tire_dually"
    FLAT_TIRE_TRAILER_RV = "flat_tire_trailer_rv"
    JUMPSTART = "jumpstart"
    LOCKOUT = "lockout"
    WINCH_OUT = "winch_out"

def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8  # miles
    dlat = radians(lat2 - lat1); dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))

def compute_price(svc: ServiceType, miles: float, within5mi: bool=False) -> Dict[str, Any]:
    miles = max(0.0, miles)
    total = 0.0
    details = {}

    if svc == ServiceType.REGULAR_TOW:
        base, free, per_mile = 105, 7, 5
        extra = max(0, miles - free)
        total = base + extra * per_mile
        details = {"base": base, "free_miles": free, "extra_miles": extra, "per_mile": per_mile}

    elif svc == ServiceType.ACCIDENT_TOW:
        base, free, per_mile = 295, 21, 5
        extra = max(0, miles - free)
        total = base + extra * per_mile
        details = {"base": base, "free_miles": free, "extra_miles": extra, "per_mile": per_mile}

    elif svc == ServiceType.MOTO_TOW:
        base, free, per_mile = 185, 7, 4
        extra = max(0, miles - free)
        total = base + extra * per_mile
        details = {"base": base, "free_miles": free, "extra_miles": extra, "per_mile": per_mile}

    elif svc in [ServiceType.FLAT_TIRE_SEDAN, ServiceType.FLAT_TIRE_TRUCK,
                 ServiceType.FLAT_TIRE_DUALLY, ServiceType.FLAT_TIRE_TRAILER_RV]:
        mapping = {
            ServiceType.FLAT_TIRE_SEDAN: 75,
            ServiceType.FLAT_TIRE_TRUCK: 85,
            ServiceType.FLAT_TIRE_DUALLY: 125,
            ServiceType.FLAT_TIRE_TRAILER_RV: 220,
        }
        total = mapping[svc]

    elif svc == ServiceType.JUMPSTART:
        total = 65 * (0.9 if within5mi else 1.0)

    elif svc == ServiceType.LOCKOUT:
        total = 75 * (0.9 if within5mi else 1.0)

    elif svc == ServiceType.WINCH_OUT:
        total = 195  # per hour; MVP assume 1 hr minimum

    app_cut = round(total * APP_CUT, 2)
    provider_earnings = round(total - app_cut, 2)
    return {"total": round(total, 2), "app_cut": app_cut, "provider": provider_earnings, "details": details}
    # --- Pydantic payloads ---
class QuoteReq(BaseModel):
    service: ServiceType
    pickup_lat: float
    pickup_lng: float
    drop_lat: Optional[float] = None
    drop_lng: Optional[float] = None

class RequestServiceReq(QuoteReq):
    customer_phone: str

class ProviderOnlineReq(BaseModel):
    provider_id: str
    vehicle: VehicleClass
    lat: float
    lng: float

# --- In-memory stores (MVP) ---
REQUESTS: Dict[str, Dict] = {}
PROVIDERS: Dict[str, Dict] = {}
JOBS: Dict[str, Dict] = {}
# --- Endpoints ---

@app.post("/quote")
def quote(body: QuoteReq):
    miles = 0.0
    if body.drop_lat is not None and body.drop_lng is not None:
        miles = haversine_miles(body.pickup_lat, body.pickup_lng, body.drop_lat, body.drop_lng)
    within5 = miles <= 5.0
    price = compute_price(body.service, miles, within5mi=within5)
    return {"miles": round(miles, 2), **price}

@app.post("/requests")
def create_request(body: RequestServiceReq):
    rid = str(uuid.uuid4())
    miles = 0.0
    if body.drop_lat is not None and body.drop_lng is not None:
        miles = haversine_miles(body.pickup_lat, body.pickup_lng, body.drop_lat, body.drop_lng)
    within5 = miles <= 5.0
    price = compute_price(body.service, miles, within5mi=within5)
    REQUESTS[rid] = {
        "id": rid, "ts": time.time(), "status": "open",
        "service": body.service, "pickup": [body.pickup_lat, body.pickup_lng],
        "drop": [body.drop_lat, body.drop_lng] if body.drop_lat is not None and body.drop_lng is not None else None,
        "miles": round(miles, 2), "price": price, "phone": body.customer_phone
    }
    JOBS[rid] = {"id": rid, "request_id": rid, "status": "open"}
    # optional: notify listeners
    asyncio.create_task(broadcast({"type": "job_opened", "job": JOBS[rid]}))
    return REQUESTS[rid]

@app.post("/providers/online")
def provider_online(p: ProviderOnlineReq):
    PROVIDERS[p.provider_id] = {
        "id": p.provider_id, "vehicle": p.vehicle,
        "lat": p.lat, "lng": p.lng, "online": True
    }
    return {"ok": True}

@app.get("/jobs/available")
def jobs_available(provider_id: str):
    prov = PROVIDERS.get(provider_id)
    if not prov or not prov.get("online"):
        return {"jobs": []}
    # capability filter
    def can_do(vehicle: VehicleClass, svc: ServiceType) -> bool:
        if vehicle == VehicleClass.SERVICE_TRUCK and svc in (
            ServiceType.REGULAR_TOW, ServiceType.ACCIDENT_TOW, ServiceType.MOTO_TOW
        ):
            return False
        return True
    capable = []
    for j in JOBS.values():
        if j["status"] != "open":
            continue
        req = REQUESTS[j["request_id"]]
        if can_do(prov["vehicle"], req["service"]):
            capable.append({
                "id": j["id"], "service": req["service"],
                "price": req["price"], "pickup": req["pickup"], "drop": req["drop"]
            })
    return {"jobs": capable}

@app.post("/jobs/{job_id}/accept")
def accept_job(job_id: str, provider_id: str):
    job = JOBS.get(job_id)
    if not job or job["status"] != "open":
        return {"ok": False, "error": "unavailable"}
    req = REQUESTS[job["request_id"]]
    prov = PROVIDERS.get(provider_id)
    if not prov or not prov.get("online"):
        return {"ok": False, "error": "provider_offline"}
    # capability check (service truck can't tow)
    if prov["vehicle"] == VehicleClass.SERVICE_TRUCK and req["service"] in (
        ServiceType.REGULAR_TOW, ServiceType.ACCIDENT_TOW, ServiceType.MOTO_TOW
    ):
        return {"ok": False, "error": "not_capable"}
    job["status"] = "assigned"
    job["provider_id"] = provider_id
    req["status"] = "assigned"
    asyncio.create_task(broadcast({"type": "job_assigned", "job": job, "request": req}))
    return {"ok": True, "job": job, "request": req}

@app.patch("/jobs/{job_id}/status")
def update_job(job_id: str, status: str):
    job = JOBS.get(job_id)
    if not job:
        return {"ok": False, "error": "not_found"}
    job["status"] = status
    REQUESTS[job["request_id"]]["status"] = status
    asyncio.create_task(broadcast({"type": "job_status", "job_id": job_id, "status": status}))
    return {"ok": True}
