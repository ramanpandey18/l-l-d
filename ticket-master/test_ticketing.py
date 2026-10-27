"""Run:  pytest -v"""
import random
import threading
import time

import pytest

from ticketing import (
    BookingStatus, BookingSystem, HoldExpiredError, InvalidOperationError,
    PaymentFailedError, Seat, SeatUnavailableError,
)


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def system(clock):
    s = BookingSystem(now=clock)
    s.add_show("show1", "Dune", "Patna", {"A1": 300, "A2": 300, "A3": 300, "B1": 150, "B2": 150})
    return s


def run_together(functions):
    """Start all functions at the same moment, return list of ('ok', result) / ('error', exc)."""
    barrier = threading.Barrier(len(functions))
    results = [None] * len(functions)

    def runner(i, fn):
        barrier.wait()
        try:
            results[i] = ("ok", fn())
        except Exception as e:
            results[i] = ("error", e)

    threads = [threading.Thread(target=runner, args=(i, f)) for i, f in enumerate(functions)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(10)
    assert not any(t.is_alive() for t in threads), "deadlock!"
    return results


# ------------------------------ browse / search -------------------------------
def test_city_and_event_search(system):
    system.add_show("show2", "Dune", "Delhi", {"A1": 300})
    system.add_show("show3", "Rock Night", "Delhi", {"A1": 999})

    assert system.list_cities() == ["Delhi", "Patna"]
    assert system.list_events("Patna") == ["Dune"]
    assert system.list_events("delhi") == ["Dune", "Rock Night"]      # case-insensitive
    assert system.list_events("Mumbai") == []

    assert [s.id for s in system.search_shows(city="Delhi")] == ["show2", "show3"]
    assert [s.id for s in system.search_shows(title="dune")] == ["show1", "show2"]
    assert [s.id for s in system.search_shows(city="Delhi", title="dune")] == ["show2"]


# ------------------------------ basic flow ---------------------------------
def test_hold_confirm_flow(system):
    booking = system.hold_seats("alice", "show1", ["A1", "B1"])
    assert booking.status == BookingStatus.PENDING
    assert booking.amount == 450
    assert "A1" not in system.available_seats("show1")      # held

    system.confirm(booking.id)
    assert booking.status == BookingStatus.CONFIRMED
    assert system.shows["show1"].seats["A1"].status.value == "BOOKED"


def test_held_seat_blocks_other_user(system):
    system.hold_seats("alice", "show1", ["A1"])
    with pytest.raises(SeatUnavailableError):
        system.hold_seats("bob", "show1", ["A1"])


def test_multi_seat_is_all_or_nothing(system):
    system.hold_seats("alice", "show1", ["A2"])
    with pytest.raises(SeatUnavailableError):
        system.hold_seats("bob", "show1", ["A1", "A2"])
    assert "A1" in system.available_seats("show1")           # A1 was not taken by the failed try


def test_validation(system):
    with pytest.raises(ValueError):
        system.hold_seats("alice", "show1", [])
    with pytest.raises(ValueError):
        system.hold_seats("alice", "show1", ["A1", "A1"])
    system.MAX_SEATS = 2
    with pytest.raises(ValueError):
        system.hold_seats("alice", "show1", ["A1", "A2", "A3"])


# ------------------------------ expiry --------------------------------------
def test_expired_hold_frees_seat(system, clock):
    system.hold_seats("alice", "show1", ["A1"])
    clock.t += 301                                            # 5 minutes pass
    assert "A1" in system.available_seats("show1")
    system.hold_seats("bob", "show1", ["A1"])                 # bob can take it


def test_confirm_after_expiry_fails(system, clock):
    booking = system.hold_seats("alice", "show1", ["A1"])
    clock.t += 301
    with pytest.raises(HoldExpiredError):
        system.confirm(booking.id)
    assert booking.status == BookingStatus.EXPIRED


def test_old_booking_cannot_free_seat_now_owned_by_someone_else(system, clock):
    old = system.hold_seats("alice", "show1", ["A1"])
    clock.t += 301
    new = system.hold_seats("bob", "show1", ["A1"])           # bob reuses the lapsed seat
    with pytest.raises(HoldExpiredError):
        system.confirm(old.id)                                # alice is too late
    assert system.shows["show1"].seats["A1"].booking_id == new.id   # bob's seat untouched
    system.confirm(new.id)


# ------------------------------ payment & cancel ----------------------------
def test_payment_failure_releases_seats(clock):
    system = BookingSystem(payment=lambda user, amount: False, now=clock)
    system.add_show("s", "Dune", "Patna", {"A1": 100})
    booking = system.hold_seats("alice", "s", ["A1"])
    with pytest.raises(PaymentFailedError):
        system.confirm(booking.id)
    assert booking.status == BookingStatus.FAILED
    assert system.available_seats("s") == ["A1"]


def test_cancel_releases_seats_and_cannot_cancel_twice(system):
    booking = system.hold_seats("alice", "show1", ["A1"])
    system.confirm(booking.id)
    system.cancel(booking.id)
    assert booking.status == BookingStatus.CANCELLED
    assert "A1" in system.available_seats("show1")
    with pytest.raises(InvalidOperationError):
        system.cancel(booking.id)


# ------------------------------ concurrency ---------------------------------
@pytest.fixture
def slow_seat_check(monkeypatch):
    """Makes the 'is the seat free?' check slow, so a missing lock would fail the tests."""
    original = Seat.is_free

    def slow(self, now):
        result = original(self, now)
        time.sleep(0.0005)
        return result

    monkeypatch.setattr(Seat, "is_free", slow)


def test_same_seat_only_one_winner(system, slow_seat_check):
    results = run_together([lambda u=u: system.hold_seats(f"user{u}", "show1", ["A1"])
                            for u in range(50)])
    winners = [r for kind, r in results if kind == "ok"]
    losers = [r for kind, r in results if kind == "error"]
    assert len(winners) == 1
    assert all(isinstance(e, SeatUnavailableError) for e in losers)


def test_double_click_confirm_charges_once(clock):
    charges = []
    system = BookingSystem(payment=lambda user, amount: charges.append(amount) or True, now=clock)
    system.add_show("s", "Dune", "Patna", {"A1": 100})
    booking = system.hold_seats("alice", "s", ["A1"])

    results = run_together([lambda: system.confirm(booking.id)] * 10)
    assert len([r for kind, r in results if kind == "ok"]) == 1
    assert len(charges) == 1                                  # money taken only once


def test_flash_sale_no_seat_sold_twice(clock):
    system = BookingSystem(now=clock)
    seats = [f"S{i}" for i in range(20)]
    system.add_show("s", "Concert", "Patna", {sid: 100 for sid in seats})
    rng = random.Random(1)

    def buy(user, seat_id):
        def run():
            booking = system.hold_seats(user, "s", [seat_id])
            return system.confirm(booking.id)
        return run

    results = run_together([buy(f"user{i}", rng.choice(seats)) for i in range(100)])

    confirmed = [r for kind, r in results if kind == "ok"]
    sold_seats = [sid for b in confirmed for sid in b.seat_ids]
    assert len(sold_seats) == len(set(sold_seats))            # no seat sold twice
    booked = [s for s in system.shows["s"].seats.values() if s.status.value == "BOOKED"]
    assert len(booked) == len(sold_seats)
