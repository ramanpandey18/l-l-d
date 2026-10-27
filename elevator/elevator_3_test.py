import time
from elevator_3 import Elevator, Request, State

e = Elevator("A", 0, 10, current_floor=0)
e.add_request(Request(3))

print("Initial floor:", e.current_floor)
e.start(tick_seconds=0.5)

try:
    time.sleep(2)

    with e.lock:
        print("Current floor:", e.current_floor)
        print("State:", e.state)
        print("Served:", e.served)

        assert e.current_floor == 3
        assert e.state == State.IDLE
        assert len(e.served) == 1

    print("PASS")
finally:
    e.stop()
