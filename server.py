from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your other modules using absolute imports
from db import get_db_session, engine, SessionLocal
import models, pricing, dispatch  # add others if needed

app = FastAPI(title="Road Guard API")

# Basic CORS (you can tighten this later)
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

# If you have routes in main.py you want to keep,
# you can import and include them here like:
# from main import some_router
# app.include_router(some_router)
