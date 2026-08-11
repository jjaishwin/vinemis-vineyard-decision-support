"""Registry persistence: JSON and SQLite backends (standard library only)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS registry_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plants (
    plant_id TEXT PRIMARY KEY,
    eid TEXT NOT NULL UNIQUE,
    block TEXT NOT NULL,
    row INTEGER NOT NULL,
    position_in_row INTEGER NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    variety TEXT NOT NULL,
    clone TEXT NOT NULL,
    rootstock TEXT NOT NULL,
    planting_year INTEGER NOT NULL,
    certification TEXT NOT NULL,
    certification_label TEXT NOT NULL,
    health_status TEXT NOT NULL,
    treatments_json TEXT NOT NULL
);
"""

_META_KEYS = (
    "registry",
    "coordinate_reference_system",
    "origin",
    "spacing_m",
)


def save_json(registry: dict, path: Path | str) -> Path:
    """Write the registry as deterministic, pretty-printed JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_json(path: Path | str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_sqlite(registry: dict, path: Path | str) -> Path:
    """Store the registry in a single-file SQLite database."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    with sqlite3.connect(path) as conn:
        conn.executescript(_SCHEMA)
        for key in _META_KEYS:
            conn.execute(
                "INSERT INTO registry_meta (key, value) VALUES (?, ?)",
                (key, json.dumps(registry[key], sort_keys=True)),
            )
        conn.executemany(
            """
            INSERT INTO plants (
                plant_id, eid, block, row, position_in_row, latitude, longitude,
                variety, clone, rootstock, planting_year, certification,
                certification_label, health_status, treatments_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    p["plant_id"], p["eid"], p["block"], p["row"], p["position_in_row"],
                    p["latitude"], p["longitude"], p["variety"], p["clone"],
                    p["rootstock"], p["planting_year"], p["certification"],
                    p["certification_label"], p["health_status"],
                    json.dumps(p["treatments"], sort_keys=True),
                )
                for p in registry["plants"]
            ],
        )
    return path


def load_sqlite(path: Path | str) -> dict:
    """Rebuild the registry dict from a SQLite file (row order stable)."""
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        meta = {
            row["key"]: json.loads(row["value"])
            for row in conn.execute("SELECT key, value FROM registry_meta")
        }
        plants = []
        for row in conn.execute(
            "SELECT * FROM plants ORDER BY block, row, position_in_row"
        ):
            plants.append(
                {
                    "plant_id": row["plant_id"],
                    "eid": row["eid"],
                    "block": row["block"],
                    "row": row["row"],
                    "position_in_row": row["position_in_row"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "variety": row["variety"],
                    "clone": row["clone"],
                    "rootstock": row["rootstock"],
                    "planting_year": row["planting_year"],
                    "certification": row["certification"],
                    "certification_label": row["certification_label"],
                    "health_status": row["health_status"],
                    "treatments": json.loads(row["treatments_json"]),
                }
            )
    return {**meta, "plants": plants}
