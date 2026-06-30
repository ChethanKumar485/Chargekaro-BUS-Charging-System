"""
ChargeKaru — Data Models
Pydantic v2 models representing buses, seats, tickets and passes.
"""

from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------

class SeatState(str, Enum):
    IDLE = "idle"                          # empty seat, socket OFF
    OCCUPIED_UNVERIFIED = "occupied_unverified"  # seated, no valid ticket, socket OFF
    CHARGING = "charging"                  # seated + valid ticket, socket ON
    FAULT = "fault"                        # simulated hardware fault


class PassType(str, Enum):
    DAILY = "daily"
    MONTHLY = "monthly"
    STUDENT = "student"


# --------------------------------------------------------------------------
# Ticketing models
# --------------------------------------------------------------------------

class Ticket(BaseModel):
    pnr: str
    bus_id: str
    seat_no: str
    passenger_name: str
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    valid_until: datetime
    used: bool = False

    @property
    def is_valid(self) -> bool:
        return (not self.used) and datetime.utcnow() <= self.valid_until


class BusPass(BaseModel):
    pass_id: str
    pass_type: PassType
    holder_name: str
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    valid_until: datetime

    @property
    def is_valid(self) -> bool:
        return datetime.utcnow() <= self.valid_until


def generate_pnr() -> str:
    return "KS" + "".join(random.choices(string.digits, k=8))


def generate_pass_id(pass_type: PassType) -> str:
    prefix = {"daily": "PD", "monthly": "PM", "student": "PS"}[pass_type.value]
    return prefix + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


# --------------------------------------------------------------------------
# Seat model — the heart of the system
# --------------------------------------------------------------------------

POWER_DRAW_W: float = 10.0  # simulated USB-PD draw per active socket (Watts)


class Seat(BaseModel):
    seat_no: str
    pressure_detected: bool = False
    ticket_validated: bool = False
    validated_code: Optional[str] = None     # PNR or Pass ID currently validating this seat
    state: SeatState = SeatState.IDLE
    fault: bool = False
    session_started_at: Optional[datetime] = None
    energy_wh: float = 0.0                   # cumulative energy delivered this session (Wh)

    def recompute_state(self) -> None:
        """Core activation rule for ChargeKaru.

        IF pressure AND ticket_validated -> CHARGING (socket ON)
        IF pressure AND NOT ticket_validated -> OCCUPIED_UNVERIFIED (socket OFF)
        IF NOT pressure -> IDLE (socket OFF), auto-reset ticket validation
        """
        if self.fault:
            self.state = SeatState.FAULT
            return

        if not self.pressure_detected:
            # Passenger left — auto reset for next rider
            self.ticket_validated = False
            self.validated_code = None
            self.state = SeatState.IDLE
            self.session_started_at = None
            return

        if self.pressure_detected and self.ticket_validated:
            if self.state != SeatState.CHARGING:
                self.session_started_at = datetime.utcnow()
            self.state = SeatState.CHARGING
        else:
            self.state = SeatState.OCCUPIED_UNVERIFIED
            self.session_started_at = None

    def tick_energy(self, seconds: float = 1.0) -> None:
        """Advance simulated energy delivery if currently charging."""
        if self.state == SeatState.CHARGING:
            self.energy_wh += POWER_DRAW_W * (seconds / 3600.0)


# --------------------------------------------------------------------------
# Bus model
# --------------------------------------------------------------------------

class Bus(BaseModel):
    bus_id: str
    registration: str
    route: str
    seats: dict[str, Seat]

    @property
    def total_seats(self) -> int:
        return len(self.seats)

    @property
    def charging_count(self) -> int:
        return sum(1 for s in self.seats.values() if s.state == SeatState.CHARGING)

    @property
    def occupied_count(self) -> int:
        return sum(
            1 for s in self.seats.values()
            if s.state in (SeatState.CHARGING, SeatState.OCCUPIED_UNVERIFIED)
        )

    @property
    def total_energy_wh(self) -> float:
        return round(sum(s.energy_wh for s in self.seats.values()), 2)

    @property
    def current_power_draw_w(self) -> float:
        return round(self.charging_count * POWER_DRAW_W, 1)
