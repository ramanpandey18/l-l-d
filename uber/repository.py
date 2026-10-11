"""
repository.py
InMemoryStore: data access layer for riders, drivers, and trips.
Acts as a stand-in for a database - service.py talks to this interface
only, so storage can later be swapped (e.g. Postgres + Redis) without
touching business logic.
"""

# import threading
# from typing import Optional
# from models import Rider, Driver, Trip


# class InMemoryStore:

#     def __init__(self):
#         self._lock = threading.RLock()
#         self.riders: dict[str, Rider] = {}
#         self.drivers: dict[str, Driver] = {}
#         self.trips: dict[str, Trip] = {}

#     # ---- Riders ----
#     def add_rider(self, rider: Rider):
#         with self._lock:
#             self.riders[rider.rider_id] = rider

#     def get_rider(self, rider_id: str) -> Optional[Rider]:
#         with self._lock:
#             return self.riders.get(rider_id)

#     # ---- Drivers ----
#     def add_driver(self, driver: Driver):
#         with self._lock:
#             self.drivers[driver.driver_id] = driver

#     def get_driver(self, driver_id: str) -> Optional[Driver]:
#         with self._lock:
#             return self.drivers.get(driver_id)

#     def get_all_drivers(self) -> dict:
#         with self._lock:
#             # return a shallow copy so callers can't mutate our internal dict structure
#             return dict(self.drivers)

#     # ---- Trips ----
#     def save_trip(self, trip: Trip):
#         with self._lock:
#             self.trips[trip.trip_id] = trip

#     def get_trip(self, trip_id: str) -> Optional[Trip]:
#         with self._lock:
#             return self.trips.get(trip_id)
        


import threading
from typing import Optional
from models import Rider, Driver, Trip

class InMemoryStore:
    
    def __init__(self):
        self._lock = threading.Lock()
        self.riders = dict[str, Rider] = {}
        self.drivers = dict[str, Driver] = {}
        self.trips = dict[str, Trip] = {}
    
    # ---- riders ---- #
    def add_rider(self, rider: Rider):
        with self._lock:
            self.riders[rider.rider_id] = rider
    
    def get_rider(self, rider_id: str) -> Optional[Rider]:
        with self._lock:
            return self.riders.get(rider_id)

    # --- drivers ---- #
    def add_driver(self, driver: Driver):
        self.drivers[driver.driver_id] = driver
    
    def get_drivers(self, driver_id: str) -> Optional[Driver]:
        with self._lock:
            self.drivers.get(driver_id)

    def get_all_drivers(self)-> dict:
        with self._lock:
            return dict(self.drivers)

    # ---- trips ---- #
    def save_trip(self, trip: Trip):
        with self._lock:
            self.trips[trip.trip_id] = trip

    def get_trip(self, trip_id: str) -> Optional[Trip]:
        with self._lock:
            return self.trips.get(trip_id)

