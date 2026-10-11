"""
Two threads race to park in a lot with exactly ONE spot left.
Without a lock, both can see the spot as "available" before either one
marks it occupied - resulting in two vehicles being issued a ticket for
the SAME physical spot.

A tiny artificial delay is inserted between "find a spot" and "mark it
occupied" to reliably widen the race window.
"""
import threading
import time
import uuid
from datetime import datetime
from typing import List


class UnsafeParkingLot:
    """Same park() logic as ParkingLot, but WITHOUT a lock, and with an
    artificial delay inserted between finding a spot and claiming it."""

    def __init__(self, spots):
        self.spots = spots  # list of simple dicts: {"id": ..., "occupied": False}
        self.tickets = {}

    def park_unsafe(self, plate: str):
        available = [s for s in self.spots if not s["occupied"]]
        if not available:
            raise ValueError(f"{plate}: lot full")

        best_spot = available[0]

        time.sleep(0.01)  # <-- artificial gap between "find" and "claim"

        best_spot["occupied"] = True
        ticket_id = str(uuid.uuid4())
        self.tickets[ticket_id] = (plate, best_spot["id"])
        print(f"{plate} parked in spot {best_spot['id']} (ticket {ticket_id[:8]})")


lot = UnsafeParkingLot(spots=[{"id": "A1", "occupied": False}])  # only ONE spot
results = {}

def try_park(plate):
    try:
        lot.park_unsafe(plate)
        results[plate] = "SUCCESS"
    except ValueError as e:
        results[plate] = f"FAILED: {e}"

t1 = threading.Thread(target=try_park, args=("Car-A",))
t2 = threading.Thread(target=try_park, args=("Car-B",))
t1.start()
t2.start()
t1.join()
t2.join()

print("\n--- Results ---")
for name, outcome in results.items():
    print(f"{name}: {outcome}")

success_count = sum(1 for v in results.values() if v == "SUCCESS")
print(f"\nNumber of cars that think they parked: {success_count}")
if success_count > 1:
    print("BUG CONFIRMED: two vehicles were both issued tickets for the same single spot!")
