import unittest
from elevator import *   # change "elevator_4" to your module's file name

UP, DOWN = Direction.UP, Direction.DOWN


def run(elevator, ticks):
    for _ in range(ticks):
        elevator.step()


def pending(elevator):
    return len(elevator.up_stops) + len(elevator.down_stops)


class ElevatorTests(unittest.TestCase):
    # ---------- adding requests ----------
    def test_floor_above_max_is_rejected(self):
        e = Elevator('A', 0, 10)
        with self.assertRaises(ValueError):
            e.add_request(Request(11))

    def test_floor_below_min_is_rejected(self):
        e = Elevator('A', 0, 10)
        with self.assertRaises(ValueError):
            e.add_request(Request(-1))

    def test_request_on_current_floor_is_ignored(self):
        e = Elevator('A', 0, 10, 4)
        e.add_request(Request(4))
        self.assertEqual(pending(e), 0)

    def test_request_above_goes_to_up_heap(self):
        e = Elevator('A', 0, 10, 4)
        e.add_request(Request(7))
        self.assertEqual(len(e.up_stops), 1)
        self.assertEqual(len(e.down_stops), 0)

    def test_request_below_goes_to_down_heap(self):
        e = Elevator('A', 0, 10, 4)
        e.add_request(Request(1))
        self.assertEqual(len(e.down_stops), 1)
        self.assertEqual(len(e.up_stops), 0)

    def test_up_heap_returns_closest_floor_first(self):
        e = Elevator('A', 0, 10)
        for f in (6, 2, 4):
            e.add_request(Request(f))
        self.assertEqual(e.up_stops[0][0], 2)

    def test_down_heap_returns_closest_floor_first(self):
        e = Elevator('A', 0, 10, 9)
        for f in (1, 5, 3):
            e.add_request(Request(f))
        self.assertEqual(-e.down_stops[0][0], 5)

    # ---------- idle ----------
    def test_new_elevator_is_idle(self):
        e = Elevator('A', 0, 10)
        self.assertEqual(e.state, State.IDLE)

    def test_step_with_no_requests_does_nothing(self):
        e = Elevator('A', 0, 10, 3)
        run(e, 5)
        self.assertEqual((e.current_floor, e.state), (3, State.IDLE))

    # ---------- moving ----------
    def test_moves_one_floor_per_step_going_up(self):
        e = Elevator('A', 0, 10)
        e.add_request(Request(5))
        e.step()
        self.assertEqual((e.current_floor, e.state), (1, State.MOVING_UP))

    def test_moves_one_floor_per_step_going_down(self):
        e = Elevator('A', 0, 10, 8)
        e.add_request(Request(2))
        e.step()
        self.assertEqual((e.current_floor, e.state), (7, State.MOVING_DOWN))

    def test_car_request_up_is_served_and_elevator_goes_idle(self):
        e = Elevator('A', 0, 10)
        e.add_request(Request(3))
        run(e, 3)
        self.assertEqual((e.current_floor, e.state), (3, State.IDLE))
        self.assertEqual(pending(e), 0)

    def test_car_request_down_is_served_and_elevator_goes_idle(self):
        e = Elevator('A', 0, 10, 5)
        e.add_request(Request(2))
        run(e, 3)
        self.assertEqual((e.current_floor, e.state), (2, State.IDLE))
        self.assertEqual(pending(e), 0)

    def test_stops_at_each_requested_floor_going_up(self):
        e = Elevator('A', 0, 10)
        e.add_request(Request(2))
        e.add_request(Request(4))
        run(e, 2)
        self.assertEqual((e.current_floor, e.state), (2, State.MOVING_UP))
        self.assertEqual(len(e.up_stops), 1)
        run(e, 2)
        self.assertEqual((e.current_floor, e.state), (4, State.IDLE))

    def test_stops_at_each_requested_floor_going_down(self):
        e = Elevator('A', 0, 10, 9)
        e.add_request(Request(7))
        e.add_request(Request(3))
        run(e, 2)
        self.assertEqual((e.current_floor, e.state), (7, State.MOVING_DOWN))
        run(e, 4)
        self.assertEqual((e.current_floor, e.state), (3, State.IDLE))

    # ---------- hall calls ----------
    def test_up_hall_call_served_when_going_up(self):
        e = Elevator('A', 0, 10)
        e.add_request(Request(3, UP))
        run(e, 3)
        self.assertEqual((e.current_floor, e.state), (3, State.IDLE))
        self.assertEqual(pending(e), 0)

    def test_down_hall_call_served_when_going_down(self):
        e = Elevator('A', 0, 10, 8)
        e.add_request(Request(3, DOWN))
        run(e, 5)
        self.assertEqual((e.current_floor, e.state), (3, State.IDLE))
        self.assertEqual(pending(e), 0)

    def test_up_hall_call_is_served_on_the_way_to_a_farther_floor(self):
        e = Elevator('A', 0, 10)
        e.add_request(Request(3, UP))
        e.add_request(Request(6))
        run(e, 3)
        self.assertEqual((e.current_floor, e.state), (3, State.MOVING_UP))
        self.assertEqual(len(e.up_stops), 1)   # only floor 6 is left
        run(e, 3)
        self.assertEqual((e.current_floor, e.state), (6, State.IDLE))

    # ---------- reversing ----------
    def test_reverses_after_last_up_stop(self):
        e = Elevator('A', 0, 10, 5)
        e.add_request(Request(7))
        e.add_request(Request(2))
        run(e, 2)                                   # reaches 7
        self.assertEqual((e.current_floor, e.state), (7, State.MOVING_DOWN))
        run(e, 5)                                   # back down to 2
        self.assertEqual((e.current_floor, e.state), (2, State.IDLE))
        self.assertEqual(pending(e), 0)

    def test_goes_up_first_when_idle_with_requests_both_sides(self):
        e = Elevator('A', 0, 10, 5)
        e.add_request(Request(2))
        e.add_request(Request(8))
        e.step()
        self.assertEqual((e.current_floor, e.state), (6, State.MOVING_UP))

    def test_new_request_while_moving_is_picked_up(self):
        e = Elevator('A', 0, 10)
        e.add_request(Request(8))
        run(e, 2)                                   # at floor 2
        e.add_request(Request(5))
        run(e, 3)
        self.assertEqual(e.current_floor, 5)
        self.assertEqual(len(e.up_stops), 1)        # floor 8 still pending
        run(e, 3)
        self.assertEqual((e.current_floor, e.state), (8, State.IDLE))


class ControllerTests(unittest.TestCase):
    def test_no_elevators_hall_call_raises(self):
        c = ElevatorController()
        with self.assertRaises(ValueError):
            c.request_elevator(3, UP)

    def test_unknown_elevator_id_raises(self):
        c = ElevatorController()
        c.add_elevator(Elevator('A', 0, 10))
        with self.assertRaises(ValueError):
            c.request_floor('Z', 3)

    def test_hall_call_goes_to_first_elevator(self):
        c = ElevatorController()
        a, b = Elevator('A', 0, 10), Elevator('B', 0, 10)
        c.add_elevator(a)
        c.add_elevator(b)
        c.request_elevator(4, UP)
        self.assertEqual(pending(a), 1)
        self.assertEqual(pending(b), 0)

    def test_car_request_goes_to_the_named_elevator(self):
        c = ElevatorController()
        a, b = Elevator('A', 0, 10), Elevator('B', 0, 10)
        c.add_elevator(a)
        c.add_elevator(b)
        c.request_floor('B', 6)
        self.assertEqual(pending(a), 0)
        self.assertEqual(pending(b), 1)

    def test_out_of_range_floor_through_controller_raises(self):
        c = ElevatorController()
        c.add_elevator(Elevator('A', 0, 10))
        with self.assertRaises(ValueError):
            c.request_floor('A', 99)
        with self.assertRaises(ValueError):
            c.request_elevator(-3, DOWN)

    def test_end_to_end_through_controller(self):
        c = ElevatorController()
        e = Elevator('A', 0, 10)
        c.add_elevator(e)
        c.request_elevator(2, UP)      # someone waiting on floor 2
        c.request_floor('A', 5)        # someone inside going to 5
        run(e, 5)
        self.assertEqual((e.current_floor, e.state), (5, State.IDLE))
        self.assertEqual(pending(e), 0)


if __name__ == "__main__":
    unittest.main()
