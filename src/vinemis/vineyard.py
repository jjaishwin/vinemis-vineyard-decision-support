"""Deterministic synthetic vineyard plant-passport registry generation.

Every plant gets a permanent RFID-style 14-digit identifier (its "plant
passport"), a WGS84 coordinate computed from the vineyard layout with the
0.8 m plant / 2.1 m row spacing used in the manuscript's field study, and
an electronic identity record (clone, rootstock, certification class,
health status, treatment history).  All values are synthetic; a fixed
seed makes regeneration byte-identical.
"""

from __future__ import annotations

import math
import random

SEED = 20260809

# Synthetic origin (invented demonstration site, not a real vineyard).
ORIGIN_LAT = 43.70000000
ORIGIN_LON = 11.20000000

# Planting geometry from the manuscript: 0.8 m between plants, 2.1 m
# between rows.  Blocks are separated by a 10 m service lane.
PLANT_SPACING_M = 0.8
ROW_SPACING_M = 2.1
BLOCK_GAP_M = 10.0
METERS_PER_DEG_LAT = 111_320.0

BLOCKS = [
    {"block": "A", "rows": 6, "plants_per_row": 20},
    {"block": "B", "rows": 4, "plants_per_row": 15},
]

# EU colored-label classes discussed in the manuscript.
CERTIFICATION_LABELS = {
    "basic": "white",
    "certified": "blue",
    "standard": "yellow",
}

_EID_PREFIX = "982000"  # 6-digit synthetic issuer prefix; +8-digit serial = 14 digits


def make_eid(serial: int) -> str:
    """Deterministic 14-digit plant eID, as stored by the RFID tag."""
    return f"{_EID_PREFIX}{serial:08d}"


def meters_to_degrees(east_m: float, north_m: float, at_lat: float = ORIGIN_LAT) -> tuple[float, float]:
    """Equirectangular offset -> (latitude, longitude), WGS84."""
    lat = ORIGIN_LAT + north_m / METERS_PER_DEG_LAT
    lon = ORIGIN_LON + east_m / (METERS_PER_DEG_LAT * math.cos(math.radians(at_lat)))
    return round(lat, 8), round(lon, 8)


def _treatments(serial: int) -> list[dict]:
    """Deterministic management history: fixed demo dates, no wall-clock."""
    treatments = []
    if serial % 2 == 0:
        treatments.append(
            {"date": "2026-03-20", "type": "agronomic", "operation": "winter pruning"}
        )
    if serial % 5 == 0:
        treatments.append(
            {"date": "2026-04-15", "type": "phytosanitary", "operation": "sulfur treatment"}
        )
    if serial % 9 == 0:
        treatments.append(
            {"date": "2026-05-10", "type": "phytosanitary", "operation": "copper treatment"}
        )
    treatments.sort(key=lambda t: t["date"])
    return treatments


def _health_status(rng: random.Random) -> str:
    draw = rng.random()
    if draw < 0.82:
        return "healthy"
    if draw < 0.94:
        return "monitor"
    return "treatment_required"


def _certification(rng: random.Random) -> str:
    draw = rng.random()
    if draw < 0.55:
        return "certified"
    if draw < 0.80:
        return "standard"
    return "basic"


def generate_registry(seed: int = SEED) -> dict:
    """Build the full synthetic registry as a JSON-serialisable dict."""
    rng = random.Random(seed)
    plants = []
    serial = 0
    block_offset_m = 0.0
    for block in BLOCKS:
        for row in range(1, block["rows"] + 1):
            for pos in range(1, block["plants_per_row"] + 1):
                serial += 1
                east_m = block_offset_m + (pos - 1) * PLANT_SPACING_M
                north_m = (row - 1) * ROW_SPACING_M
                lat, lon = meters_to_degrees(east_m, north_m)
                certification = _certification(rng)
                plants.append(
                    {
                        "plant_id": f"{block['block']}-R{row:02d}-P{pos:03d}",
                        "eid": make_eid(serial),
                        "block": block["block"],
                        "row": row,
                        "position_in_row": pos,
                        "latitude": lat,
                        "longitude": lon,
                        "variety": "Sangiovese",
                        "clone": "I-SS-F9-A5-48",
                        "rootstock": "1103 Paulsen",
                        "planting_year": 2007,
                        "certification": certification,
                        "certification_label": CERTIFICATION_LABELS[certification],
                        "health_status": _health_status(rng),
                        "treatments": _treatments(serial),
                    }
                )
        block_width = (block["plants_per_row"] - 1) * PLANT_SPACING_M
        block_offset_m += block_width + BLOCK_GAP_M
    return {
        "registry": "vinemis-synthetic-plant-passports",
        "coordinate_reference_system": "WGS84 (EPSG:4326)",
        "origin": {"latitude": ORIGIN_LAT, "longitude": ORIGIN_LON},
        "spacing_m": {"between_plants": PLANT_SPACING_M, "between_rows": ROW_SPACING_M},
        "plants": plants,
    }
