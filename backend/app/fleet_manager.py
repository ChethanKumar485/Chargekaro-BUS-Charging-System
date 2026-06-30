"""
ChargeKaru — Fleet manager
============================
Owns the live in-memory state of every bus in the simulated fleet and
exposes the operations the API layer needs: boarding, leaving, ticket
validation, sensor toggling, and periodic "natural" simulation ticks
(used by the demo simulator to make buses feel alive without manual clicks).
"""

import random
from datetime import datetime
from app.models import Bus, Seat, SeatChargeState, FleetSummary
from app.ticket_registry import registry, ROUTES, _random_name

BUS_TYPES = ["KSRTC Airavat Club Class", "KSRTC Rajahamsa", "KSRTC Express",
             "Private - VRL Travels", "Private - SRS Travels"]

DRIVER_NAMES = ["Manjunath K.", "Srinivas R.", "Basavaraj P.", "Eshwar G.", "Ramesh N."]
CONDUCTOR_NAMES = ["Shivakumar T.", "Nagaraj S.", "Prakash M.", "Veeresh B.", "Anand K."]


def _seat_layout(total: int) -> list[str]:
    """Generate seat numbers like 1A,1B,1C,1D, 2A... (4 across, KSRTC style)."""
    letters = ["A", "B", "C", "D"]
    seats = []
    row = 1
    while len(seats) < total:
        for l in letters:
            if len(seats) >= total:
                break
            seats.append(f"{row}{l}")
        row += 1
    return seats


class FleetManager:
    def __init__(self):
        self.buses: dict[str, Bus] = {}

    def create_bus(self, total_seats: int = 36) -> Bus:
        route_name, route_code = random.choice(ROUTES)
        bus_id = f"BUS-{random.randint(1000, 9999)}"
        reg_no = f"KA-{random.randint(1,59):02d}-F-{random.randint(1000,9999)}"
        seats = {sn: Seat(seat_number=sn) for sn in _seat_layout(total_seats)}
        bus = Bus(
            bus_id=bus_id,
            registration_number=reg_no,
            route_name=route_name,
            route_code=route_code,
            bus_type=random.choice(BUS_TYPES),
            total_seats=total_seats,
            seats=seats,
            driver_name=random.choice(DRIVER_NAMES),
            conductor_name=random.choice(CONDUCTOR_NAMES),
            current_location="Depot",
            is_active=True,
        )
        self.buses[bus_id] = bus
        return bus

    def seed_fleet(self, num_buses: int = 6):
        for _ in range(num_buses):
            self.create_bus(total_seats=random.choice([32, 36, 40]))

    def get_bus(self, bus_id: str) -> Bus | None:
        return self.buses.get(bus_id)

    def list_buses(self) -> list[Bus]:
        return list(self.buses.values())

    # ---- Core passenger actions ----

    def board_seat(self, bus_id: str, seat_number: str) -> Seat | None:
        """Simulated pressure sensor fires: passenger sits down."""
        bus = self.get_bus(bus_id)
        if not bus or seat_number not in bus.seats:
            return None
        seat = bus.seats[seat_number]
        seat.pressure_detected = True
        seat.recompute_state()
        return seat

    def leave_seat(self, bus_id: str, seat_number: str) -> Seat | None:
        """Simulated pressure sensor releases: passenger stands/exits."""
        bus = self.get_bus(bus_id)
        if not bus or seat_number not in bus.seats:
            return None
        seat = bus.seats[seat_number]
        seat.pressure_detected = False
        seat.recompute_state()
        return seat

    def validate_seat_ticket(self, bus_id: str, seat_number: str, code: str):
        """Conductor or passenger validates PNR/Pass for a specific seat."""
        bus = self.get_bus(bus_id)
        if not bus or seat_number not in bus.seats:
            return None, "Bus or seat not found."
        seat = bus.seats[seat_number]
        is_valid, message, record = registry.validate(code)
        if is_valid:
            seat.ticket_validated = True
            seat.bound_pnr_or_pass = code.strip().upper()
        seat.recompute_state()
        return seat, message

    def tick_energy(self):
        """Call periodically: accrue simulated Wh for every seat currently charging."""
        for bus in self.buses.values():
            for seat in bus.seats.values():
                if seat.state == SeatChargeState.CHARGING:
                    # ~10W draw, tick assumed to represent ~5 seconds of real time in demo speed
                    seat.session_wh_used += (10.0 * (5 / 3600))

    def fleet_summary(self) -> FleetSummary:
        total_seats = sum(b.total_seats for b in self.buses.values())
        occupied = sum(b.occupied_count() for b in self.buses.values())
        charging = sum(b.charging_count() for b in self.buses.values())
        power = sum(b.total_power_draw_w() for b in self.buses.values())
        return FleetSummary(
            total_buses=len(self.buses),
            active_buses=sum(1 for b in self.buses.values() if b.is_active),
            total_seats=total_seats,
            occupied_seats=occupied,
            charging_seats=charging,
            total_power_draw_w=power,
        )


# Global singleton
fleet = FleetManager()
