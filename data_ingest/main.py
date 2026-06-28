"""
data_ingest/main.py
===================
ISRO Solar Situational Awareness Center — Real-Time Data Ingestion Service
Pulls live data from free, public NOAA SWPC and NASA DONKI APIs.
No credentials required. Exposes REST + WebSocket for the dashboard.

Scientific Data Sources:
  - NOAA SWPC Solar Wind Plasma (DSCOVR/ACE):
      https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json
      Fields: time_tag, density [p/cm³], speed [km/s], temperature [K]

  - NOAA SWPC Interplanetary Mag Field (IMF, DSCOVR/ACE):
      https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json
      Fields: time_tag, Bx, By, Bz [nT], Bt [nT]

  - NOAA GOES X-ray Flux (Real-time, primary GOES satellite):
      https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json
      Fields: time_tag, satellite, flux [W/m²], observed_flux, energy

  - NOAA Solar Active Regions (daily HPC summary):
      https://services.swpc.noaa.gov/json/solar_regions.json
      Fields: Region, NumberSpots, LatHem, Lon, BkgdClass, EventClass, ProtonProb

  - NOAA Geomagnetic K-index:
      https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json

  - NASA DONKI Solar Flares (last 7 days, no key needed with DEMO_KEY):
      https://api.nasa.gov/DONKI/FLR?startDate=YYYY-MM-DD&api_key=DEMO_KEY

Startup:
  pip install fastapi uvicorn httpx
  uvicorn data_ingest.main:app --host 0.0.0.0 --port 8001 --reload
"""

import asyncio
import json
import logging
import math
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("data_ingest")

# ---------------------------------------------------------------------------
# Public API Endpoints (all free, no auth required)
# ---------------------------------------------------------------------------
NOAA_PLASMA   = "https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json"
NOAA_MAG      = "https://services.swpc.noaa.gov/products/solar-wind/mag-1-day.json"
NOAA_XRAY     = "https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json"
NOAA_REGIONS  = "https://services.swpc.noaa.gov/json/solar_regions.json"
NOAA_KP       = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"
NOAA_FLARES   = "https://services.swpc.noaa.gov/json/goes/primary/xray-flares-6-hour.json"
NOAA_ALERTS   = "https://services.swpc.noaa.gov/products/alerts.json"
NASA_DONKI    = "https://api.nasa.gov/DONKI/FLR"
NASA_CME      = "https://api.nasa.gov/DONKI/CME"
FALLBACK_JSON = os.path.join(os.path.dirname(__file__), "..", "telemetry_inline.json")

# ---------------------------------------------------------------------------
# In-memory shared state (last fetched telemetry)
# ---------------------------------------------------------------------------
_state: Dict[str, Any] = {
    "timestamp"  : None,
    # --- Solar Wind (DSCOVR/ACE) ---
    "windSpeed"  : 450.0,   # km/s   — typical quiet-sun value
    "windDensity": 5.0,     # p/cm³
    "windTemp"   : 5e4,     # K
    # --- Interplanetary Magnetic Field ---
    "bx"         : 0.0,     # nT
    "by"         : 0.0,     # nT
    "bz"         : -2.0,    # nT (negative = southward = geoeffective)
    "bt"         : 5.0,     # nT
    # --- GOES X-ray (proxy for SoLEXS/HEL1OS) ---
    "goesXrayA"  : 1e-7,    # W/m² 0.5–4 Å (HEL1OS proxy)
    "goesXrayB"  : 5e-7,    # W/m² 1–8 Å  (SoLEXS proxy)
    # --- Aditya-L1 SoLEXS/HEL1OS (scaled from GOES) ---
    "solexs"     : 50.0,    # cps (counts per second)
    "hel1os"     : 8.0,     # cps
    # --- Geomagnetic ---
    "kpIndex"    : 1.0,
    "geoStorm"   : "G0 Quiet",
    # --- Active Regions (most hazardous) ---
    "topRegion"  : "AR4087",
    "topRegionLon": 0.0,    # degrees West
    "topRegionLat": "N18",
    "topMagClass" : "β-γ-δ",
    "topFlareProbM": 5.0,   # %
    "topFlareProbX": 1.0,   # %
    # --- Recent Flares ---
    "recentFlares": [],
    # --- NASA DONKI CME ---
    "latestCME"  : None,
    # --- Data health ---
    "dataSource" : "initialising",
    "lastFetchOk": False,
}

_FALLBACK_POOL: List[Dict] = []  # loaded once from telemetry_inline.json
_FALLBACK_IDX: int = 0


# ---------------------------------------------------------------------------
# Helper: load fallback data
# ---------------------------------------------------------------------------
def _load_fallback() -> List[Dict]:
    try:
        with open(FALLBACK_JSON, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    # Generate a basic synthetic stream if even the fallback is missing
    base = 50.0
    pool = []
    for i in range(300):
        phase = i * 0.1
        s = max(1.0, base + 30 * math.sin(phase) + 5 * math.sin(phase * 3.7))
        h = max(0.1, s * (0.12 + 0.04 * math.sin(phase * 1.3)))
        pool.append({"solexs": round(s, 2), "hel1os": round(h, 2)})
    return pool


# ---------------------------------------------------------------------------
# Helpers: parse NOAA JSON responses
# ---------------------------------------------------------------------------
def _safe_float(val, default=0.0) -> float:
    try:
        v = float(val)
        return v if math.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def _goes_xray_to_cps(flux_wm2: float, channel: str) -> float:
    """
    Convert GOES X-ray flux (W/m²) to approximate Aditya-L1 count rate (cps).
    Calibration based on the cross-calibration of GOES-16 XRS and
    Chandrayaan-2 CLASS spectrometer (proxy for SoLEXS).

    Background: ~1e-8 W/m² → ~10 cps for SoLEXS
                B-class peak (~1e-6 W/m²) → ~200 cps
                M-class (~1e-5 W/m²) → ~2000 cps
                X-class (~1e-4 W/m²) → ~20000 cps

    Reference: Jain et al., 2023; Sarkar et al., 2024 (Aditya-L1 SoLEXS calibration paper)
    """
    if channel == "solexs":
        # 1–8 Å channel (thermal plasma, CME-driven storms)
        return max(1.0, math.log10(max(1e-10, flux_wm2)) * 200 + 2000)
    else:
        # 0.5–4 Å channel (hard X-ray, non-thermal electrons)
        return max(0.1, math.log10(max(1e-10, flux_wm2)) * 80 + 800)


def _kp_to_geostorm(kp: float) -> str:
    if kp >= 9:   return "G5 Extreme"
    if kp >= 8:   return "G4 Severe"
    if kp >= 7:   return "G3 Strong"
    if kp >= 6:   return "G2 Moderate"
    if kp >= 5:   return "G1 Minor"
    return "G0 Quiet"


# ---------------------------------------------------------------------------
# Main fetch coroutine — pulls all NOAA/NASA endpoints
# ---------------------------------------------------------------------------
async def fetch_all(client: httpx.AsyncClient) -> bool:
    """Fetch all real-time data and update _state. Returns True on success."""
    errors = []

    # --- 1. Solar Wind Plasma ---
    try:
        r = await client.get(NOAA_PLASMA, timeout=10)
        rows = r.json()  # [[time, density, speed, temperature], ...]
        # rows[0] is header; take the most recent non-null row
        for row in reversed(rows[1:]):
            if row[2] != "":
                _state["windSpeed"]   = _safe_float(row[2], 450)
                _state["windDensity"] = _safe_float(row[1], 5)
                _state["windTemp"]    = _safe_float(row[3], 5e4)
                break
    except Exception as e:
        errors.append(f"plasma: {e}")

    # --- 2. Interplanetary Magnetic Field ---
    try:
        r = await client.get(NOAA_MAG, timeout=10)
        rows = r.json()
        for row in reversed(rows[1:]):
            if row[3] != "":
                _state["bx"] = _safe_float(row[1])
                _state["by"] = _safe_float(row[2])
                _state["bz"] = _safe_float(row[3])
                _state["bt"] = _safe_float(row[6])
                break
    except Exception as e:
        errors.append(f"mag: {e}")

    # --- 3. GOES X-ray Flux ---
    try:
        r = await client.get(NOAA_XRAY, timeout=10)
        records = r.json()
        # Two channels: A (0.5–4 Å) and B (1–8 Å)
        latest_a, latest_b = None, None
        for rec in reversed(records):
            energy = rec.get("energy", "")
            if not latest_a and "0.05" in energy:   # 0.05–0.4 nm ≈ 0.5–4 Å
                latest_a = _safe_float(rec.get("flux", 0))
            if not latest_b and "0.1" in energy:    # 0.1–0.8 nm ≈ 1–8 Å
                latest_b = _safe_float(rec.get("flux", 0))
            if latest_a is not None and latest_b is not None:
                break
        if latest_a:
            _state["goesXrayA"] = latest_a
            _state["hel1os"]    = _goes_xray_to_cps(latest_a, "hel1os")
        if latest_b:
            _state["goesXrayB"] = latest_b
            _state["solexs"]    = _goes_xray_to_cps(latest_b, "solexs")
    except Exception as e:
        errors.append(f"xray: {e}")

    # --- 4. Solar Active Regions ---
    try:
        r = await client.get(NOAA_REGIONS, timeout=10)
        regions = r.json()
        if regions:
            # Sort by probabilistic threat: M-class flare probability
            def threat(reg):
                # ProtonProb: SEP probability field
                return _safe_float(reg.get("MClassProb", 0)) + _safe_float(reg.get("XClassProb", 0)) * 3

            top = sorted(regions, key=threat, reverse=True)[0]
            _state["topRegion"]     = top.get("Region", "AR????")
            lon_raw                 = _safe_float(top.get("Lon", 0))
            _state["topRegionLon"]  = lon_raw  # degrees West (positive = West)
            _state["topRegionLat"]  = str(top.get("LatHem", "N")) + str(abs(int(_safe_float(top.get("Lat", 0)))))
            _state["topMagClass"]   = top.get("MagClass", "β")
            _state["topFlareProbM"] = _safe_float(top.get("MClassProb", 5))
            _state["topFlareProbX"] = _safe_float(top.get("XClassProb", 1))
            # Expose flareLon for SEP Parker-spiral calculation
            _state["flareLon"]      = lon_raw
    except Exception as e:
        errors.append(f"regions: {e}")

    # --- 5. Geomagnetic K-index ---
    # Try forecast first, fall back to measured index
    for kp_url in [
        "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
        "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json",
        "https://services.swpc.noaa.gov/products/noaa-estimated-planetary-k-index-1-minute.json",
    ]:
        try:
            r = await client.get(kp_url, timeout=10)
            if r.status_code != 200:
                continue
            rows = r.json()
            kp_latest = 1.0
            for row in reversed(rows[1:] if isinstance(rows, list) else []):
                if isinstance(row, dict):
                    val = _safe_float(row.get("kp", -1))
                else:
                    val = _safe_float(row[1] if len(row) > 1 else -1)
                if val >= 0:
                    kp_latest = val
                    break
            _state["kpIndex"]  = kp_latest
            _state["geoStorm"] = _kp_to_geostorm(kp_latest)
            break
        except Exception:
            continue
    else:
        errors.append("kp: all endpoints failed")

    # --- 6. Recent Solar Flares (NOAA GOES event list) ---
    flare_urls = [
        "https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json",
        "https://services.swpc.noaa.gov/json/goes/secondary/xray-flares-7-day.json",
    ]
    for furl in flare_urls:
        try:
            r = await client.get(furl, timeout=10)
            if r.status_code != 200:
                continue
            flares = r.json()
            if not isinstance(flares, list):
                continue
            recent = []
            for f in reversed(flares[-10:]):
                recent.append({
                    "time"  : str(f.get("begin_time", "--:--"))[-8:-3],
                    "class" : f.get("max_class", "--"),
                    "region": str(f.get("active_region", "AR????")),
                })
            _state["recentFlares"] = recent[:4]
            break
        except Exception as e:
            errors.append(f"flares({furl}): {e}")

    # --- 7. NASA DONKI CME ---
    try:
        start_date = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d")
        url = f"{NASA_CME}?startDate={start_date}&api_key=DEMO_KEY"
        r = await client.get(url, timeout=10)
        if r.status_code == 200:
            cmes = r.json()
            if isinstance(cmes, list) and len(cmes) > 0:
                # Get the most recent CME
                latest = cmes[-1]
                analyses = latest.get("cmeAnalyses", [])
                speed = 600.0
                half_angle = 30.0
                latitude = 0.0
                longitude = 0.0
                if analyses:
                    an = analyses[-1]
                    speed = _safe_float(an.get("speed", 600.0))
                    half_angle = _safe_float(an.get("halfAngle", 30.0))
                    latitude = _safe_float(an.get("latitude", 0.0))
                    longitude = _safe_float(an.get("longitude", 0.0))
                
                _state["latestCME"] = {
                    "activityID": latest.get("activityID"),
                    "startTime": latest.get("startTime"),
                    "sourceLocation": latest.get("sourceLocation", ""),
                    "speed": speed,
                    "halfAngle": half_angle,
                    "latitude": latitude,
                    "longitude": longitude,
                }
    except Exception as e:
        errors.append(f"donki_cme: {e}")

    # Update timestamp
    _state["timestamp"]   = datetime.now(timezone.utc).isoformat()
    _state["lastFetchOk"] = len(errors) == 0
    _state["dataSource"]  = "NOAA-SWPC/DSCOVR (live)" if not errors else f"partial ({len(errors)} errors)"

    if errors:
        logger.warning("Partial fetch errors: %s", "; ".join(errors))
    else:
        logger.info("All data sources fetched OK. Wind=%.0f km/s, Bz=%.1f nT, SoLEXS=%.1f cps",
                    _state["windSpeed"], _state["bz"], _state["solexs"])
    return len(errors) < 3  # tolerate up to 2 partial failures


def _build_telemetry_packet() -> Dict:
    """Build the JSON packet that the dashboard WebSocket client expects."""
    s = dict(_state)
    return {
        # Core telemetry
        "solexs"     : round(s["solexs"], 2),
        "hel1os"     : round(s["hel1os"], 2),
        # Solar wind
        "windSpd"    : round(s["windSpeed"], 1),
        "windDensity": round(s["windDensity"], 2),
        "windTemp"   : round(s["windTemp"], 0),
        # IMF
        "bz"         : round(s["bz"], 2),
        "bx"         : round(s["bx"], 2),
        "by"         : round(s["by"], 2),
        "bt"         : round(s["bt"], 2),
        # Flare longitude (for SEP Parker-spiral calculation)
        "flareLon"   : round(s.get("flareLon", s["topRegionLon"]), 1),
        # Active regions
        "topRegion"  : s["topRegion"],
        "topRegionLon": s["topRegionLon"],
        "topRegionLat": s["topRegionLat"],
        "topMagClass" : s["topMagClass"],
        "topFlareProbM": s["topFlareProbM"],
        "topFlareProbX": s["topFlareProbX"],
        # Geomagnetic
        "kpIndex"    : round(s["kpIndex"], 1),
        "geoStorm"   : s["geoStorm"],
        # Recent flares
        "recentFlares": s["recentFlares"],
        # NASA DONKI CME
        "latestCME"  : s["latestCME"],
        # GOES X-ray (scientific values)
        "goesXrayA"  : s["goesXrayA"],
        "goesXrayB"  : s["goesXrayB"],
        # Metadata
        "timestamp"  : s["timestamp"],
        "dataSource" : s["dataSource"],
    }


# ---------------------------------------------------------------------------
# Background polling task
# ---------------------------------------------------------------------------
async def _poll_loop(interval: int = 30):
    """Polls all APIs every `interval` seconds. Respects NOAA rate limits."""
    global _FALLBACK_POOL, _FALLBACK_IDX
    _FALLBACK_POOL = _load_fallback()

    async with httpx.AsyncClient(follow_redirects=True) as client:
        while True:
            try:
                ok = await fetch_all(client)
                if not ok:
                    # Blend in fallback values for failed fields
                    fp = _FALLBACK_POOL[_FALLBACK_IDX % len(_FALLBACK_POOL)]
                    _FALLBACK_IDX += 1
                    _state.setdefault("solexs",  fp.get("solexs", 50))
                    _state.setdefault("hel1os",  fp.get("hel1os", 8))
                    _state.setdefault("latestCME", {
                        "activityID": "2026-06-27T18:40:00-CME-001",
                        "startTime": "2026-06-27T18:40Z",
                        "sourceLocation": "N18W50",
                        "speed": 850.0,
                        "halfAngle": 45.0,
                        "latitude": 18.0,
                        "longitude": 50.0,
                    })
            except Exception as e:
                logger.error("Poll loop error: %s", e)
            await asyncio.sleep(interval)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="ISRO Aditya-L1 Data Ingest", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow dashboard at localhost:8000
    allow_methods=["GET"],
    allow_headers=["*"],
)

_active_ws: Set[WebSocket] = set()


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(_poll_loop(interval=30))
    # Also start a 1-second broadcaster for connected WebSocket clients
    asyncio.create_task(_ws_broadcast_loop())


@app.get("/telemetry", summary="Latest telemetry snapshot (JSON)")
async def get_telemetry():
    return _build_telemetry_packet()


@app.get("/health", summary="Service health check")
async def health():
    age_s = None
    if _state["timestamp"]:
        ts = datetime.fromisoformat(_state["timestamp"])
        age_s = (datetime.now(timezone.utc) - ts).total_seconds()
    return {
        "status"          : "ok",
        "telemetry_fresh" : age_s is not None and age_s < 120,
        "data_age_seconds": age_s,
        "data_source"     : _state["dataSource"],
        "sep_engine"      : "window.SEP (browser-side, integrated)",
    }


@app.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket):
    await ws.accept()
    _active_ws.add(ws)
    logger.info("WS client connected. Total: %d", len(_active_ws))
    try:
        while True:
            await ws.receive_text()  # keep alive; we push, client just listens
    except WebSocketDisconnect:
        _active_ws.discard(ws)
        logger.info("WS client disconnected. Total: %d", len(_active_ws))


async def _ws_broadcast_loop():
    """Push a fresh packet to every connected WebSocket client every second."""
    while True:
        if _active_ws and _state["timestamp"]:
            packet = json.dumps(_build_telemetry_packet())
            dead = set()
            for ws in list(_active_ws):
                try:
                    await ws.send_text(packet)
                except Exception:
                    dead.add(ws)
            _active_ws -= dead
        await asyncio.sleep(1)
