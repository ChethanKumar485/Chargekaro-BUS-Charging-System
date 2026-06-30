"""
ChargeKaru — Data models
=========================
Pure in-memory data structures (no real DB needed for the simulation).
Everything here models the real-world KSRTC entities this system would touch:
buses, routes, seats, tickets, passes, and live charging sessions.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid
import random


class PassType(str, Enum):
    DAILY = "daily"
    MONTHLY = "monthly"
    STUDENT = "student"


class SeatChargeState(str, Enum):
    IDLE = "idle"                  # empty seat, socket off
    OCCUPIED_UNVERIFIED = "occupied_unverified"   # someone sitting, no valid ticket yet -> socket OFF
    CHARGING = "charging"          # pressure + valid ticket -> socket ON
    FAULT = "fault"                # simulated hardware fault (rare, for realism)


class Ticket(BaseModel):
    pnr: str
    passenger_name: str
    seat_number: Optional[str] = None
    route: str
    valid_from: datetime
    valid_until: datetime
    is_active: bool = True


class Pass(BaseModel):
    pass_id: str
    passenger_name: str
    pass_type: PassType
    valid_from: datetime
    valid_until: datetime
    is_active: bool = True


class Seat(BaseModel):
    seat_number: str
    pressure_detected: bool = False        # simulated seat sensor
    ticket_validated: bool = False         # PNR/pass scanned & valid for THIS seat
    state: SeatChargeState = SeatChargeState.IDLE
    bound_pnr_or_pass: Optional[str] = None
    charging_since: Optional[datetime] = None
    session_wh_used: float = 0.0           # simulated energy usage in Watt-hours
    last_event: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    def recompute_state(self):
        """
        Core activation rule (this is the heart of the whole idea):
        Socket only goes live when BOTH are true:
          1. Seat pressure sensor detects a person seated
          2. A valid ticket/pass has been validated and bound to this seat
        If either drops, charging stops immediately (auto safety cutoff).
        """
        if self.pressure_detected and self.ticket_validated:
            if self.state != SeatChargeState.CHARGING:
                self.charging_since = datetime.utcnow()
                self.last_event = "Charging started — seat occupied + ticket verified"
            self.state = SeatChargeState.CHARGING
        elif self.pressure_detected and not self.ticket_validated:
            self.state = SeatChargeState.OCCUPIED_UNVERIFIED
            self.charging_since = None
            self.last_event = "Seat occupied but no valid ticket — socket OFF"
        else:
            if self.state == SeatChargeState.CHARGING:
                self.last_event = "Charging stopped — passenger left seat"
            self.state = SeatChargeState.IDLE
            self.charging_since = None
            self.bound_pnr_or_pass = None
            self.ticket_validated = False
        self.last_updated = datetime.utcnow()


class Bus(BaseModel):
    bus_id: str
    registration_number: str
    route_name: str
    route_code: str
    bus_type: str  # "KSRTC Airavat", "KSRTC Express", "Private - VRL", etc.
    total_seats: int
    seats: dict[str, Seat] = Field(default_factory=dict)
    driver_name: str
    conductor_name: str
    current_location: str = "Depot"
    is_active: bool = True

    def charging_count(self) -> int:
        return sum(1 for s in self.seats.values() if s.state == SeatChargeState.CHARGING)

    def occupied_count(self) -> int:
        return sum(1 for s in self.seats.values() if s.pressure_detected)

    def total_power_draw_w(self) -> float:
        # Assume ~10W average draw per actively charging phone (realistic USB-A/PD trickle)
        return self.charging_count() * 10.0


class FleetSummary(BaseModel):
    total_buses: int
    active_buses: int
    total_seats: int
    occupied_seats: int
    charging_seats: int
    total_power_draw_w: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
