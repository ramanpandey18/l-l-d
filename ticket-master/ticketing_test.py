from ticketing import BookingSystem, BookingStatus

system = BookingSystem()

system.add_show(
    "S1",
    "Interstellar",
    "Patna",
    {"A1": 300, "A2": 300, "B1": 200},
)

print("Available seats:", system.available_seats("S1"))

# 1. Hold seats
booking = system.hold_seats("user1", "S1", ["A1", "A2"])

print("Booking status:", booking.status)
print("Amount:", booking.amount)
print("Available after hold:", system.available_seats("S1"))

assert booking.status == BookingStatus.PENDING
assert "A1" not in system.available_seats("S1")

# 2. Confirm booking
system.confirm(booking.id)

print("After confirmation:", booking.status)
print("Available after confirmation:", system.available_seats("S1"))

assert booking.status == BookingStatus.CONFIRMED
assert "A1" not in system.available_seats("S1")

# 3. Hold and cancel another seat
booking2 = system.hold_seats("user2", "S1", ["B1"])
system.cancel(booking2.id)

print("After cancellation:", booking2.status)
print("Available after cancellation:", system.available_seats("S1"))

assert booking2.status == BookingStatus.CANCELLED
assert "B1" in system.available_seats("S1")

print("PASS: Booking flow works correctly.")
