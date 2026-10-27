"""
Simple BookMyShow / Ticketmaster  (in-memory, thread-safe)

Browse: list_cities() -> list_events(city) -> search_shows(city, title)
Flow:  hold_seats()  ->  confirm()  (mock payment)  ->  cancel()
Rules: max 6 seats per booking, a hold lasts 5 minutes, a seat is never sold twice.

Concurrency idea (the one thing to explain):
  every Show has ONE lock. hold / confirm / cancel on that show run inside it,
  so "check seat is free, then take it" can never interleave between two users.
  Different shows have different locks, so they never block each other.

Expiry idea:
  no background thread. A HELD seat whose hold time has passed simply counts as free
  (checked whenever someone looks at it).
"""
    
import threading
import time
import uuid
from enum import Enum


class SeatStatus(Enum):
    AVAILABLE = "AVAILABLE"
    HELD = "HELD"
    BOOKED = "BOOKED"


class BookingStatus(Enum):
    PENDING = "PENDING"        # seats are held, waiting for payment
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"          # payment failed


class SeatUnavailableError(Exception):
    pass


class HoldExpiredError(Exception):
    pass


class PaymentFailedError(Exception):
    pass


class InvalidOperationError(Exception):
    pass


class Seat:
    def __init__(self, seat_id, price):
        self.id = seat_id
        self.price = price
        self.status = SeatStatus.AVAILABLE
        self.booking_id = None      # who holds / owns it
        self.hold_expiry = 0

    def is_free(self, now):
        # free if available, or held but the hold time is over
        return self.status == SeatStatus.AVAILABLE or (
            self.status == SeatStatus.HELD and self.hold_expiry <= now)


class Show:
    def __init__(self, show_id, title, city, seat_prices):
        """title = event name (movie/concert), seat_prices = {"A1": 300, "B1": 150, ...}"""
        self.id = show_id
        self.title = title
        self.city = city
        self.seats = {sid: Seat(sid, price) for sid, price in seat_prices.items()}
        self.lock = threading.Lock()


class Booking:
    def __init__(self, user, show_id, seat_ids, amount):
        self.id = uuid.uuid4().hex[:8]
        self.user = user
        self.show_id = show_id
        self.seat_ids = seat_ids
        self.amount = amount
        self.status = BookingStatus.PENDING


class BookingSystem:
    MAX_SEATS = 6
    HOLD_SECONDS = 300
    
    def __init__(self, payment=None, now=time.time):
        self.payment = payment or (lambda user, amount: True)      # function(user, amount) -> True/False  (mock gateway)
        self.now = now              # injectable clock, so tests can fast-forward time
        self.shows = {}
        self.bookings = {}

    def add_show(self, show_id, title, city, seat_prices):
        self.shows[show_id] = Show(show_id, title, city, seat_prices)

    # ---- browse / search -----------------------------------------------------
    def list_cities(self):
        return sorted({s.city for s in list(self.shows.values())})

    
    def list_events(self, city):
        """Event titles that are playing in a city."""
        return sorted({s.title for s in list(self.shows.values()) if s.city.lower() == city.lower()})

    def search_shows(self, city=None, title=None):
        """Filter by city and/or part of the event title (case-insensitive)."""
        result = []
        for s in list(self.shows.values()):
            if city and s.city.lower() != city.lower():
                continue
            if title and title.lower() not in s.title.lower():
                continue
            result.append(s)
        return sorted(result, key=lambda s: s.id)

    def available_seats(self, show_id):
        show, now = self.shows[show_id], self.now()
        with show.lock:
            return sorted(s.id for s in show.seats.values() if s.is_free(now))

    # ---- step 1: hold ------------------------------------------------------
    def hold_seats(self, user, show_id, seat_ids):
        if not seat_ids or len(set(seat_ids)) != len(seat_ids):
            raise ValueError("Pick at least one seat, no duplicates")
        if len(seat_ids) > self.MAX_SEATS:
            raise ValueError(f"Max {self.MAX_SEATS} seats per booking")
        
        show = self.shows[show_id]
        with show.lock:
            now = self.now()
            # 1) check ALL seats first ...
            taken = [sid for sid in seat_ids if not show.seats[sid].is_free(now)]
            if taken:
                raise SeatUnavailableError(f"Not available: {taken}")
            # 2) ... then take them all  (all-or-nothing)
            booking = Booking(user, show_id, seat_ids,
                              sum(show.seats[sid].price for sid in seat_ids))
            for sid in seat_ids:
                seat = show.seats[sid]
                seat.status = SeatStatus.HELD
                seat.booking_id = booking.id
                seat.hold_expiry = now + self.HOLD_SECONDS
            self.bookings[booking.id] = booking
            return booking

    # ---- step 2: pay + confirm -----------------------------------------------
    def confirm(self, booking_id):
        booking = self.bookings[booking_id]
        show = self.shows[booking.show_id]

        with show.lock:
            if booking.status != BookingStatus.PENDING:
                raise InvalidOperationError(f"Booking is {booking.status.value}")
            now = self.now()
            still_mine = all(
                show.seats[sid].booking_id == booking.id
                and show.seats[sid].status == SeatStatus.HELD
                and show.seats[sid].hold_expiry > now
                for sid in booking.seat_ids)
            if not still_mine:
                self._release(show, booking)
                booking.status = BookingStatus.EXPIRED
                raise HoldExpiredError("Hold expired, please select seats again")

            if not self.payment(booking.user, booking.amount):
                self._release(show, booking)
                booking.status = BookingStatus.FAILED
                raise PaymentFailedError("Payment failed")

            for sid in booking.seat_ids:
                show.seats[sid].status = SeatStatus.BOOKED
            booking.status = BookingStatus.CONFIRMED
            return booking

    # ---- step 3: cancel -------------------------------------------------------
    def cancel(self, booking_id):
        booking = self.bookings[booking_id]
        show = self.shows[booking.show_id]

        with show.lock:
            if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
                raise InvalidOperationError(f"Booking is {booking.status.value}")
            self._release(show, booking)
            booking.status = BookingStatus.CANCELLED   # (refund would go here)
            return booking

    def _release(self, show, booking):
        """Free the booking's seats. Only touches seats this booking still owns, so an
        old expired booking can never free a seat that someone else has taken since."""
        for sid in booking.seat_ids:
            seat = show.seats[sid]
            if seat.booking_id == booking.id:
                seat.status = SeatStatus.AVAILABLE
                seat.booking_id = None
