"""
library.py
Demo/test runner for the ride-hailing system.
Run: python library.py
"""

from models import Location, Trip
from repository import InMemoryStore
from matching import MatchingStrategy
from pricing import PricingEngine
from service import RideService


def print_trip(trip: Trip):
    print(f"\nTrip {trip.trip_id} | Status: {trip.status.value} | "
          f"Driver: {trip.driver_id} | Fare: {trip.fare}")
    for _, event in trip.events:
        print(f"   - {event}")


def setup_service() -> RideService:
    store = InMemoryStore()
    matcher = MatchingStrategy(max_radius_km=10)
    pricing = PricingEngine()
    return RideService(store, matcher, pricing)


def flow_happy_path(service: RideService):
    print("\n===== FLOW 1: Happy Path =====")
    rider = service.register_rider("Alice")
    service.register_driver("Bob", Location(12.9716, 77.5946), "SEDAN")
    service.register_driver("Carl", Location(12.9352, 77.6245), "SEDAN")

    pickup = Location(12.9352, 77.6245)
    drop = Location(12.9783, 77.6408)

    trip = service.request_ride(rider.rider_id, pickup, drop, vehicle_type="SEDAN")
    print_trip(trip)

    trip = service.driver_arrived(trip.trip_id)
    trip = service.start_trip(trip.trip_id)
    trip = service.end_trip(trip.trip_id)
    print_trip(trip)

    driver = service.store.get_driver(trip.driver_id)
    print(f"\nDriver {driver.driver_id} status after trip: {driver.status.value}")
    return service, rider


def flow_no_drivers(service: RideService, rider):
    print("\n===== FLOW 2: No Drivers Available =====")
    # MINI requested but no MINI registered
    trip = service.request_ride(rider.rider_id, Location(0, 0), Location(1, 1), vehicle_type="MINI")
    print_trip(trip)
    return trip


def flow_cancellation(service: RideService, rider):
    print("\n===== FLOW 3: Cancellation =====")
    driver = service.register_driver("Dan", Location(12.9352, 77.6245), "SUV")

    trip = service.request_ride(rider.rider_id, Location(12.9352, 77.6245), Location(12.9783, 77.6408), vehicle_type="SUV")
    print_trip(trip)

    trip = service.cancel_ride(trip.trip_id, by="rider")
    print_trip(trip)

    refreshed_driver = service.store.get_driver(driver.driver_id)
    print(f"\nDriver {driver.driver_id} status after cancel: {refreshed_driver.status.value}")


def flow_invalid_transition(service: RideService, no_driver_trip):
    print("\n===== FLOW 4: Invalid State Transition =====")
    try:
        service.start_trip(no_driver_trip.trip_id)
    except ValueError as e:
        print(f"Expected error: {e}")


def flow_surge_pricing(service: RideService, rider):
    print("\n===== FLOW 5: Surge Pricing =====")
    service.pricing.set_surge(1.8)
    service.register_driver("Eve", Location(12.9352, 77.6245), "SEDAN")

    trip = service.request_ride(rider.rider_id, Location(12.9352, 77.6245), Location(12.9783, 77.6408), vehicle_type="SEDAN")
    print_trip(trip)
    print(f"\n(Surge multiplier 1.8x applied to fare)")


if __name__ == "__main__":
    service = setup_service()
    service, rider = flow_happy_path(service)
    no_driver_trip = flow_no_drivers(service, rider)
    flow_cancellation(service, rider)
    flow_invalid_transition(service, no_driver_trip)
    flow_surge_pricing(service, rider)