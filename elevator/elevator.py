from typing import Optional, List
from enum import Enum
import heapq


class Direction(Enum):
    UP = "UP"
    DOWN = "DOWN"


class ElevatorState(Enum):
    IDLE = "IDLE"
    MOVING_UP = "MOVING_UP"
    MOVING_DOWN = "MOVING_DOWN"


class Request:
    """A single request: either a hall call (has a direction, made from
    outside the elevator) or a car request (no direction, made by someone
    already inside, pressing a destination floor)."""
    def __init__(self, floor: int, direction: Optional[Direction] = None):
        self.floor = floor
        self.direction = direction  # None for car requests


class Elevator:
    def __init__(self, elevator_id: str, min_floor: int, max_floor: int, current_floor: int = 0):
        self.elevator_id = elevator_id
        self.min_floor = min_floor
        self.max_floor = max_floor
        self.current_floor = current_floor
        self.state: ElevatorState = ElevatorState.IDLE

        # min-heap: pending floors ABOVE current position, closest first
        self.up_stops: List[int] = []
        # max-heap (via negation): pending floors BELOW current position, closest first
        self.down_stops: List[int] = []

    def add_request(self, request: Request) -> None:
        if request.floor < self.min_floor or request.floor > self.max_floor:
            raise ValueError("Floor out of range.")

        if request.floor == self.current_floor:
            return
        if request.floor > self.current_floor:
            heapq.heappush(self.up_stops, (request.floor, request))
        else:
            heapq.heappush(self.down_stops, (-request.floor, request))

    def step(self) -> None:
        if self.state == ElevatorState.IDLE:
            if self.up_stops:
                self.state = ElevatorState.MOVING_UP
            elif self.down_stops:
                self.state = ElevatorState.MOVING_DOWN
            else:
                return

        if self.state == ElevatorState.MOVING_UP:
            self.current_floor += 1

            while self.up_stops and self.up_stops[0][0] <= self.current_floor:
                floor, request = heapq.heappop(self.up_stops)
                is_match = floor == self.current_floor and (
                        request.direction is None or request.direction == Direction.UP
                )
                if not is_match:
                    # already passed this floor, or wrong direction - reschedule for the down run
                    heapq.heappush(self.down_stops, (-floor, request))

            if not self.up_stops:
                if self.down_stops:
                    self.state = ElevatorState.MOVING_DOWN
                else:
                    self.state = ElevatorState.IDLE

        elif self.state == ElevatorState.MOVING_DOWN:
            self.current_floor -= 1

            while self.down_stops and -self.down_stops[0][0] >= self.current_floor:
                neg_floor, request = heapq.heappop(self.down_stops)
                floor = -neg_floor
                is_match = floor == self.current_floor and (
                        request.direction is None or request.direction == Direction.DOWN
                )
                if not is_match:
                    heapq.heappush(self.up_stops, (floor, request))

            if not self.down_stops:
                if self.up_stops:
                    self.state = ElevatorState.MOVING_UP
                else:
                    self.state = ElevatorState.IDLE

class ElevatorController:
    """Owns one or more elevators and routes incoming requests to them.
    For v1, with a single elevator, dispatch is trivial - but this seam is
    exactly where multi-elevator dispatch logic would plug in later."""
    def __init__(self):
        self.elevators: List[Elevator] = []

    def add_elevator(self, elevator: Elevator) -> None:
        self.elevators.append(elevator)

    def request_elevator(self, floor: int, direction: Direction) -> None:
        """A hall call - someone outside pressing up/down."""
        if not self.elevators:
            raise ValueError("No elevators available.")

        elevator = self.elevators[0]

        request = Request(floor, direction)

        elevator.add_request(request)

    def request_floor(self, elevator_id: str, floor: int) -> None:
        """A car request - someone inside pressing a destination button."""
        for elevator in self.elevators:
            if elevator.elevator_id == elevator_id:
                request = Request(floor)
                elevator.add_request(request)
                return

        raise ValueError(f"Elevator {elevator_id} not found.")
