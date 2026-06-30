# ⚡ ChargeKaru — Smart Seat-Charging System for KSRTC

> *"Charge karu"* — Kannada/Hindi mix for "I'll charge it."

ChargeKaru is a software-simulated smart charging system for KSRTC and private Karnataka buses. Every seat has a USB charging socket, but the socket only powers ON when **two conditions are both true**:

1. **Seat pressure sensor detects a passenger is seated**
2. **A valid KSRTC ticket or bus pass is verified for that seat**

The moment either condition drops (passenger stands up, or ticket expires), charging stops automatically. No ticket → no power. Simple, fair, fraud-proof.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        ChargeKaru                           │
│                                                             │
│  ┌──────────────┐    ┌─────────────┐    ┌───────────────┐  │
│  │  Seat Sensor │    │  Ticket DB  │    │  Socket Relay │  │
│  │ (simulated)  │───►│ (simulated) │───►│ (simulated)   │  │
│  └──────────────┘    └─────────────┘    └───────────────┘  │
│         │                   │                  │            │
│         └───────────────────┼──────────────────┘            │
│                             │                               │
│                    ┌────────▼────────┐                      │
│                    │  FastAPI Backend│                      │
│                    │  (Core Logic)   │                      │
│                    └────────┬────────┘                      │
│                             │                               │
│           ┌─────────────────┼─────────────────┐            │
│           │                 │                 │             │
│  ┌────────▼──────┐  ┌───────▼──────┐  ┌──────▼────────┐   │
│  │Fleet Dashboard│  │Passenger View│  │Demo Simulator │    │
│  │(conductor/ops)│  │(mobile-first)│  │(auto-pilot)   │    │
│  └───────────────┘  └──────────────┘  └───────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
chargekaru/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + all API routes
│   │   ├── models.py            # Pydantic data models (Bus, Seat, Ticket, Pass...)
│   │   ├── fleet_manager.py     # Live fleet state + boarding/charging logic
│   │   └── ticket_registry.py   # Simulated KSRTC ticket/pass database
│   ├── simulate_journey.py      # Demo auto-pilot: simulates passengers across fleet
│   └── requirements.txt
└── frontend/
    ├── dashboard.html           # Conductor/ops dashboard (fleet view + seat grid)
    └── passenger.html           # Passenger mobile view (check my charging status)
```

---

## How to Run

### Step 1 — Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend starts at **http://localhost:8000**
API docs auto-generated at **http://localhost:8000/docs**

### Step 2 — Open the dashboards

Open in your browser (no build step needed):
- `frontend/dashboard.html` — Conductor / Fleet operations view
- `frontend/passenger.html` — Passenger mobile view

### Step 3 — Run the demo simulator (for presentations)

In a second terminal:

```bash
cd backend
python simulate_journey.py
```

This auto-pilots passengers boarding, sitting, getting verified, and leaving across all 6 buses simultaneously. Watch `dashboard.html` update in real time.

---

## Core Activation Logic

The heart of the system is one rule (`Seat.recompute_state()` in `models.py`):

```
IF seat_pressure_detected == True
AND ticket_validated == True
THEN socket = ON  →  state = "charging"

IF seat_pressure_detected == True
AND ticket_validated == False
THEN socket = OFF  →  state = "occupied_unverified"

IF seat_pressure_detected == False
THEN socket = OFF  →  state = "idle"
    (also clears ticket validation — auto-reset for next passenger)
```

This means:
- A passenger cannot charge without a valid ticket (anti-fraud)
- A ticket holder cannot charge without physically sitting (anti-misuse)
- The socket auto-resets between passengers

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fleet/summary` | Fleet-wide stats (charging count, power draw...) |
| GET | `/fleet/buses` | List all buses with live stats |
| GET | `/fleet/buses/{id}` | Full bus detail with all seat states |
| POST | `/fleet/buses/{id}/seats/{seat}/board` | Simulate seat pressure sensor (passenger sits) |
| POST | `/fleet/buses/{id}/seats/{seat}/leave` | Simulate sensor release (passenger stands) |
| POST | `/fleet/buses/{id}/seats/{seat}/validate` | Validate PNR or Pass ID for a seat |
| POST | `/ticketing/issue-ticket` | Issue a new mock KSRTC ticket |
| POST | `/ticketing/issue-pass` | Issue a new mock KSRTC pass (daily/monthly/student) |
| POST | `/ticketing/validate` | Check if a PNR/Pass is valid |
| GET | `/ticketing/sample-codes` | Get demo PNRs/Passes to test with |
| POST | `/simulate/tick` | Advance energy simulation (called by dashboard) |

Full interactive docs: **http://localhost:8000/docs**

---

## Seat States

| State | Colour | Meaning |
|-------|--------|---------|
| `idle` | Dark grey | Empty seat — socket OFF |
| `occupied_unverified` | Amber | Someone seated, no valid ticket yet — socket OFF |
| `charging` | Green ⚡ | Seated + valid ticket — socket ON |
| `fault` | Red | Hardware fault (rare, simulated for realism) |

---

## What's Simulated vs What's Real

| Component | In this project | In real deployment |
|-----------|----------------|-------------------|
| Seat pressure sensor | POST /board API call | Piezoelectric / FSR sensor under cushion |
| Socket relay control | State flag in memory | Microcontroller (ESP32/Arduino) GPIO pin |
| Ticket validation | In-memory mock DB | KSRTC API / QR scan / NFC tap |
| Energy measurement | Calculated estimate | INA219 current sensor |
| Data persistence | In-memory only | PostgreSQL / Redis |
| Auth | None (demo) | JWT + conductor PIN |

---

## Future Scope (Real Deployment)

- **Hardware layer**: ESP32 per seat row, I2C bus to central bus MCU, MQTT to backend
- **KSRTC API integration**: Real PNR/pass validation via KSRTC SWIFT/SARTHI system
- **Revenue model**: KSRTC charges ₹5–10/session or bundles into premium seats
- **Analytics**: Per-route usage heatmaps, energy cost tracking, ROI per bus
- **Safety**: Over-current protection, USB-PD negotiation, smoke detection cutoff
- **Offline mode**: Charging decisions cached on the MCU in case of connectivity drop

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, Pydantic v2, Uvicorn |
| Frontend | React 18 (CDN), Babel Standalone, vanilla CSS |
| Data | In-memory (Pydantic models) |
| Simulation | Python script with requests |

---

*Built as a software-simulated proof-of-concept for KSRTC Smart Bus initiative.*
*All passenger names, PNRs, and bus registrations are randomly generated.*
