"""
ChargeKaru — Mock ticket & pass database
==========================================
Simulates the KSRTC ticketing backend (PNR + pass lookups) that a real
deployment would integrate with. In production this would be a real API
call to KSRTC's reservation system; here it's an in-memory mock so the
whole project runs standalone with zero external dependencies.
"""

import random
import string
from datetime import datetime, timedelta
from app.models import Ticket, Pass, PassType

FIRST_NAMES = ["Aditi", "Rahul", "Sneha", "Vikram", "Pooja", "Arjun", "Divya",
               "Karthik", "Lakshmi", "Manoj", "Nisha", "Pradeep", "Ravi", "Sunita",
               "Vinay", "Anjali", "Suresh", "Meera", "Ganesh", "Kavya"]
LAST_NAMES = ["Sharma", "Reddy", "Gowda", "Iyer", "Nair", "Hegde", "Rao", "Patil",
              "Shetty", "Naik", "Murthy", "Pillai", "Kumar", "Bhat"]

ROUTES = [
    ("Bengaluru - Mysuru", "KA-RT-101"),
    ("Bengaluru - Mangaluru", "KA-RT-205"),
    ("Bengaluru - Hubballi", "KA-RT-310"),
    ("Mysuru - Coorg", "KA-RT-417"),
    ("Bengaluru - Shivamogga", "KA-RT-522"),
    ("Bengaluru - Belagavi", "KA-RT-630"),
]


def _random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _random_pnr() -> str:
    return "KS" + "".join(random.choices(string.digits, k=8))


def _random_pass_id() -> str:
    return "KSP" + "".join(random.choices(string.digits, k=6))


class TicketRegistry:
    """In-memory registry simulating KSRTC's central ticket/pass database."""

    def __init__(self):
        self.tickets: dict[str, Ticket] = {}
        self.passes: dict[str, Pass] = {}

    def issue_ticket(self, route: str, seat_number: str | None = None,
                      passenger_name: str | None = None,
                      valid_minutes: int = 240) -> Ticket:
        pnr = _random_pnr()
        now = datetime.utcnow()
        ticket = Ticket(
            pnr=pnr,
            passenger_name=passenger_name or _random_name(),
            seat_number=seat_number,
            route=route,
            valid_from=now,
            valid_until=now + timedelta(minutes=valid_minutes),
            is_active=True,
        )
        self.tickets[pnr] = ticket
        return ticket

    def issue_pass(self, pass_type: PassType = PassType.MONTHLY,
                    passenger_name: str | None = None) -> Pass:
        pid = _random_pass_id()
        now = datetime.utcnow()
        duration = {
            PassType.DAILY: timedelta(days=1),
            PassType.MONTHLY: timedelta(days=30),
            PassType.STUDENT: timedelta(days=90),
        }[pass_type]
        p = Pass(
            pass_id=pid,
            passenger_name=passenger_name or _random_name(),
            pass_type=pass_type,
            valid_from=now,
            valid_until=now + duration,
            is_active=True,
        )
        self.passes[pid] = p
        return p

    def validate(self, code: str) -> tuple[bool, str, Ticket | Pass | None]:
        """
        Validate a PNR or Pass ID.
        Returns (is_valid, message, record)
        """
        code = code.strip().upper()
        now = datetime.utcnow()

        if code in self.tickets:
            t = self.tickets[code]
            if not t.is_active:
                return False, "Ticket has been cancelled.", t
            if now > t.valid_until:
                return False, "Ticket has expired.", t
            if now < t.valid_from:
                return False, "Ticket is not yet valid.", t
            return True, f"Valid ticket for {t.passenger_name} — {t.route}", t

        if code in self.passes:
            p = self.passes[code]
            if not p.is_active:
                return False, "Pass has been deactivated.", p
            if now > p.valid_until:
                return False, "Pass has expired.", p
            return True, f"Valid {p.pass_type.value} pass for {p.passenger_name}", p

        return False, "PNR / Pass ID not found in KSRTC records.", None


# Global singleton used by the app
registry = TicketRegistry()


def seed_registry(num_tickets: int = 60, num_passes: int = 15):
    """Pre-populate with realistic sample tickets/passes for the demo."""
    for _ in range(num_tickets):
        route, _ = random.choice(ROUTES)
        registry.issue_ticket(route=route, valid_minutes=random.choice([120, 240, 360]))
    for _ in range(num_passes):
        registry.issue_pass(pass_type=random.choice(list(PassType)))
    return registry
