"""
service.py
RideService: core business logic. Orchestrates InMemoryStore (data),
MatchingStrategy (driver selection), and PricingEngine (fare).
Enforces valid trip state transitions.
"""

# import uuid
# from typing import Optional
# from models import Rider, Driver, Trip, Location, DriverStatus, TripStatus
# from repository import InMemoryStore
# from matching import MatchingStrategy
# from pricing import PricingEngine


# class RideService:

#     def __init__(self, store: InMemoryStore, matcher: MatchingStrategy, pricing: PricingEngine):
#         self.store = store
#         self.matcher = matcher
#         self.pricing = pricing
#         self._lock = __import__("threading").RLock()  # guards driver-assignment race

#     # ---------- Registration ----------

#     def register_rider(self, name: str) -> Rider:
#         rider = Rider(rider_id=str(uuid.uuid4())[:8], name=name)
#         self.store.add_rider(rider)
#         return rider

#     def register_driver(self, name: str, location: Location, vehicle_type: str = "SEDAN") -> Driver:
#         driver = Driver(
#             driver_id=str(uuid.uuid4())[:8],
#             name=name,
#             location=location,
#             vehicle_type=vehicle_type,
#             status=DriverStatus.AVAILABLE,
#         )
#         self.store.add_driver(driver)
#         return driver

#     # ---------- Ride lifecycle ----------

#     def request_ride(self, rider_id: str, pickup: Location, drop: Location, vehicle_type: str = "SEDAN") -> Trip:
#         if not self.store.get_rider(rider_id):
#             raise ValueError("Rider not found")
#         if vehicle_type not in PricingEngine.BASE_FARE:
#             raise ValueError(f"Invalid vehicle type: {vehicle_type}")

#         trip = Trip(
#             trip_id=str(uuid.uuid4())[:8],
#             rider_id=rider_id,
#             pickup=pickup,
#             drop=drop,
#             vehicle_type=vehicle_type,
#         )
#         trip.log("Ride requested")

#         # Lock guards against two ride requests grabbing the same driver
#         with self._lock:
#             driver = self.matcher.find_driver(pickup, vehicle_type, self.store.get_all_drivers())

#             if driver is None:
#                 trip.status = TripStatus.NO_DRIVERS_AVAILABLE
#                 trip.log("No drivers available")
#                 self.store.save_trip(trip)
#                 return trip

#             # Atomically claim the driver before releasing the lock
#             driver.status = DriverStatus.EN_ROUTE
#             trip.driver_id = driver.driver_id
#             trip.status = TripStatus.MATCHED
#             trip.log(f"Matched with driver {driver.driver_id} ({driver.name})")

#             distance = pickup.distance_km(drop)
#             eta_min = distance * 2.5  # naive: avg speed ~24 km/h in city traffic
#             trip.fare = self.pricing.estimate_fare(vehicle_type, distance, eta_min)

#         self.store.save_trip(trip)
#         return trip

#     def driver_arrived(self, trip_id: str) -> Trip:
#         trip = self._get_trip_or_raise(trip_id)
#         self._assert_status(trip, TripStatus.MATCHED)
#         trip.status = TripStatus.DRIVER_ARRIVED
#         trip.log("Driver arrived at pickup")
#         self.store.save_trip(trip)
#         return trip

#     def start_trip(self, trip_id: str) -> Trip:
#         trip = self._get_trip_or_raise(trip_id)
#         self._assert_status(trip, TripStatus.DRIVER_ARRIVED)
#         trip.status = TripStatus.ONGOING
#         driver = self.store.get_driver(trip.driver_id)
#         driver.status = DriverStatus.ON_TRIP
#         trip.log("Trip started")
#         self.store.save_trip(trip)
#         return trip

#     def end_trip(self, trip_id: str) -> Trip:
#         trip = self._get_trip_or_raise(trip_id)
#         self._assert_status(trip, TripStatus.ONGOING)
#         trip.status = TripStatus.COMPLETED
#         driver = self.store.get_driver(trip.driver_id)
#         driver.location = trip.drop   # driver is now physically at drop location
#         driver.status = DriverStatus.AVAILABLE
#         trip.log(f"Trip completed. Fare: {trip.fare}")
#         self.store.save_trip(trip)
#         return trip

#     def cancel_ride(self, trip_id: str, by: str = "rider") -> Trip:
#         trip = self._get_trip_or_raise(trip_id)
#         with self._lock:
#             if trip.status in (TripStatus.COMPLETED, TripStatus.CANCELLED, TripStatus.NO_DRIVERS_AVAILABLE):
#                 raise ValueError(f"Cannot cancel trip in status {trip.status}")
#             if trip.driver_id:
#                 driver = self.store.get_driver(trip.driver_id)
#                 driver.status = DriverStatus.AVAILABLE
#             trip.status = TripStatus.CANCELLED
#             trip.log(f"Trip cancelled by {by}")
#         self.store.save_trip(trip)
#         return trip

#     def get_trip_status(self, trip_id: str) -> Trip:
#         return self._get_trip_or_raise(trip_id)

#     # ---------- Helpers ----------

#     def _get_trip_or_raise(self, trip_id: str) -> Trip:
#         trip = self.store.get_trip(trip_id)
#         if not trip:
#             raise ValueError("Trip not found")
#         return trip

#     def _assert_status(self, trip: Trip, expected: TripStatus):
#         if trip.status != expected:
#             raise ValueError(f"Invalid state transition: trip is {trip.status}, expected {expected}")
        

import uuid
import threading
from typing import Optional
from models import Rider, Driver, Location, Trip, DriverStatus, TripStatus
from repository import InMemoryStore
from matching import MatchingStrategy
from pricing import PricingEngine

class RiderService:
    def __init__(self, store: InMemoryStore, matcher: MatchingStrategy, pricing: PricingEngine):
        self.store = store
        self.matcher = matcher
        self.pricing = pricing
        self._lock = threading.RLock()

    # ---------- Registration ----------

    def register_rider(self, name: str) -> Rider:
        rider = Rider(
            rider_id = str(uuid.uuid4() [:8]),
            name = name
        )
        self.store.add_rider(rider)
        return rider
    
    def register_driver(self, name: str, location: Location, vehicle_type: str = "SEDAN", ) -> Driver:
        driver = Driver(
            driver_id = str(uuid.uuid4() [:8]),
            name = name,
            location = location,
            vehicle_type = vehicle_type,
            status = DriverStatus.AVAILABLE
        )
        self.store.add_driver(driver)
        return driver

# ---------- Ride lifecycle ----------
    def request_ride(self, rider_id, pick_up: Location, drop: Location, vehicle_type: str = "SEDAN") -> Trip:
        rider = self.store.get_rider(rider_id)
        if not rider:
            raise ValueError("Rider not found!")
        if vehicle_type not in PricingEngine.BASE_FARE:
            raise ValueError(f"Invalid vehicle type {vehicle_type}")

        trip = Trip(
            trip_id = str(uuid.uuid4() [:8]),
            rider_id = rider_id,
            pick_up = pick_up,
            drop = drop,
            vehicle_type = vehicle_type
        )
        trip.log("Ride requested")

        with self._lock:
            driver = self.matcher.find_driver(pick_up, vehicle_type, self.store.get_all_drivers())

            if driver is None:
                trip.status = TripStatus.NO_DRIVERS_AVAILABLE
                trip.log("No Drivers Available")
                self.store.save_trip(trip)
                return trip

            driver.status = DriverStatus.EN_ROUTE
            trip.driver_id = driver.driver_id
            trip.status = TripStatus.MATCHED
            trip.log(f"Matched with driver {driver.driver_id} ({driver.name})")

            distance = pick_up.distance_km(drop)
            eta_min = distance * 2.5
            trip.fare = self.pricing.estimate_fare(vehicle_type, distance, eta_min)
        self.store.save_trip(trip)
        return trip
    
    def driver_arrived(self, trip_id: str) -> Trip:
        trip = self._get_trip_or_raise(trip_id)
        self._assert_status(trip, TripStatus.MATCHED)
        trip.status = TripStatus.DRIVER_ARRIVED
        trip.log("Driver arrived at pickup")
        self.store.save_trip(trip)
        return trip


    def start_trip(self, trip_id: str) -> Trip:
        trip = self._get_trip_or_raise(trip_id)
        self._assert_status(trip, TripStatus.DRIVER_ARRIVED)
        trip.status = TripStatus.ONGOING
        driver = self.store.get_drivers(trip.driver_id)
        driver.status = DriverStatus.ON_TRIP
        trip.log("Trip started")
        self.store.save_trip(trip)
        return trip

    def end_trip(self, trip_id: str) -> Trip:
        trip = self._get_trip_or_raise(trip_id)
        self._assert_status(trip, TripStatus.ONGOING)
        driver = self.store.get_drivers(trip.driver_id)
        driver.location = trip.drop
        driver.status = DriverStatus.AVAILABLE
        trip.log(f"Trip completed. Fare: {trip.fare}")
        self.store.save_trip(trip)
        return trip
    
    def cancel_ride(self, trip_id: str, by: str = "rider") -> Trip:
        trip = self._get_trip_or_raise(trip_id)
        with self._lock:
            if trip.status in (TripStatus.COMPLETED , TripStatus.CANCELLED , TripStatus.NO_DRIVERS_AVAILABLE):
                raise ValueError(f"Cannot cancel trip in status {trip.status}")
            if trip.driver_id:
                driver = self.store.get_drivers(trip.driver_id)
                driver.status = DriverStatus.AVAILABLE
            trip.status = TripStatus.CANCELLED
            trip.log(f"Trip cancelled by {by}")
        self.store.save_trip(trip)
        return trip

    def get_trip_status(self, trip_id: str) -> Trip:
        return self._get_trip_or_raise(trip_id)


# ---------- Helpers ----------

    def _get_trip_or_raise(self, trip_id: str) -> Trip:
        trip = self.store.get_trip(trip_id)
        if not trip:
            raise ValueError("Trip not found")
        return trip
    
    def _assert_status(self, trip: Trip, expected: TripStatus):
        if trip.status != expected:
            raise ValueError(f"Invalid state transition: trip is {trip.status}, expected {expected}") 
