"""Command-line interface for the VineMIS synthetic demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .decision import render_text, summarize
from .exports import write_geojson, write_kml
from .storage import load_json, load_sqlite, save_json, save_sqlite
from .vineyard import SEED, generate_registry

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"
DEFAULT_JSON = DEFAULT_DATA_DIR / "plant_passports.json"
DEFAULT_SQLITE = DEFAULT_DATA_DIR / "plant_passports.sqlite"
DEFAULT_GEOJSON = DEFAULT_DATA_DIR / "virtual_vineyard.geojson"
DEFAULT_KML = DEFAULT_DATA_DIR / "virtual_vineyard.kml"
DEFAULT_SUMMARY = DEFAULT_DATA_DIR / "decision_summary.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vinemis",
        description=(
            "VineMIS demo: synthetic geotagged plant passports with JSON/SQLite "
            "storage, GeoJSON/KML exports, and a decision-support summary."
        ),
    )
    sub = parser.add_subparsers(dest="command")

    p_gen = sub.add_parser("generate", help="build the synthetic registry (JSON + SQLite)")
    p_gen.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    p_gen.add_argument("--seed", type=int, default=SEED)

    p_exp = sub.add_parser("export", help="write GeoJSON and KML from a stored registry")
    p_exp.add_argument("--registry", type=Path, default=DEFAULT_JSON,
                       help="registry JSON file (default: data/synthetic/plant_passports.json)")
    p_exp.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)

    p_sum = sub.add_parser("summary", help="print + save the decision-support summary")
    p_sum.add_argument("--registry", type=Path, default=DEFAULT_JSON)
    p_sum.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)

    p_lookup = sub.add_parser("lookup", help="print one plant passport by plant id or eID")
    p_lookup.add_argument("identifier", help="plant_id (e.g. A-R03-P012) or 14-digit eID")
    p_lookup.add_argument("--registry", type=Path, default=DEFAULT_JSON)

    sub.add_parser("demo", help="generate, export, summarize (all defaults)")
    return parser


def _load_registry(path: Path) -> dict:
    if path.suffix == ".sqlite":
        return load_sqlite(path)
    return load_json(path)


def _cmd_generate(args: argparse.Namespace) -> int:
    registry = generate_registry(seed=args.seed)
    json_path = save_json(registry, args.data_dir / DEFAULT_JSON.name)
    sqlite_path = save_sqlite(registry, args.data_dir / DEFAULT_SQLITE.name)
    print(f"Wrote {json_path} ({len(registry['plants'])} plants)")
    print(f"Wrote {sqlite_path}")
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    registry = _load_registry(args.registry)
    geojson_path = write_geojson(registry, args.data_dir / DEFAULT_GEOJSON.name)
    kml_path = write_kml(registry, args.data_dir / DEFAULT_KML.name)
    print(f"Wrote {geojson_path} ({len(registry['plants'])} features)")
    print(f"Wrote {kml_path} ({len(registry['plants'])} placemarks)")
    return 0


def _cmd_summary(args: argparse.Namespace) -> int:
    registry = _load_registry(args.registry)
    summary = summarize(registry)
    out_path = args.data_dir / DEFAULT_SUMMARY.name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(render_text(summary))
    print(f"\nWrote {out_path}")
    return 0


def _cmd_lookup(args: argparse.Namespace) -> int:
    registry = _load_registry(args.registry)
    for plant in registry["plants"]:
        if plant["plant_id"] == args.identifier or plant["eid"] == args.identifier:
            print(json.dumps(plant, indent=2, sort_keys=True))
            return 0
    print(f"No plant found for identifier: {args.identifier}", file=sys.stderr)
    return 1


def _cmd_demo(args: argparse.Namespace) -> int:
    ns = argparse.Namespace(data_dir=DEFAULT_DATA_DIR, seed=SEED, registry=DEFAULT_JSON)
    for step in (_cmd_generate, _cmd_export, _cmd_summary):
        rc = step(ns)
        if rc:
            return rc
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "generate": _cmd_generate,
        "export": _cmd_export,
        "summary": _cmd_summary,
        "lookup": _cmd_lookup,
        "demo": _cmd_demo,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 0
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
