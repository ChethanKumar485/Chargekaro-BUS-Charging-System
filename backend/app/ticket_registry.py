"""
ChargeKaru — Ticket Registry
A simulated in-memory KSRTC ticketing/pass database used to validate seats.
"""

from datetime import datetime, timedelta
from typing import Optional

from .models import BusPass, PassType, Ticket, generate_pass_id, generate_pnr

# In-memory stores (demo only — would be a real DB / KSRTC API in production)
TICKETS: dict[str, Ticket] = {}
PASSES: dict[str, BusPass] = {}

PASS_VALIDITY = {
    PassType.DAILY: timedelta(days=1),
    PassType.MONTHLY: timedelta(days=30),
    PassType.STUDENT: timedelta(days=180),
}


def issue_ticket(bus_id: str, seat_no: str, passenger_name: str, hours_valid: float = 6) -> Ticket:
    pnr = generate_pnr()
    while pnr in TICKETS:
        pnr = generate_pnr()
    ticket = Ticket(
        pnr=pnr,
        bus_id=bus_id,
        seat_no=seat_no,
        passenger_name=passenger_name,
        valid_until=datetime.utcnow() + timedelta(hours=hours_valid),
    )
    TICKETS[pnr] = ticket
    return ticket


def issue_pass(pass_type: PassType, holder_name: str) -> BusPass:
    pass_id = generate_pass_id(pass_type)
    while pass_id in PASSES:
        pass_id = generate_pass_id(pass_type)
    bus_pass = BusPass(
        pass_id=pass_id,
        pass_type=pass_type,
        holder_name=holder_name,
        valid_until=datetime.utcnow() + PASS_VALIDITY[pass_type],
    )
    PASSES[pass_id] = bus_pass
    return bus_pass


def validate_code(code: str) -> dict:
    """Validate a PNR or Pass ID. Returns a dict describing the result."""
    code = code.strip().upper()

    if code in TICKETS:
        ticket = TICKETS[code]
        return {
            "valid": ticket.is_valid,
            "type": "ticket",
            "holder_name": ticket.passenger_name,
            "detail": ticket,
        }

    if code in PASSES:
        bus_pass = PASSES[code]
        return {
            "valid": bus_pass.is_valid,
            "type": "pass",
            "holder_name": bus_pass.holder_name,
            "detail": bus_pass,
        }

    return {"valid": False, "type": None, "holder_name": None, "detail": None}


def seed_sample_codes() -> dict:
    """Seed a handful of ready-to-use demo codes for presentations."""
    t1 = issue_ticket("BUS-1", "A1", "Ramesh Gowda")
    t2 = issue_ticket("BUS-1", "A2", "Sandhya Rao")
    t3 = issue_ticket("BUS-2", "B3", "Mohammed Imran")
    p1 = issue_pass(PassType.STUDENT, "Anjali Shetty")
    p2 = issue_pass(PassType.MONTHLY, "Pradeep Kumar")
    p3 = issue_pass(PassType.DAILY, "Lakshmi Devi")
    return {
        "tickets": [t1.pnr, t2.pnr, t3.pnr],
        "passes": [p1.pass_id, p2.pass_id, p3.pass_id],
    }
