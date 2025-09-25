# Simple helper to create DB tables using SQLAlchemy models
from .db import engine
from .models import Base

def create_all():
    print("Creating DB tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    create_all()
