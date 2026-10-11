"""
Same race scenario, but now against the REAL ParkingLot class (with self.lock)
to prove the fix works - run many times to rule out a single lucky pass.
"""
import threading
from parking_lot import VehicleSize, Vehicle, ParkingSpot, Floor, ParkingLot

successes = []

for run in range(20):
    lot = ParkingLot()
    floor = Floor(1)
    floor.spots.append(ParkingSpot("A1", VehicleSize.SMALL))  # only ONE spot
    lot.add_floor(floor)

    results = {}

    def attempt(name, plate, target_lot=lot):
        try:
            target_lot.park(Vehicle(VehicleSize.SMALL, "red", plate))
            results[name] = "SUCCESS"
        except ValueError:
            results[name] = "FAILED"

    t1 = threading.Thread(target=attempt, args=("A", "Car-A"))
    t2 = threading.Thread(target=attempt, args=("B", "Car-B"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    success_count = sum(1 for v in results.values() if v == "SUCCESS")
    successes.append(success_count == 1)

print(f"Runs with exactly one successful park: {sum(successes)} / {len(successes)}")
print(f"All runs correct: {all(successes)}")
