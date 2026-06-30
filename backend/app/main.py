"""
ChargeKaru — Backend API
===========================
FastAPI server exposing the fleet simulation. This is what the conductor
dashboard and passenger view talk to. Run with:

    uvicorn app.main:app --reload --port 8000

Then visit http://localhost:8000/docs for interactive API docs.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

from app.fleet_manager import fleet
from app.ticket_registry import registry, seed_registry, ROUTES
from app.models import PassType

app = FastAPI(
    title="ChargeKaru API",
    description="Smart seat-charging simulation for KSRTC buses — "
                 "charges only activate when a seat is occupied AND a valid ticket/pass is verified.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    seed_registry(num_tickets=80, num_passes=20)
    fleet.seed_fleet(num_buses=6)


# ---------- Request models ----------

class ValidateRequest(BaseModel):
    code: str


class IssueTicketRequest(BaseModel):
    route: str | None = None
    passenger_name: str | None = None


class IssuePassRequest(BaseModel):
    pass_type: PassType = PassType.MONTHLY
    passenger_name: str | None = None


# ---------- Fleet endpoints ----------

@app.get("/fleet/summary")
def get_fleet_summary():
    return fleet.fleet_summary()


@app.get("/fleet/buses")
def list_buses():
    return [
        {
            "bus_id": b.bus_id,
            "registration_number": b.registration_number,
            "route_name": b.route_name,
            "route_code": b.route_code,
            "bus_type": b.bus_type,
            "total_seats": b.total_seats,
            "driver_name": b.driver_name,
            "conductor_name": b.conductor_name,
            "current_location": b.current_location,
            "occupied_count": b.occupied_count(),
            "charging_count": b.charging_count(),
            "total_power_draw_w": round(b.total_power_draw_w(), 1),
        }
        for b in fleet.list_buses()
    ]


@app.get("/fleet/buses/{bus_id}")
def get_bus(bus_id: str):
    bus = fleet.get_bus(bus_id)
    if not bus:
        raise HTTPException(404, "Bus not found")
    return bus


# ---------- Seat actions ----------

@app.post("/fleet/buses/{bus_id}/seats/{seat_number}/board")
def board(bus_id: str, seat_number: str):
    seat = fleet.board_seat(bus_id, seat_number)
    if not seat:
        raise HTTPException(404, "Bus or seat not found")
    return seat


@app.post("/fleet/buses/{bus_id}/seats/{seat_number}/leave")
def leave(bus_id: str, seat_number: str):
    seat = fleet.leave_seat(bus_id, seat_number)
    if not seat:
        raise HTTPException(404, "Bus or seat not found")
    return seat


@app.post("/fleet/buses/{bus_id}/seats/{seat_number}/validate")
def validate_seat(bus_id: str, seat_number: str, body: ValidateRequest):
    seat, message = fleet.validate_seat_ticket(bus_id, seat_number, body.code)
    if seat is None:
        raise HTTPException(404, message)
    return {"seat": seat, "message": message}


# ---------- Ticketing endpoints (mock KSRTC reservation system) ----------

@app.post("/ticketing/issue-ticket")
def issue_ticket(body: IssueTicketRequest):
    route = body.route or random.choice(ROUTES)[0]
    t = registry.issue_ticket(route=route, passenger_name=body.passenger_name)
    return t


@app.post("/ticketing/issue-pass")
def issue_pass(body: IssuePassRequest):
    p = registry.issue_pass(pass_type=body.pass_type, passenger_name=body.passenger_name)
    return p


@app.post("/ticketing/validate")
def validate_code(body: ValidateRequest):
    is_valid, message, record = registry.validate(body.code)
    return {"is_valid": is_valid, "message": message, "record": record}


@app.get("/ticketing/sample-codes")
def sample_codes():
    """Returns a handful of real seeded PNRs/passes — handy for demo purposes."""
    pnrs = list(registry.tickets.keys())[:5]
    passes = list(registry.passes.keys())[:5]
    return {"sample_pnrs": pnrs, "sample_passes": passes}


# ---------- Simulation tick (used by the live demo simulator) ----------

@app.post("/simulate/tick")
def simulate_tick():
    """Advances simulated energy accrual. Called periodically by the frontend simulator."""
    fleet.tick_energy()
    return {"status": "ticked"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "ChargeKaru API"}
