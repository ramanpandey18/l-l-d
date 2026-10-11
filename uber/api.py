"""
api.py
FastAPI layer exposing RideService as HTTP endpoints.
Run: uvicorn api:app --reload
Docs: http://127.0.0.1:8000/docs (Swagger UI - test everything here)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel  # type: ignore[import-not-found]

from models import Location
from repository import InMemoryStore
from matching import MatchingStrategy
from pricing import PricingEngine
from service import RideService

app = FastAPI(title="Uber LLD Demo")

# Single shared instance (in-memory state lives for the lifetime of the process)
store = InMemoryStore()
matcher = MatchingStrategy(max_radius_km=10)
pricing = PricingEngine()
service = RideService(store, matcher, pricing)


# ---------- Request/Response schemas ----------

class RegisterRiderRequest(BaseModel):
    name: str


class RegisterDriverRequest(BaseModel):
    name: str
    lat: float
    lng: float
    vehicle_type: str = "SEDAN"


class RequestRideRequest(BaseModel):
    rider_id: str
    pickup_lat: float
    pickup_lng: float
    drop_lat: float
    drop_lng: float
    vehicle_type: str = "SEDAN"


class SurgeRequest(BaseModel):
    multiplier: float


def trip_to_dict(trip):
    return {
        "trip_id": trip.trip_id,
        "rider_id": trip.rider_id,
        "driver_id": trip.driver_id,
        "status": trip.status.value,
        "fare": trip.fare,
        "events": [{"time": t, "event": e} for t, e in trip.events],
    }


# ---------- Rider endpoints ----------

@app.post("/riders")
def register_rider(req: RegisterRiderRequest):
    rider = service.register_rider(req.name)
    return {"rider_id": rider.rider_id, "name": rider.name}


@app.post("/rides")
def request_ride(req: RequestRideRequest):
    try:
        trip = service.request_ride(
            rider_id=req.rider_id,
            pickup=Location(req.pickup_lat, req.pickup_lng),
            drop=Location(req.drop_lat, req.drop_lng),
            vehicle_type=req.vehicle_type,
        )
        return trip_to_dict(trip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/rides/{trip_id}/cancel")
def cancel_ride(trip_id: str):
    try:
        trip = service.cancel_ride(trip_id, by="rider")
        return trip_to_dict(trip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/rides/{trip_id}")
def get_trip(trip_id: str):
    try:
        trip = service.get_trip_status(trip_id)
        return trip_to_dict(trip)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------- Driver endpoints ----------

@app.post("/drivers")
def register_driver(req: RegisterDriverRequest):
    driver = service.register_driver(req.name, Location(req.lat, req.lng), req.vehicle_type)
    return {"driver_id": driver.driver_id, "name": driver.name, "status": driver.status.value}


@app.post("/rides/{trip_id}/driver-arrived")
def driver_arrived(trip_id: str):
    try:
        trip = service.driver_arrived(trip_id)
        return trip_to_dict(trip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/rides/{trip_id}/start")
def start_trip(trip_id: str):
    try:
        trip = service.start_trip(trip_id)
        return trip_to_dict(trip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/rides/{trip_id}/end")
def end_trip(trip_id: str):
    try:
        trip = service.end_trip(trip_id)
        return trip_to_dict(trip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- Admin/ops endpoints ----------

@app.post("/admin/surge")
def set_surge(req: SurgeRequest):
    service.pricing.set_surge(req.multiplier)
    return {"surge_multiplier": req.multiplier}


@app.get("/drivers/{driver_id}")
def get_driver(driver_id: str):
    driver = service.store.get_driver(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return {
        "driver_id": driver.driver_id,
        "name": driver.name,
        "status": driver.status.value,
        "location": {"lat": driver.location.lat, "lng": driver.location.lng},
        "vehicle_type": driver.vehicle_type,
    }