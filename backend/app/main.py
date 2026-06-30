"""
ChargeKaru — FastAPI Backend
Core API for the smart seat-charging simulation.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .fleet_manager import fleet_manager
from .models import PassType
from . import ticket_registry

app = FastAPI(
    title="ChargeKaru API",
    description="Smart seat-charging system simulation for KSRTC buses",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed a few demo codes on startup so the dashboards have something to show
_SAMPLE_CODES = ticket_registry.seed_sample_codes()


# --------------------------------------------------------------------------
# Request bodies
# --------------------------------------------------------------------------

class ValidateBody(BaseModel):
    code: str


class IssueTicketBody(BaseModel):
    bus_id: str
    seat_no: str
    passenger_name: str
    hours_valid: float = 6


class IssuePassBody(BaseModel):
    pass_type: PassType
    holder_name: str


# --------------------------------------------------------------------------
# Fleet routes
# --------------------------------------------------------------------------

@app.get("/fleet/summary", tags=["fleet"])
def fleet_summary():
    return fleet_manager.fleet_summary()


@app.get("/fleet/buses", tags=["fleet"])
def list_buses():
    out = []
    for bus in fleet_manager.buses.values():
        out.append({
            "bus_id": bus.bus_id,
            "registration": bus.registration,
            "route": bus.route,
            "total_seats": bus.total_seats,
            "occupied_count": bus.occupied_count,
            "charging_count": bus.charging_count,
            "current_power_draw_w": bus.current_power_draw_w,
            "total_energy_wh": bus.total_energy_wh,
        })
    return out


@app.get("/fleet/buses/{bus_id}", tags=["fleet"])
def get_bus(bus_id: str):
    bus = fleet_manager.get_bus(bus_id)
    if not bus:
        raise HTTPException(404, "Bus not found")
    return bus


@app.post("/fleet/buses/{bus_id}/seats/{seat_no}/board", tags=["fleet"])
def board_seat(bus_id: str, seat_no: str):
    seat = fleet_manager.board(bus_id, seat_no)
    if not seat:
        raise HTTPException(404, "Bus or seat not found")
    return seat


@app.post("/fleet/buses/{bus_id}/seats/{seat_no}/leave", tags=["fleet"])
def leave_seat(bus_id: str, seat_no: str):
    seat = fleet_manager.leave(bus_id, seat_no)
    if not seat:
        raise HTTPException(404, "Bus or seat not found")
    return seat


@app.post("/fleet/buses/{bus_id}/seats/{seat_no}/validate", tags=["fleet"])
def validate_seat(bus_id: str, seat_no: str, body: ValidateBody):
    result = fleet_manager.validate(bus_id, seat_no, body.code)
    if not result["ok"]:
        raise HTTPException(400, result["reason"])
    return result["seat"]


@app.post("/fleet/buses/{bus_id}/seats/{seat_no}/fault", tags=["fleet"])
def fault_seat(bus_id: str, seat_no: str, fault: bool = True):
    seat = fleet_manager.set_fault(bus_id, seat_no, fault)
    if not seat:
        raise HTTPException(404, "Bus or seat not found")
    return seat


# --------------------------------------------------------------------------
# Ticketing routes
# --------------------------------------------------------------------------

@app.post("/ticketing/issue-ticket", tags=["ticketing"])
def issue_ticket(body: IssueTicketBody):
    ticket = ticket_registry.issue_ticket(
        body.bus_id, body.seat_no, body.passenger_name, body.hours_valid
    )
    return ticket


@app.post("/ticketing/issue-pass", tags=["ticketing"])
def issue_pass(body: IssuePassBody):
    bus_pass = ticket_registry.issue_pass(body.pass_type, body.holder_name)
    return bus_pass


@app.post("/ticketing/validate", tags=["ticketing"])
def validate_code(body: ValidateBody):
    return ticket_registry.validate_code(body.code)


@app.get("/ticketing/sample-codes", tags=["ticketing"])
def sample_codes():
    return _SAMPLE_CODES


# --------------------------------------------------------------------------
# Simulation route
# --------------------------------------------------------------------------

@app.post("/simulate/tick", tags=["simulation"])
def simulate_tick(seconds: float = 1.0):
    return fleet_manager.tick(seconds)


@app.get("/", tags=["meta"])
def root():
    return {
        "name": "ChargeKaru API",
        "status": "running",
        "docs": "/docs",
        "tagline": "Charge karu — only when you're seated and ticketed.",
    }
