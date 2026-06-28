# ---------------------------------------------------------
# File: scratch/fetch_solar_flares.py
# Description: Download the live NOAA SWPC solar‑flare catalogue
#              and write it as a CSV compatible with the dashboard.
# ---------------------------------------------------------

import csv
import json
import sys
import time
from pathlib import Path

import requests

# ----------------------------------------------------------------------
# Configuration (adjust as needed)
# ----------------------------------------------------------------------
JSON_URL = "https://services.swpc.noaa.gov/json/edited_events.json"
OUTPUT_CSV = Path("../solar_flares_live.csv")   # placed in project root
SLEEP_SECONDS = None   # set to an int (e.g. 3600) for periodic refresh

# ----------------------------------------------------------------------
# Helper: map NOAA class string (e.g. "M3.5") to a numeric flux in W/m²
# ----------------------------------------------------------------------
def class_to_flux(cls: str) -> str:
    """Convert GOES class (A/B/C/M/X + number) to scientific‑notation flux."""
    if not cls or len(cls) < 2:
        return ""
    letter = cls[0].upper()
    try:
        number = float(cls[1:])
    except ValueError:
        return ""
    multipliers = {"A": 1e-8, "B": 1e-7, "C": 1e-6, "M": 1e-5, "X": 1e-4}
    return f"{multipliers.get(letter, 0) * number:.2e}"

# ----------------------------------------------------------------------
# Core: fetch JSON, filter, and write CSV
# ----------------------------------------------------------------------
def fetch_and_write() -> None:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fetching NOAA data …")
    resp = requests.get(JSON_URL, timeout=30)
    resp.raise_for_status()
    all_events = resp.json()

    # Keep only solar‑flare events (FLR)
    flares = [e for e in all_events if e.get("event_type") == "FLR"]
    print(f"  → {len(flares):,} flare records found")

    header = [
        "event_id",
        "date",
        "time_utc",
        "class",
        "peak_flux_wm2",
        "latitude",
        "longitude",
        "region",
        "duration_sec",
        "sunspot_area_msh",
        "associated_cme",
        "notes",
    ]
    rows = []
    for ev in flares:
        ev_id = f"{ev.get('source','NOAA')}_{ev.get('event_no','?')}"
        begin = ev.get("begin_time", "")
        date = begin[:10] if begin else ""
        time_utc = begin[11:19] if begin else ""
        flare_class = ev.get("region_type", "")
        flux = class_to_flux(flare_class)
        # Parse location like N12W45
        loc = ev.get("location", "")
        lat, lon = "", ""
        if loc:
            import re
            m = re.match(r"([NS])(\d+)([EW])(\d+)", loc)
            if m:
                lat = f"{'-' if m.group(1)=='S' else ''}{m.group(2)}"
                lon = f"{'-' if m.group(3)=='W' else ''}{m.group(4)}"
        region = ev.get("region_num", "")
        duration = ev.get("duration", "")
        area = ev.get("sunspot_area_hem", "0")
        cme_flag = 1 if ev.get("cme_associated") else 0
        notes = ev.get("event_notes", "")
        rows.append([
            ev_id,
            date,
            time_utc,
            flare_class,
            flux,
            lat,
            lon,
            region,
            duration,
            area,
            cme_flag,
            notes,
        ])
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"✅  CSV written to {OUTPUT_CSV} ({len(rows):,} rows)")

# ----------------------------------------------------------------------
# Entry point – optional looping mode
# ----------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--loop":
        try:
            SLEEP_SECONDS = int(sys.argv[2])
        except ValueError:
            sys.exit("Usage: --loop <seconds>")
        print(f"🔁  Running in loop mode – refresh every {SLEEP_SECONDS}s")
        while True:
            fetch_and_write()
            time.sleep(SLEEP_SECONDS)
    else:
        fetch_and_write()
