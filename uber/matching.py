"""
matching.py
MatchingStrategy: finds the best available driver for a ride request.
Current implementation: nearest available driver of the requested vehicle
type, within a max radius. Linear scan - O(n) over all drivers.

For scale, this would be replaced with a geo-indexed lookup
(geohash / quadtree / Redis GEO commands) so we only scan drivers
in nearby grid cells instead of all drivers globally.
"""

# from typing import Optional
# from models import Driver, DriverStatus, Location


# class MatchingStrategy:

#     def __init__(self, max_radius_km: float = 5.0):
#         self.max_radius_km = max_radius_km

#     def find_driver(self, pickup: Location, vehicle_type: str, drivers: dict) -> Optional[Driver]:
#         """
#         drivers: dict[driver_id -> Driver]
#         Returns the nearest eligible driver, or None if none found.
#         """
#         candidates = []

#         for driver in drivers.values():
#             if driver.status != DriverStatus.AVAILABLE:
#                 continue
#             if driver.vehicle_type != vehicle_type:
#                 continue

#             dist = driver.location.distance_km(pickup)
#             if dist <= self.max_radius_km:
#                 candidates.append((dist, driver))

#         if not candidates:
#             return None

#         candidates.sort(key=lambda x: x[0])
#         return candidates[0][1]
    

from typing import Optional
from models import Driver, DriverStatus, Location

class MatchingStrategy:

    def __init__(self, max_radius_km: float = 5.0):
        self.max_radius_km = max_radius_km

    def find_driver(self, pick_up: Location, vehicle_type: str, drivers: dict) -> Optional[Driver]:
        candidates = []

        for driver in drivers.values():
            if driver.status != DriverStatus.AVAILABLE:
                continue
            if driver.vehicle_type != vehicle_type:
                continue

            dist = driver.location.distance_km(pick_up)
            if dist <= self.max_radius_km:
                candidates.append(dist, driver)
        
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0])
        
        return candidates[0][1]
    