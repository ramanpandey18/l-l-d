import heapq
import itertools
import threading
from enum import Enum
from typing import List, Optional


class Direction(Enum):
    UP = "UP"
    DOWN = "DOWN"


class State(Enum):
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
        if min_floor > max_floor:
            raise ValueError("Invalid floor range.")
        if not (min_floor <= current_floor <= max_floor):
            raise ValueError("Current floor out of range.")
        self.elevator_id = elevator_id
        self.min_floor = min_floor
        self.max_floor = max_floor
        self.current_floor = current_floor
        self.state: State = State.IDLE

        # min-heap: pending stops ABOVE current position, closest first
        self.up_stops: List[tuple] = []
        # max-heap (via negation): pending stops BELOW current position, closest first
        # heap entries are (floor, seq, request); seq breaks ties so requests are never compared
        self.down_stops: List[tuple] = []
        self._seq = itertools.count()

        self.served = []  # log of (floor, request direction, travel direction)
        self.lock = threading.Lock()            # protects heaps, state, floor, log
        self.lifecycle_lock = threading.Lock()  # serializes start()/stop()
        self.stop_event = threading.Event()
        self.worker: Optional[threading.Thread] = None

    @property
    def requests(self) -> List[Request]:
        """All pending requests (handy for tests and debugging)."""
        return [entry[2] for entry in self.up_stops + self.down_stops]

    def _push_up(self, request: Request) -> None:
        heapq.heappush(self.up_stops, (request.floor, next(self._seq), request))

    def _push_down(self, request: Request) -> None:
        heapq.heappush(self.down_stops, (-request.floor, next(self._seq), request))

    def add_request(self, request: Request) -> None:
        if request.floor < self.min_floor or request.floor > self.max_floor:
            raise ValueError("Floor out of range.")

        with self.lock:
            for r in self.requests:  # ignore duplicate button presses
                if r.floor == request.floor and r.direction == request.direction:
                    return

            if request.floor == self.current_floor and self.state == State.IDLE:
                # already here and not moving: doors open, served right away
                self.served.append((request.floor, request.direction, None))
            elif request.floor > self.current_floor or (
                    request.floor == self.current_floor and self.state == State.MOVING_DOWN):
                self._push_up(request)    # above us (or on this floor, which we are leaving downwards)
            else:
                self._push_down(request)  # below us (or on this floor, which we are leaving upwards)

    def step(self) -> None:
        with self.lock:
            if self.state == State.IDLE:
                if self.up_stops:
                    self.state = State.MOVING_UP
                elif self.down_stops:
                    self.state = State.MOVING_DOWN
                else:
                    return
            if self.state == State.MOVING_UP:
                self.current_floor += 1
                due = []
                while self.up_stops and self.up_stops[0][0] <= self.current_floor:
                    due.append(heapq.heappop(self.up_stops)[2])
                # last stop going up: we reverse here, so serve every call on this floor
                turnaround = not self.up_stops
                for request in due:
                    if turnaround or request.direction in (None, Direction.UP):
                        self.served.append((self.current_floor, request.direction, Direction.UP))
                    else:
                        # wrong direction: collect it on the way back down
                        self._push_down(request)
                if not self.up_stops:
                    if self.down_stops:
                        self.state = State.MOVING_DOWN
                    else:
                        self.state = State.IDLE
            elif self.state == State.MOVING_DOWN:
                self.current_floor -= 1
                due = []
                while self.down_stops and -self.down_stops[0][0] >= self.current_floor:
                    due.append(heapq.heappop(self.down_stops)[2])
                # last stop going down: we reverse here, so serve every call on this floor
                turnaround = not self.down_stops
                for request in due:
                    if turnaround or request.direction in (None, Direction.DOWN):
                        self.served.append((self.current_floor, request.direction, Direction.DOWN))
                    else:
                        # wrong direction: collect it on the way back up
                        self._push_up(request)
                if not self.down_stops:
                    if self.up_stops:
                        self.state = State.MOVING_UP
                    else:
                        self.state = State.IDLE

    # --- background ticking ---
    def start(self, tick_seconds: float = 1.0) -> None:
        if tick_seconds <= 0:
            raise ValueError("tick_seconds must be positive.")
        with self.lifecycle_lock:
            if self.worker and self.worker.is_alive():
                return  # already running
            self.stop_event.clear()
            self.worker = threading.Thread(target=self._run, args=(tick_seconds,), daemon=True)
            self.worker.start()

    def stop(self) -> None:
        with self.lifecycle_lock:
            self.stop_event.set()
            if self.worker and self.worker is not threading.current_thread():
                self.worker.join()

    def _run(self, tick_seconds: float) -> None:
        while not self.stop_event.is_set():
            self.step()
            self.stop_event.wait(tick_seconds)


class ElevatorController:
    """Owns one or more elevators and routes incoming requests to them.
    For v1, with a single elevator, dispatch is trivial - but this seam is
    exactly where multi-elevator dispatch logic would plug in later."""
    def __init__(self):
        self.elevators: List[Elevator] = []
        self.lock = threading.Lock()

    def add_elevator(self, elevator: Elevator) -> None:
        with self.lock:
            if any(e.elevator_id == elevator.elevator_id for e in self.elevators):
                raise ValueError(f"Elevator {elevator.elevator_id} already exists.")
            self.elevators.append(elevator)

    def request_elevator(self, floor: int, direction: Direction) -> None:
        """A hall call - someone outside pressing up/down."""
        with self.lock:
            if not self.elevators:
                raise ValueError("No elevators available.")
            elevator = self.elevators[0]
        elevator.add_request(Request(floor, direction))

    def request_floor(self, elevator_id: str, floor: int) -> None:
        """A car request - someone inside pressing a destination button."""
        with self.lock:
            elevators = list(self.elevators)
        for elevator in elevators:
            if elevator.elevator_id == elevator_id:
                elevator.add_request(Request(floor))
                return
        raise ValueError(f"Elevator {elevator_id} not found.")
