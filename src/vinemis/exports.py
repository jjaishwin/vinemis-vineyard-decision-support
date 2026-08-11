"""Interoperable exports: GeoJSON and KML placemarks linked to plant eIDs.

The KML export mirrors the manuscript's Google Earth integration: each
plant is a Placemark whose description carries the eID and passport
attributes, so users can navigate between spatial and attribute data.
"""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

_KML_STYLE = {
    "healthy": "ff00a838",      # green (aabbggrr)
    "monitor": "ff00c8ff",      # amber
    "treatment_required": "ff3838d8",  # red
}


def to_geojson(registry: dict) -> dict:
    """FeatureCollection with one Point feature per plant passport."""
    features = []
    for plant in registry["plants"]:
        properties = {k: v for k, v in plant.items() if k not in {"latitude", "longitude"}}
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    # GeoJSON is [longitude, latitude], WGS84.
                    "coordinates": [plant["longitude"], plant["latitude"]],
                },
                "properties": properties,
            }
        )
    return {
        "type": "FeatureCollection",
        "name": registry["registry"],
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "features": features,
    }


def write_geojson(registry: dict, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(to_geojson(registry), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def _kml_placemark(plant: dict) -> str:
    description = (
        f"eID: {plant['eid']}\n"
        f"Variety: {plant['variety']} (clone {plant['clone']})\n"
        f"Rootstock: {plant['rootstock']}\n"
        f"Certification: {plant['certification']} ({plant['certification_label']} label)\n"
        f"Health status: {plant['health_status']}\n"
        f"Treatments: {len(plant['treatments'])}"
    )
    color = _KML_STYLE.get(plant["health_status"], "ffffffff")
    return f"""    <Placemark>
      <name>{escape(plant['plant_id'])}</name>
      <description>{escape(description)}</description>
      <Style><IconStyle><color>{color}</color></IconStyle></Style>
      <ExtendedData>
        <Data name="eid"><value>{escape(plant['eid'])}</value></Data>
        <Data name="health_status"><value>{escape(plant['health_status'])}</value></Data>
        <Data name="certification"><value>{escape(plant['certification'])}</value></Data>
      </ExtendedData>
      <Point>
        <coordinates>{plant['longitude']},{plant['latitude']},0</coordinates>
      </Point>
    </Placemark>"""


def to_kml(registry: dict) -> str:
    """KML 2.2 document with one placemark per plant, grouped by block."""
    blocks: dict[str, list[dict]] = {}
    for plant in registry["plants"]:
        blocks.setdefault(plant["block"], []).append(plant)
    folders = []
    for block in sorted(blocks):
        placemarks = "\n".join(_kml_placemark(p) for p in blocks[block])
        folders.append(f"  <Folder>\n    <name>Block {escape(block)}</name>\n{placemarks}\n  </Folder>")
    body = "\n".join(folders)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        "<Document>\n"
        f"  <name>{escape(registry['registry'])}</name>\n"
        f"  <description>Synthetic virtual vineyard; CRS {escape(registry['coordinate_reference_system'])}</description>\n"
        f"{body}\n"
        "</Document>\n"
        "</kml>\n"
    )


def write_kml(registry: dict, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_kml(registry), encoding="utf-8")
    return path
