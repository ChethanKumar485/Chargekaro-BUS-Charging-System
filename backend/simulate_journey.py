"""
ChargeKaru — Journey Simulator
Auto-pilots passengers boarding, validating, and leaving across the whole fleet,
so the dashboards have live activity to show during a demo/presentation.

Run this in a second terminal while the FastAPI server is running:
    python simulate_journey.py
"""

import random
import time

import requests

BASE_URL = "http://localhost:8000"
BUS_IDS = [f"BUS-{i}" for i in range(1, 7)]
SEAT_LAYOUT = [f"{row}{col}" for row in "ABCDEFGHIJ" for col in (1, 2)]

NAMES = [
    "Ramesh Gowda", "Sandhya Rao", "Mohammed Imran", "Anjali Shetty",
    "Pradeep Kumar", "Lakshmi Devi", "Naveen Reddy", "Kavya Hegde",
    "Suresh Patil", "Divya Bhat", "Arjun Naik", "Fathima Begum",
]


def issue_random_ticket(bus_id: str, seat_no: str) -> str | None:
    try:
        resp = requests.post(
            f"{BASE_URL}/ticketing/issue-ticket",
            json={
                "bus_id": bus_id,
                "seat_no": seat_no,
                "passenger_name": random.choice(NAMES),
                "hours_valid": 6,
            },
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()["pnr"]
    except Exception as e:
        print(f"  [!] ticket issue failed: {e}")
        return None


def board(bus_id: str, seat_no: str):
    requests.post(f"{BASE_URL}/fleet/buses/{bus_id}/seats/{seat_no}/board", timeout=5)


def leave(bus_id: str, seat_no: str):
    requests.post(f"{BASE_URL}/fleet/buses/{bus_id}/seats/{seat_no}/leave", timeout=5)


def validate(bus_id: str, seat_no: str, code: str):
    requests.post(
        f"{BASE_URL}/fleet/buses/{bus_id}/seats/{seat_no}/validate",
        json={"code": code},
        timeout=5,
    )


def tick(seconds: float = 2.0):
    requests.post(f"{BASE_URL}/simulate/tick", params={"seconds": seconds}, timeout=5)


def simulate_passenger_cycle(bus_id: str, seat_no: str):
    """Board -> (sometimes) validate -> charge for a while -> leave."""
    board(bus_id, seat_no)
    print(f"  {bus_id} {seat_no}: passenger seated")

    # 85% of passengers have a valid ticket — small % are unverified to show amber state
    if random.random() < 0.85:
        code = issue_random_ticket(bus_id, seat_no)
        if code:
            time.sleep(random.uniform(0.3, 1.0))  # delay before verification, like real QR scan
            validate(bus_id, seat_no, code)
            print(f"  {bus_id} {seat_no}: verified with {code} -> charging")
    else:
        print(f"  {bus_id} {seat_no}: no ticket presented (stays unverified)")


def main():
    print("=" * 60)
    print("ChargeKaru Journey Simulator — auto-piloting the fleet")
    print("=" * 60)

    try:
        requests.get(f"{BASE_URL}/", timeout=5)
    except Exception:
        print(f"[!] Cannot reach backend at {BASE_URL}. Start it first with:")
        print("    uvicorn app.main:app --reload --port 8000")
        return

    active: dict[tuple[str, str], float] = {}  # (bus_id, seat_no) -> leave_at timestamp

    print("\nRunning continuous simulation. Press Ctrl+C to stop.\n")
    try:
        while True:
            now = time.time()

            # Randomly board a few new passengers each loop
            for _ in range(random.randint(1, 3)):
                bus_id = random.choice(BUS_IDS)
                seat_no = random.choice(SEAT_LAYOUT)
                key = (bus_id, seat_no)
                if key not in active:
                    simulate_passenger_cycle(bus_id, seat_no)
                    active[key] = now + random.uniform(8, 20)

            # Release passengers whose ride segment ended
            for key in list(active.keys()):
                if now >= active[key]:
                    bus_id, seat_no = key
                    leave(bus_id, seat_no)
                    print(f"  {bus_id} {seat_no}: passenger left -> socket OFF")
                    del active[key]

            tick(2.0)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nSimulation stopped.")


if __name__ == "__main__":
    main()
