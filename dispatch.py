"""Dispatch prototype: radius-expansion matching logic using in-memory/DB lookups.
This file implements a simple function `start_dispatch_worker(job_id, lat, lon, service_type)`
which simulates searching for eligible drivers and assigns the first available match.
It is intended as a developer-friendly prototype and uses DB queries via SQLAlchemy.
"""

from .db import SessionLocal
from . import models
import math
import time

def haversine_miles(lat1, lon1, lat2, lon2):
    # Haversine formula to estimate distance in miles between two lat/lon pairs
    R = 3958.8  # Earth radius in miles
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def find_eligible_drivers(db, lat, lon, service_type, radius_miles):
    """
    Service rules:
    - flatbed & wheel_lift: can do all jobs
    - service_truck: roadside-only (no tows)
    """
    candidates = []
    drivers = db.query(models.Driver).filter(models.Driver.is_online == True).all()
    for d in drivers:
        # compute distance
        if d.current_lat is None or d.current_lon is None:
            continue
        dist = haversine_miles(lat, lon, d.current_lat, d.current_lon)
        if dist > radius_miles:
            continue
        # check vehicle capability: get primary vehicle for driver (first registered)
        veh = db.query(models.Vehicle).filter(models.Vehicle.driver_id == d.id).first()
        if not veh:
            continue
        if veh.type == "service_truck" and service_type in ["regular_tow", "accident_tow", "motorcycle_tow"]:
            # service truck cannot do tows
            continue
        candidates.append((d, veh, dist))
    # sort by distance ascending
    candidates.sort(key=lambda t: t[2])
    return candidates

def assign_job_to_driver(db, job, driver, vehicle):
    job.driver_id = driver.id
    job.vehicle_id = vehicle.id
    job.status = "assigned"
    db.add(job)
    db.commit()
    print(f"Assigned job {job.id} to driver {driver.id} (vehicle {vehicle.id})")

def start_dispatch_worker(job_id: str, lat: float, lon: float, service_type: str):
    """
    Simple synchronous radius-expansion dispatcher.
    In production this should be event-driven and async.
    """
    db = SessionLocal()
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        print("Job not found:", job_id)
        return False

    radius = 3.0  # miles initial radius
    attempts = 0
    max_attempts = 4
    while attempts < max_attempts:
        print(f"Dispatch attempt {attempts+1} radius={radius} miles for job {job_id}")
        candidates = find_eligible_drivers(db, lat, lon, service_type, radius)
        if candidates:
            # Offer to first candidate (synchronous accept simulation)
            d, v, dist = candidates[0]
            assign_job_to_driver(db, job, d, v)
            db.close()
            return True
        # expand radius and retry
        radius *= 2
        attempts += 1
        time.sleep(1)  # backoff in this prototype
    # no drivers found
    job.status = "unserviced"
    db.add(job)
    db.commit()
    db.close()
    print(f"No drivers found for job {job_id}")
    return False
