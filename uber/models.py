"""
models.py
Core data structures: Location, Rider, Driver, Trip, and status enums.
No business logic here — pure data.
"""

# import math
# import time
# from enum import Enum
# from dataclasses import dataclass, field
# from typing import Optional


# class DriverStatus(Enum):
#     OFFLINE = "OFFLINE"
#     AVAILABLE = "AVAILABLE"
#     EN_ROUTE = "EN_ROUTE"      # heading to pickup
#     ON_TRIP = "ON_TRIP"


# class TripStatus(Enum):
#     REQUESTED = "REQUESTED"
#     MATCHED = "MATCHED"
#     DRIVER_ARRIVED = "DRIVER_ARRIVED"
#     ONGOING = "ONGOING"
#     COMPLETED = "COMPLETED"
#     CANCELLED = "CANCELLED"
#     NO_DRIVERS_AVAILABLE = "NO_DRIVERS_AVAILABLE"


# @dataclass
# class Location:
#     lat: float
#     lng: float

#     def distance_km(self, other: "Location") -> float:
#         """Haversine formula - straight-line distance between two coordinates."""
#         R = 6371  # Earth radius in km
#         lat1, lon1, lat2, lon2 = map(math.radians, [self.lat, self.lng, other.lat, other.lng])
#         dlat, dlon = lat2 - lat1, lon2 - lon1
#         a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
#         return 2 * R * math.asin(math.sqrt(a))


# @dataclass
# class Rider:
#     rider_id: str
#     name: str
#     rating: float = 5.0


# @dataclass
# class Driver:
#     driver_id: str
#     name: str
#     location: Location
#     status: DriverStatus = DriverStatus.OFFLINE
#     rating: float = 5.0
#     vehicle_type: str = "SEDAN"  # SEDAN, SUV, MINI


# @dataclass
# class Trip:
#     trip_id: str
#     rider_id: str
#     pickup: Location
#     drop: Location
#     vehicle_type: str
#     status: TripStatus = TripStatus.REQUESTED
#     driver_id: Optional[str] = None
#     fare: Optional[float] = None
#     created_at: float = field(default_factory=time.time)
#     events: list = field(default_factory=list)  # audit trail

#     def log(self, event: str):
#         """Append a timestamped event - acts as an audit trail for the trip."""
#         self.events.append((time.time(), event))




import math
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

class DriverStatus(Enum):
    OFFLINE = "OFFLINE"
    AVAILABLE = "AVAILABLE"
    EN_ROUTE = "EN_ROUTE"
    ON_TRIP = "ON_TRIP"

class TripStatus(Enum):
    REQUESTED = "REQUESTED"
    MATCHED = "MATCHED"
    DRIVER_ARRIVED = "DRIVER_ARRIVED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_DRIVERS_AVAILABLE = "NO_DRIVERS_AVAILABLE"


@dataclass
class Location:
    lat: float
    lng: float

    def distance_km(self, other: "Location") -> float:
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [self.lat, self.lng, other.lat, other.lng])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 2 * R * math.asin(math.sqrt(a))


@dataclass
class Rider:
    rider_id: str
    name: str
    rating: float = 5.0

@dataclass
class Driver:
    driver_id: str
    name: str
    location: Location
    status: DriverStatus = DriverStatus.OFFLINE
    rating: float = 5.0
    vehicle_type: str = "SEDAN"

@dataclass
class Trip:
    trip_id: str
    rider_id: str
    pick_up: Location
    drop: Location
    vehicle_type: str
    status: DriverStatus = DriverStatus.REQUESTED
    driver_id: Optional[str] = None
    fare: Optional[float] = None
    created_at: float = field(default_factor = time.time)
    events: list = field(default_factory = list)

    def log(self, event):
        self.events.append(time.time(), event)
