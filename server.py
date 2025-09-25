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
