"""
ChargeKaru — Live demo simulator
===================================
Run this alongside the backend to make the whole fleet feel "alive" for a
demo: passengers randomly board, occasionally forget to show a valid ticket
(so you can SEE the socket stay off), get verified, and eventually leave.

Usage:
    # In one terminal:
    uvicorn app.main:app --reload --port 8000

    # In another terminal:
    python simulate_journey.py

Then open frontend/dashboard.html in your browser and watch seats light up.
"""

import random
import time
import requests

API = "http://localhost:8000"


def get_buses():
    return requests.get(f"{API}/fleet/buses").json()


def get_bus_detail(bus_id):
    return requests.get(f"{API}/fleet/buses/{bus_id}").json()


def get_sample_codes():
    return requests.get(f"{API}/ticketing/sample-codes").json()


def board(bus_id, seat):
    requests.post(f"{API}/fleet/buses/{bus_id}/seats/{seat}/board")


def leave(bus_id, seat):
    requests.post(f"{API}/fleet/buses/{bus_id}/seats/{seat}/leave")


def validate(bus_id, seat, code):
    requests.post(f"{API}/fleet/buses/{bus_id}/seats/{seat}/validate", json={"code": code})


def tick():
    requests.post(f"{API}/simulate/tick")


def main():
    print("ChargeKaru live simulator starting...")
    print(f"Connecting to {API} ...")

    try:
        buses = get_buses()
    except requests.exceptions.ConnectionError:
        print("\n  Could not connect to backend.")
        print("  Start it first with: uvicorn app.main:app --reload --port 8000\n")
        return

    if not buses:
        print("No buses found in fleet. Did the backend seed correctly?")
        return

    print(f"Found {len(buses)} buses in the fleet. Simulation running — Ctrl+C to stop.\n")

    occupied_state = {}  # (bus_id, seat) -> bool

    try:
        while True:
            buses = get_buses()
            bus = random.choice(buses)
            bus_id = bus["bus_id"]
            detail = get_bus_detail(bus_id)
            seats = list(detail["seats"].keys())
            seat = random.choice(seats)
            key = (bus_id, seat)

            currently_occupied = occupied_state.get(key, False)

            if not currently_occupied:
                # Passenger boards
                board(bus_id, seat)
                print(f"[{bus['registration_number']}] Passenger sat at seat {seat}")

                # 75% of the time they have a valid ticket ready; 25% they fumble first (realistic!)
                codes = get_sample_codes()
                all_codes = codes["sample_pnrs"] + codes["sample_passes"]
                if random.random() < 0.75 and all_codes:
                    code = random.choice(all_codes)
                    time.sleep(0.4)
                    validate(bus_id, seat, code)
                    print(f"   -> Verified ticket {code}. Charging started.")
                else:
                    print(f"   -> No ticket shown yet. Socket stays OFF.")

                occupied_state[key] = True

            else:
                # Passenger leaves
                leave(bus_id, seat)
                print(f"[{bus['registration_number']}] Passenger left seat {seat}. Charging stopped.")
                occupied_state[key] = False

            tick()
            time.sleep(random.uniform(1.5, 3.0))

    except KeyboardInterrupt:
        print("\nSimulation stopped.")


if __name__ == "__main__":
    main()
