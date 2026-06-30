"""
ChargeKaru — Fleet Manager
Holds live in-memory fleet state and exposes the boarding/validation/energy operations
used by the API layer.
"""

import random
from datetime import datetime

from .models import Bus, Seat, SeatState
from . import ticket_registry

ROUTES = [
    "Bengaluru → Mysuru",
    "Bengaluru → Mangaluru",
    "Bengaluru → Hubballi",
    "Bengaluru → Belagavi",
    "Bengaluru → Shivamogga",
    "Bengaluru → Tumakuru",
]

SEAT_LAYOUT = [f"{row}{col}" for row in "ABCDEFGHIJ" for col in (1, 2)]  # 20 seats/bus


class FleetManager:
    def __init__(self) -> None:
        self.buses: dict[str, Bus] = {}
        self._init_fleet()

    def _init_fleet(self) -> None:
        for i in range(1, 7):
            bus_id = f"BUS-{i}"
            seats = {sn: Seat(seat_no=sn) for sn in SEAT_LAYOUT}
            self.buses[bus_id] = Bus(
                bus_id=bus_id,
                registration=f"KA-{random.randint(1,59):02d}-F-{random.randint(1000,9999)}",
                route=ROUTES[i - 1],
                seats=seats,
            )

    # ---------------------------------------------------------------
    # Lookups
    # ---------------------------------------------------------------

    def get_bus(self, bus_id: str) -> Bus | None:
        return self.buses.get(bus_id.upper())

    def get_seat(self, bus_id: str, seat_no: str) -> Seat | None:
        bus = self.get_bus(bus_id)
        if not bus:
            return None
        return bus.seats.get(seat_no.upper())

    # ---------------------------------------------------------------
    # Sensor / ticket events
    # ---------------------------------------------------------------

    def board(self, bus_id: str, seat_no: str) -> Seat | None:
        seat = self.get_seat(bus_id, seat_no)
        if not seat:
            return None
        seat.pressure_detected = True
        seat.recompute_state()
        return seat

    def leave(self, bus_id: str, seat_no: str) -> Seat | None:
        seat = self.get_seat(bus_id, seat_no)
        if not seat:
            return None
        seat.pressure_detected = False
        seat.recompute_state()
        return seat

    def validate(self, bus_id: str, seat_no: str, code: str) -> dict:
        seat = self.get_seat(bus_id, seat_no)
        if not seat:
            return {"ok": False, "reason": "seat_not_found"}

        result = ticket_registry.validate_code(code)
        if not result["valid"]:
            return {"ok": False, "reason": "invalid_or_expired_code", "result": result}

        seat.ticket_validated = True
        seat.validated_code = code.strip().upper()
        seat.recompute_state()
        return {"ok": True, "reason": "validated", "result": result, "seat": seat}

    def set_fault(self, bus_id: str, seat_no: str, fault: bool) -> Seat | None:
        seat = self.get_seat(bus_id, seat_no)
        if not seat:
            return None
        seat.fault = fault
        seat.recompute_state()
        return seat

    # ---------------------------------------------------------------
    # Simulation tick — advances energy counters
    # ---------------------------------------------------------------

    def tick(self, seconds: float = 1.0) -> dict:
        for bus in self.buses.values():
            for seat in bus.seats.values():
                seat.tick_energy(seconds)
        return self.fleet_summary()

    # ---------------------------------------------------------------
    # Aggregates
    # ---------------------------------------------------------------

    def fleet_summary(self) -> dict:
        total_seats = sum(b.total_seats for b in self.buses.values())
        charging = sum(b.charging_count for b in self.buses.values())
        occupied = sum(b.occupied_count for b in self.buses.values())
        power_draw = sum(b.current_power_draw_w for b in self.buses.values())
        energy = round(sum(b.total_energy_wh for b in self.buses.values()), 2)
        return {
            "total_buses": len(self.buses),
            "total_seats": total_seats,
            "occupied_seats": occupied,
            "charging_seats": charging,
            "current_power_draw_w": round(power_draw, 1),
            "total_energy_wh": energy,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Singleton fleet instance shared across the app
fleet_manager = FleetManager()
