"""
pricing.py
PricingEngine: calculates fare estimates.
Implemented as a strategy so pricing rules can be swapped/extended
(e.g. city-specific pricing, promo discounts) without touching service.py.
"""

# import threading


# class PricingEngine:
#     # Per-vehicle-type pricing config — could be loaded from DB/config in real system
#     BASE_FARE = {"MINI": 30, "SEDAN": 50, "SUV": 80}
#     PER_KM = {"MINI": 8, "SEDAN": 12, "SUV": 18}
#     PER_MIN = {"MINI": 1, "SEDAN": 1.5, "SUV": 2}

#     def __init__(self):
#         self._lock = threading.Lock()
#         self._surge_multiplier = 1.0

#     def set_surge(self, multiplier: float):
#         """In a real system, this would be computed periodically per geo-zone
#         based on demand/supply ratio. Exposed here for manual testing."""
#         with self._lock:
#             self._surge_multiplier = multiplier

#     def estimate_fare(self, vehicle_type: str, distance_km: float, eta_min: float) -> float:
#         base = self.BASE_FARE[vehicle_type]
#         dist_cost = distance_km * self.PER_KM[vehicle_type]
#         time_cost = eta_min * self.PER_MIN[vehicle_type]

#         with self._lock:
#             surge = self._surge_multiplier

#         fare = (base + dist_cost + time_cost) * surge
#         return round(fare, 2)
    
import threading

class PricingEngine:

    BASE_FARE = {"MINI": 30, "SEDAN": 50, "SUV": 80}
    PER_KM = {"MINI": 8, "SEDAN": 12, "SUV": 18}
    PER_MIN = {"MINI": 1, "SEDAN": 1.5, "SUV": 2}

    def __init__(self):
        self._lock = threading.Lock()
        self._surge_multiplier = 1

    def set_surge(self, multiplier: float):
        with self._lock:
            self._surge_multiplier = multiplier
    
    def estimate_fare(self, vehicle_type: str, distance_km: float, eta_min: float) -> float:
        base = self.BASE_FARE[vehicle_type]
        dist_cost = self.PER_KM[vehicle_type] * distance_km
        time_cost = self.PER_MIN[vehicle_type] * eta_min

        with self._lock:
            surge = self._surge_multiplier

        fare = (base + dist_cost + time_cost) * surge
        return (fare, 2)
    