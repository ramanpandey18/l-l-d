import pytest

from elevator import *   # change "elevator" to your module's file name

UP, DOWN = Direction.UP, Direction.DOWN


def run(elevator, ticks):
    for _ in range(ticks):
        elevator.step()


def pending(elevator):
    return len(elevator.up_stops) + len(elevator.down_stops)


# ---------- adding requests ----------
@pytest.mark.parametrize("floor", [11, -1])   # above max, below min
def test_floor_out_of_range_is_rejected(floor):
    e = Elevator('A', 0, 10)
    with pytest.raises(ValueError):
        e.add_request(Request(floor))


def test_request_on_current_floor_is_ignored():
    e = Elevator('A', 0, 10, 4)
    e.add_request(Request(4))
    assert pending(e) == 0


def test_request_above_goes_to_up_heap():
    e = Elevator('A', 0, 10, 4)
    e.add_request(Request(7))
    assert len(e.up_stops) == 1
    assert len(e.down_stops) == 0


def test_request_below_goes_to_down_heap():
    e = Elevator('A', 0, 10, 4)
    e.add_request(Request(1))
    assert len(e.down_stops) == 1
    assert len(e.up_stops) == 0


def test_up_heap_returns_closest_floor_first():
    e = Elevator('A', 0, 10)
    for f in (6, 2, 4):
        e.add_request(Request(f))
    assert e.up_stops[0][0] == 2


def test_down_heap_returns_closest_floor_first():
    e = Elevator('A', 0, 10, 9)
    for f in (1, 5, 3):
        e.add_request(Request(f))
    assert -e.down_stops[0][0] == 5


# ---------- idle ----------
def test_new_elevator_is_idle():
    e = Elevator('A', 0, 10)
    assert e.state == State.IDLE


def test_step_with_no_requests_does_nothing():
    e = Elevator('A', 0, 10, 3)
    run(e, 5)
    assert (e.current_floor, e.state) == (3, State.IDLE)


# ---------- moving ----------
def test_moves_one_floor_per_step_going_up():
    e = Elevator('A', 0, 10)
    e.add_request(Request(5))
    e.step()
    assert (e.current_floor, e.state) == (1, State.MOVING_UP)


def test_moves_one_floor_per_step_going_down():
    e = Elevator('A', 0, 10, 8)
    e.add_request(Request(2))
    e.step()
    assert (e.current_floor, e.state) == (7, State.MOVING_DOWN)


def test_car_request_up_is_served_and_elevator_goes_idle():
    e = Elevator('A', 0, 10)
    e.add_request(Request(3))
    run(e, 3)
    assert (e.current_floor, e.state) == (3, State.IDLE)
    assert pending(e) == 0


def test_car_request_down_is_served_and_elevator_goes_idle():
    e = Elevator('A', 0, 10, 5)
    e.add_request(Request(2))
    run(e, 3)
    assert (e.current_floor, e.state) == (2, State.IDLE)
    assert pending(e) == 0


def test_stops_at_each_requested_floor_going_up():
    e = Elevator('A', 0, 10)
    e.add_request(Request(2))
    e.add_request(Request(4))
    run(e, 2)
    assert (e.current_floor, e.state) == (2, State.MOVING_UP)
    assert len(e.up_stops) == 1
    run(e, 2)
    assert (e.current_floor, e.state) == (4, State.IDLE)


def test_stops_at_each_requested_floor_going_down():
    e = Elevator('A', 0, 10, 9)
    e.add_request(Request(7))
    e.add_request(Request(3))
    run(e, 2)
    assert (e.current_floor, e.state) == (7, State.MOVING_DOWN)
    run(e, 4)
    assert (e.current_floor, e.state) == (3, State.IDLE)


# ---------- hall calls ----------
def test_up_hall_call_served_when_going_up():
    e = Elevator('A', 0, 10)
    e.add_request(Request(3, UP))
    run(e, 3)
    assert (e.current_floor, e.state) == (3, State.IDLE)
    assert pending(e) == 0


def test_down_hall_call_served_when_going_down():
    e = Elevator('A', 0, 10, 8)
    e.add_request(Request(3, DOWN))
    run(e, 5)
    assert (e.current_floor, e.state) == (3, State.IDLE)
    assert pending(e) == 0


def test_up_hall_call_is_served_on_the_way_to_a_farther_floor():
    e = Elevator('A', 0, 10)
    e.add_request(Request(3, UP))
    e.add_request(Request(6))
    run(e, 3)
    assert (e.current_floor, e.state) == (3, State.MOVING_UP)
    assert len(e.up_stops) == 1   # only floor 6 is left
    run(e, 3)
    assert (e.current_floor, e.state) == (6, State.IDLE)


# ---------- reversing ----------
def test_reverses_after_last_up_stop():
    e = Elevator('A', 0, 10, 5)
    e.add_request(Request(7))
    e.add_request(Request(2))
    run(e, 2)                                   # reaches 7
    assert (e.current_floor, e.state) == (7, State.MOVING_DOWN)
    run(e, 5)                                   # back down to 2
    assert (e.current_floor, e.state) == (2, State.IDLE)
    assert pending(e) == 0


def test_goes_up_first_when_idle_with_requests_both_sides():
    e = Elevator('A', 0, 10, 5)
    e.add_request(Request(2))
    e.add_request(Request(8))
    e.step()
    assert (e.current_floor, e.state) == (6, State.MOVING_UP)


def test_new_request_while_moving_is_picked_up():
    e = Elevator('A', 0, 10)
    e.add_request(Request(8))
    run(e, 2)                                   # at floor 2
    e.add_request(Request(5))
    run(e, 3)
    assert e.current_floor == 5
    assert len(e.up_stops) == 1                 # floor 8 still pending
    run(e, 3)
    assert (e.current_floor, e.state) == (8, State.IDLE)


# ---------- controller ----------
def test_no_elevators_hall_call_raises():
    c = ElevatorController()
    with pytest.raises(ValueError):
        c.request_elevator(3, UP)


def test_unknown_elevator_id_raises():
    c = ElevatorController()
    c.add_elevator(Elevator('A', 0, 10))
    with pytest.raises(ValueError):
        c.request_floor('Z', 3)


def test_hall_call_goes_to_first_elevator():
    c = ElevatorController()
    a, b = Elevator('A', 0, 10), Elevator('B', 0, 10)
    c.add_elevator(a)
    c.add_elevator(b)
    c.request_elevator(4, UP)
    assert pending(a) == 1
    assert pending(b) == 0


def test_car_request_goes_to_the_named_elevator():
    c = ElevatorController()
    a, b = Elevator('A', 0, 10), Elevator('B', 0, 10)
    c.add_elevator(a)
    c.add_elevator(b)
    c.request_floor('B', 6)
    assert pending(a) == 0
    assert pending(b) == 1


def test_out_of_range_floor_through_controller_raises():
    c = ElevatorController()
    c.add_elevator(Elevator('A', 0, 10))
    with pytest.raises(ValueError):
        c.request_floor('A', 99)
    with pytest.raises(ValueError):
        c.request_elevator(-3, DOWN)


def test_end_to_end_through_controller():
    c = ElevatorController()
    e = Elevator('A', 0, 10)
    c.add_elevator(e)
    c.request_elevator(2, UP)      # someone waiting on floor 2
    c.request_floor('A', 5)        # someone inside going to 5
    run(e, 5)
    assert (e.current_floor, e.state) == (5, State.IDLE)
    assert pending(e) == 0
