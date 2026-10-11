import threading
import time
from datetime import datetime, timedelta

import pytest
from parking_lot import VehicleSize, Vehicle, ParkingSpot, Floor, Ticket, ParkingLot


# ---------- add_floor ----------

def test_add_floor_success():
    lot = ParkingLot()
    floor = Floor(1)

    lot.add_floor(floor)

    assert len(lot.floors) == 1
    assert lot.floors[0] is floor


def test_add_floor_wrong_type_raises():
    lot = ParkingLot()

    with pytest.raises(ValueError):
        lot.add_floor("not a floor")  # type: ignore


def test_add_floor_duplicate_number_raises():
    lot = ParkingLot()
    lot.add_floor(Floor(1))

    with pytest.raises(ValueError):
        lot.add_floor(Floor(1))


# ---------- _calculate_fee ----------

def test_calculate_fee_correct_rate_per_size():
    lot = ParkingLot()

    assert lot._calculate_fee(VehicleSize.SMALL, 2) == 2.0    # 1.0/hr * 2
    assert lot._calculate_fee(VehicleSize.MEDIUM, 2) == 4.0   # 2.0/hr * 2
    assert lot._calculate_fee(VehicleSize.LARGE, 2) == 8.0    # 4.0/hr * 2


def test_calculate_fee_fractional_hours_not_rounded_down():
    lot = ParkingLot()

    fee = lot._calculate_fee(VehicleSize.SMALL, 1.5)

    assert fee == 1.5  # not floored to 1.0


def test_calculate_fee_negative_duration_raises():
    lot = ParkingLot()

    with pytest.raises(ValueError):
        lot._calculate_fee(VehicleSize.SMALL, -1)


# ---------- park ----------

def _build_lot(spot_sizes_by_floor):
    """Helper: spot_sizes_by_floor = [[SMALL, MEDIUM], [LARGE]] etc."""
    lot = ParkingLot()
    for floor_num, sizes in enumerate(spot_sizes_by_floor, start=1):
        floor = Floor(floor_num)
        for i, size in enumerate(sizes):
            floor.spots.append(ParkingSpot(f"F{floor_num}-S{i}", size))
        lot.add_floor(floor)
    return lot


def test_park_success_returns_ticket():
    lot = _build_lot([[VehicleSize.MEDIUM]])
    vehicle = Vehicle(VehicleSize.SMALL, "red", "ABC-123")

    ticket = lot.park(vehicle)

    assert ticket.ticket_id is not None
    assert ticket.vehicle is vehicle
    assert ticket.spot.is_occupied is True
    assert ticket.ticket_id in lot.active_tickets


def test_park_picks_smallest_fitting_spot_not_first_found():
    # LARGE spot appears first in the list, but a MEDIUM spot also fits
    # a SMALL vehicle and should be preferred since it's the smaller fit.
    lot = _build_lot([[VehicleSize.LARGE, VehicleSize.MEDIUM]])
    vehicle = Vehicle(VehicleSize.SMALL, "blue", "XYZ-999")

    ticket = lot.park(vehicle)

    assert ticket.spot.size == VehicleSize.MEDIUM


def test_park_smaller_vehicle_can_use_larger_spot_if_needed():
    lot = _build_lot([[VehicleSize.LARGE]])  # only a LARGE spot exists
    vehicle = Vehicle(VehicleSize.SMALL, "green", "AAA-111")

    ticket = lot.park(vehicle)

    assert ticket.spot.size == VehicleSize.LARGE


def test_park_larger_vehicle_cannot_use_smaller_spot():
    lot = _build_lot([[VehicleSize.SMALL]])
    vehicle = Vehicle(VehicleSize.LARGE, "black", "BBB-222")

    with pytest.raises(ValueError):
        lot.park(vehicle)


def test_park_searches_across_multiple_floors():
    lot = _build_lot([[VehicleSize.SMALL], [VehicleSize.SMALL]])  # 2 floors, 1 spot each
    v1 = Vehicle(VehicleSize.SMALL, "red", "V1")
    v2 = Vehicle(VehicleSize.SMALL, "blue", "V2")

    t1 = lot.park(v1)
    t2 = lot.park(v2)

    assert t1.spot is not t2.spot  # got two different spots, across floors


def test_park_lot_full_raises():
    lot = _build_lot([[VehicleSize.SMALL]])
    lot.park(Vehicle(VehicleSize.SMALL, "red", "V1"))  # takes the only spot

    with pytest.raises(ValueError):
        lot.park(Vehicle(VehicleSize.SMALL, "blue", "V2"))


# ---------- unpark ----------

def test_unpark_success_returns_fee_and_frees_spot():
    lot = _build_lot([[VehicleSize.SMALL]])
    vehicle = Vehicle(VehicleSize.SMALL, "red", "V1")
    ticket = lot.park(vehicle)

    # simulate 2 hours having passed by backdating entry_time
    ticket.entry_time = datetime.now() - timedelta(hours=2)

    fee = lot.unpark(ticket.ticket_id)

    assert fee == 2.0  # SMALL rate ($1/hr) * 2 hours
    assert ticket.spot.is_occupied is False
    assert ticket.ticket_id not in lot.active_tickets


def test_unpark_frees_spot_for_reuse():
    lot = _build_lot([[VehicleSize.SMALL]])
    ticket1 = lot.park(Vehicle(VehicleSize.SMALL, "red", "V1"))
    lot.unpark(ticket1.ticket_id)

    # should be able to park a new vehicle in the now-freed spot
    ticket2 = lot.park(Vehicle(VehicleSize.SMALL, "blue", "V2"))

    assert ticket2.spot is ticket1.spot


def test_unpark_unknown_ticket_raises():
    lot = _build_lot([[VehicleSize.SMALL]])

    with pytest.raises(ValueError):
        lot.unpark("no-such-ticket-id")


def test_unpark_charges_different_rates_by_vehicle_size():
    lot = _build_lot([[VehicleSize.LARGE, VehicleSize.LARGE]])

    small_ticket = lot.park(Vehicle(VehicleSize.SMALL, "red", "V1"))
    large_ticket = lot.park(Vehicle(VehicleSize.LARGE, "blue", "V2"))

    small_ticket.entry_time = datetime.now() - timedelta(hours=1)
    large_ticket.entry_time = datetime.now() - timedelta(hours=1)

    small_fee = lot.unpark(small_ticket.ticket_id)
    large_fee = lot.unpark(large_ticket.ticket_id)

    assert small_fee == 1.0   # SMALL rate
    assert large_fee == 4.0   # LARGE rate


# ---------- Concurrency ----------

def test_concurrent_park_only_one_winner_for_last_spot():
    lot = _build_lot([[VehicleSize.SMALL]])  # only ONE spot exists

    results = {}

    def attempt(name, plate):
        try:
            lot.park(Vehicle(VehicleSize.SMALL, "red", plate))
            results[name] = "SUCCESS"
        except ValueError:
            results[name] = "FAILED"

    t1 = threading.Thread(target=attempt, args=("A", "V1"))
    t2 = threading.Thread(target=attempt, args=("B", "V2"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    success_count = sum(1 for v in results.values() if v == "SUCCESS")
    assert success_count == 1


def test_concurrent_park_consistent_across_many_runs():
    for _ in range(20):
        lot = _build_lot([[VehicleSize.SMALL]])

        results = {}

        def attempt(name, plate, target_lot=lot):
            try:
                target_lot.park(Vehicle(VehicleSize.SMALL, "red", plate))
                results[name] = "SUCCESS"
            except ValueError:
                results[name] = "FAILED"

        t1 = threading.Thread(target=attempt, args=("A", "V1"))
        t2 = threading.Thread(target=attempt, args=("B", "V2"))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        success_count = sum(1 for v in results.values() if v == "SUCCESS")
        assert success_count == 1