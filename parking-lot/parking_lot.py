from typing import Dict, Optional, List
from datetime import datetime
from enum import IntEnum
import threading
import uuid


class VehicleSize(IntEnum):
    SMALL = 1
    MEDIUM = 2
    LARGE = 3


class Vehicle:
    def __init__(self, size: VehicleSize, color: str, license_plate: str):
        self.size = size
        self.color = color
        self.license_plate = license_plate


class ParkingSpot:
    def __init__(self, spot_id: str, size: VehicleSize):
        self.spot_id = spot_id
        self.size = size
        self.is_occupied: bool = False


class Floor:
    def __init__(self, floor_number: int):
        self.floor_number = floor_number
        self.spots: List[ParkingSpot] = []


class Ticket:
    def __init__(self, vehicle: Vehicle, spot: ParkingSpot, entry_time: datetime):
        self.ticket_id: Optional[str] = None
        self.vehicle = vehicle
        self.spot = spot
        self.entry_time = entry_time


class ParkingLot:
    HOURLY_RATES = {
        VehicleSize.SMALL: 1.0,
        VehicleSize.MEDIUM: 2.0,
        VehicleSize.LARGE: 4.0,
    }

    def __init__(self):
        self.floors: List[Floor] = []
        self.active_tickets: Dict[str, Ticket] = {}  # ticket_id -> Ticket
        self.lock = threading.Lock()

    def add_floor(self, floor: Floor):
        if not isinstance(floor, Floor):
            raise ValueError("Expected a Floor instance.")

        with self.lock:
            if any(existing.floor_number == floor.floor_number for existing in self.floors):
                raise ValueError(f"Floor {floor.floor_number} already exists.")
            self.floors.append(floor)

    def _calculate_fee(self, vehicle_size: VehicleSize, duration_hours: float) -> float:
        if not isinstance(duration_hours, (float, int)) or duration_hours < 0:
            raise ValueError("Parking duration cannot be negative.")

        rate = self.HOURLY_RATES[vehicle_size]
        return round(rate * duration_hours, 2)

    def park(self, vehicle: Vehicle) -> Ticket:
        with self.lock:
            candidates = []
            for floor in self.floors:
                for spot in floor.spots:
                    if not spot.is_occupied and spot.size >= vehicle.size:
                        candidates.append(spot)

            if not candidates:
                raise ValueError(f"No available spot for vehicle size {vehicle.size.name}")

            best_spot = min(candidates, key=lambda spot: spot.size)
            best_spot.is_occupied = True

            ticket = Ticket(vehicle, best_spot, datetime.now())
            ticket.ticket_id = str(uuid.uuid4())
            self.active_tickets[ticket.ticket_id] = ticket

            return ticket

    def unpark(self, ticket_id: str) -> float:
        with self.lock:
            ticket = self.active_tickets.get(ticket_id)
            if not ticket:
                raise ValueError("Ticket not found.")

            duration = datetime.now() - ticket.entry_time
            duration_hours = duration.total_seconds() / 3600
            fee = self._calculate_fee(ticket.vehicle.size, duration_hours)

            ticket.spot.is_occupied = False
            del self.active_tickets[ticket_id]

            return fee
