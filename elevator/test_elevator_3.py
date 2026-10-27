import random

import pytest

from elevator_3 import *

UP, DOWN = Direction.UP, Direction.DOWN


def run(e, ticks=30):
    for _ in range(ticks):
        e.step()


def test_down_call_served_at_turnaround():
    e = Elevator('A', 0, 10)
    e.add_request(Request(3, DOWN))
    run(e)
    # served at floor 3 while travelling UP: allowed because it is the last stop in this direction
    assert e.served == [(3, DOWN, UP)]


def test_down_call_not_served_while_passing():
    e = Elevator('A', 0, 10)
    e.add_request(Request(5, DOWN))
    e.add_request(Request(8))
    run(e)
    assert e.served == [(8, None, UP), (5, DOWN, DOWN)]  # collected on the way back


def test_up_call_not_served_while_passing_down():
    e = Elevator('A', 0, 10, 9)
    e.add_request(Request(5, UP))
    e.add_request(Request(1))
    run(e)
    assert e.served == [(1, None, DOWN), (5, UP, UP)]


def test_call_on_current_floor_while_moving_up():
    e = Elevator('A', 0, 10)
    e.add_request(Request(7))
    run(e, 3)
    e.add_request(Request(3, DOWN))
    run(e)
    assert e.served == [(7, None, UP), (3, DOWN, DOWN)]


def test_call_on_current_floor_while_idle_is_served_at_once():
    e = Elevator('A', 0, 10, 4)
    e.add_request(Request(4, UP))
    assert e.served == [(4, UP, None)]
    assert e.requests == []


def test_request_behind_elevator_reverses_without_idle():
    e = Elevator('A', 0, 10)
    e.add_request(Request(6))
    run(e, 4)                          # at floor 4, moving up
    e.add_request(Request(3, DOWN))    # behind us
    run(e, 2)                          # reach 6, serve it
    assert e.current_floor == 6
    assert e.state.value == "MOVING_DOWN"
    run(e)
    assert e.served == [(6, None, UP), (3, DOWN, DOWN)]


def test_two_requests_on_same_floor_do_not_crash():
    e = Elevator('A', 0, 10)
    e.add_request(Request(5))
    e.add_request(Request(5, UP))
    e.add_request(Request(5, DOWN))
    run(e)
    assert sorted(str(d) for _, d, _ in e.served) == sorted(str(d) for d in (None, UP, DOWN))


@pytest.mark.parametrize("seed", range(5))
def test_random_every_request_served_correctly(seed):
    random.seed(seed)
    for _ in range(400):
        e = Elevator('A', 0, 9, random.randint(0, 9))
        sent = set()
        for t in range(80):
            if t < 25 and random.random() < 0.5:
                f = random.randint(0, 9)
                d = random.choice([None, UP, DOWN])
                if (d == UP and f == 9) or (d == DOWN and f == 0):
                    d = None
                e.add_request(Request(f, d))
                sent.add((f, d))
            before = len(e.served)
            e.step()
            assert 0 <= e.current_floor <= 9
            for floor, d, travel in e.served[before:]:
                assert floor == e.current_floor
                if d is not None and travel is not None and d != travel:
                    # opposite-direction call: only OK if nothing is left ahead (we reverse here)
                    ahead = [r for r in e.requests
                             if (r.floor > floor if travel == UP else r.floor < floor)]
                    assert ahead == []
        served = {(f, d) for f, d, _ in e.served}
        assert sent <= served
        assert e.requests == []
        assert e.state.value == "IDLE"