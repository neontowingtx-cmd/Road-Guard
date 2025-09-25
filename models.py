from sqlalchemy import Column, String, Float, Boolean, Integer, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

def gen_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    phone = Column(String(32), unique=True, nullable=True)
    email = Column(String(256), unique=True, nullable=True)

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    display_name = Column(String(200))
    rating = Column(Float, default=5.0)
    is_online = Column(Boolean, default=False)
    # simple lat/lon columns for demo (in production use PostGIS Point)
    current_lat = Column(Float, nullable=True)
    current_lon = Column(Float, nullable=True)

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    driver_id = Column(UUID(as_uuid=False), ForeignKey("drivers.id"))
    type = Column(String(50))  # flatbed | wheel_lift | service_truck
    plate = Column(String(32), nullable=True)
    make = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), nullable=True)
    driver_id = Column(UUID(as_uuid=False), ForeignKey("drivers.id"), nullable=True)
    service_type = Column(String(100))
    status = Column(String(50), default="requested")
    pickup_lat = Column(Float, nullable=True)
    pickup_lon = Column(Float, nullable=True)
    dropoff_lat = Column(Float, nullable=True)
    dropoff_lon = Column(Float, nullable=True)
    base_price = Column(Numeric(10,2), nullable=True)
    distance_miles = Column(Float, nullable=True)
    extra_charges = Column(Numeric(10,2), default=0.00)
    total_amount = Column(Numeric(10,2), nullable=True)

class DriverWallet(Base):
    __tablename__ = "driver_wallets"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    driver_id = Column(UUID(as_uuid=False), ForeignKey("drivers.id"))
    balance = Column(Numeric(12,2), default=0.00)

class Rating(Base):
    __tablename__ = "ratings"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    job_id = Column(UUID(as_uuid=False), ForeignKey("jobs.id"))
    from_user = Column(UUID(as_uuid=False), nullable=True)
    to_driver = Column(UUID(as_uuid=False), nullable=True)
    stars = Column(Integer)
    comment = Column(String(500))
