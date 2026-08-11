# VineMIS: Geotagged Plant Passports for Vineyard Decision Support

This repository is a small, dependency-free Python demonstration of the VineMIS concept described in the manuscript: a **synthetic plant-level asset registry** ("virtual vineyard") in which every vine carries a permanent RFID-style 14-digit electronic identity (eID) fused with a **deterministic WGS84 coordinate** computed from the vineyard layout (0.8 m plant / 2.1 m row spacing, as in the paper's field study), persisted to **JSON or SQLite**, exported to **GeoJSON and KML** (placemarks linked to eIDs, mirroring the paper's Google Earth integration), and rolled up into a **decision-support summary** with tasking and a traceability audit.

## Paper link

No public venue, DOI, or URL for this manuscript could be verified as of 2026-08-09. The provenance source is the uploaded manuscript PDF (`VineMIS__Geotagged_Plant_Passports_for_Vineyard_Decision_Support.pdf`, author shown as "Jayant Jaishwin Shanmugam kavitha" — lowercase family name in the PDF). No metadata beyond the PDF itself is asserted anywhere in this repository.

## What this repository demonstrates

- **Plant passports:** 180 synthetic vines across two blocks, each with plant id, 14-digit eID, clone `I-SS-F9-A5-48`, rootstock `1103 Paulsen`, EU colored-label certification class (white/blue/yellow), health status, and a deterministic treatment history.
- **Deterministic geotagging:** coordinates derived from layout geometry around an invented origin — regeneration is byte-identical (fixed seed, no wall-clock values).
- **Storage backends:** `plant_passports.json` and an equivalent `plant_passports.sqlite` (stdlib `sqlite3`), with lossless round-trips.
- **Interoperable exports:** `virtual_vineyard.geojson` (FeatureCollection, CRS84) and `virtual_vineyard.kml` (per-block folders, health-colored placemarks carrying eID attributes).
- **Decision support:** health/certification breakdowns, per-block counts, targeted-treatment and monitoring task lists, and an eID traceability audit.
- **Lookup:** `vinemis lookup A-R03-P012` (or any 14-digit eID) prints the full plant passport — the "retrieve plant information" workflow at demo scale.

This is an educational demo of the manuscript's concepts on synthetic data; it does not reproduce the GeoGis software, hardware field trial, or the paper's empirical accuracy/timing results.

## Quickstart

```bash
cd vinemis-vineyard-decision-support
PYTHONPATH=src python -m vinemis --help
PYTHONPATH=src python -m vinemis demo
PYTHONPATH=src python -m unittest discover -s tests -v
```

If installed (`pip install .`), the console script `vinemis` provides the same CLI. Subcommands: `generate`, `export`, `summary`, `lookup`, `demo`.

## Example command and expected output

```bash
$ PYTHONPATH=src python -m vinemis demo
Wrote data/synthetic/plant_passports.json (180 plants)
Wrote data/synthetic/plant_passports.sqlite
Wrote data/synthetic/virtual_vineyard.geojson (180 features)
Wrote data/synthetic/virtual_vineyard.kml (180 placemarks)
VineMIS decision-support summary
================================
Registry: vinemis-synthetic-plant-passports
Plants: 180

Health status:
  healthy: 138
  monitor: 33
  treatment_required: 9
Certification classes:
  basic: 33
  certified: 101
  standard: 46
Blocks:
  Block A: 120 plants {'healthy': 87, 'monitor': 26, 'treatment_required': 7}
  Block B: 60 plants {'healthy': 51, 'monitor': 7, 'treatment_required': 2}

Suggested tasks:
  - Targeted treatment: 9 plants flagged treatment_required
  - Monitoring round: 33 plants on the watch list
  - Compliance audit: 101 certified (blue-label) plants with complete eID traceability

Traceability audit: 180/180 plants with valid 14-digit eIDs, 0 duplicates, 180 geotagged.

Wrote data/synthetic/decision_summary.json
```

## Repository structure

```text
vinemis-vineyard-decision-support/
├── README.md
├── CITATION.cff
├── LICENSE
├── pyproject.toml
├── data/
│   └── synthetic/
│       ├── plant_passports.json      # generated registry (JSON backend)
│       ├── plant_passports.sqlite    # generated registry (SQLite backend)
│       ├── virtual_vineyard.geojson  # generated GeoJSON export
│       ├── virtual_vineyard.kml      # generated KML export
│       └── decision_summary.json     # generated decision-support summary
├── src/
│   └── vinemis/
│       ├── __init__.py
│       ├── __main__.py               # python -m entry point
│       ├── cli.py                    # argparse CLI + console script
│       ├── vineyard.py               # deterministic registry generator
│       ├── storage.py                # JSON + SQLite persistence
│       ├── exports.py                # GeoJSON + KML writers
│       └── decision.py               # decision-support summary
└── tests/
    └── test_smoke.py
```

## Data/privacy note

All data is synthetic: the site origin, vineyard layout, eIDs, health statuses, and treatment records are invented and generated with a fixed seed. No real vineyard, grower, certifier, or location data is included, and no personal, confidential, proprietary, or credential data appears in this repository.

## How to cite

Cite the demo software via `CITATION.cff` (GitHub renders it automatically). The manuscript has no verified year, venue, DOI, or URL; the BibTeX below deliberately omits those fields:

```bibtex
@misc{kavitha_vinemis,
  author = {Shanmugam Kavitha, Jayant Jaishwin},
  title  = {VineMIS: Geotagged Plant Passports for Vineyard Decision Support},
  note   = {Uploaded manuscript; no public venue, DOI, or publication date verified as of 2026-08-09}
}
```

See `CITATION.cff` for the machine-readable version, including the `preferred-citation` entry.

## License

MIT — see `LICENSE`.
