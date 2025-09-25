"""Simple seeding script to populate the DB with users/drivers and test a dispatch.
Run inside the container after DB is up:
    python -m app.create_tables
    python -m app.seed
"""
from .db import SessionLocal
from . import models
from .dispatch import start_dispatch_worker

def seed():
    db = SessionLocal()
    # Create two drivers with vehicles
    d1 = models.Driver(display_name="Alice Flatbed", rating=4.9, is_online=True, current_lat=32.7767, current_lon=-96.7970)
    d2 = models.Driver(display_name="Bob Service", rating=4.8, is_online=True, current_lat=32.78, current_lon=-96.80)
    db.add_all([d1, d2])
    db.commit(); db.refresh(d1); db.refresh(d2)

    v1 = models.Vehicle(driver_id=d1.id, type="flatbed", plate="FB123")
    v2 = models.Vehicle(driver_id=d2.id, type="service_truck", plate="SV456")
    db.add_all([v1, v2]); db.commit()

    # Create a user and a job request (regular tow)
    u = models.User(phone="555-1111", email="user@test.com")
    db.add(u); db.commit(); db.refresh(u)

    j = models.Job(user_id=u.id, service_type="regular_tow", status="requested",
                   pickup_lat=32.7768, pickup_lon=-96.7971)
    db.add(j); db.commit(); db.refresh(j); db.close()

    # Run dispatcher (assigns to Alice Flatbed)
    start_dispatch_worker(str(j.id), 32.7768, -96.7971, "regular_tow")
    print("Seed complete. Created job:", j.id)

if __name__ == "__main__":
    seed()
