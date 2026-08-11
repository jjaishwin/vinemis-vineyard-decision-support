"""Smoke tests for the VineMIS synthetic demo. No network access required."""

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from vinemis.cli import main
from vinemis.decision import summarize
from vinemis.exports import to_geojson, to_kml, write_geojson, write_kml
from vinemis.storage import load_json, load_sqlite, save_json, save_sqlite
from vinemis.vineyard import generate_registry, make_eid, meters_to_degrees


class TestVineyard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = generate_registry()
        cls.plants = cls.registry["plants"]

    def test_generation_deterministic(self):
        self.assertEqual(generate_registry(), generate_registry())

    def test_plant_count_and_unique_eids(self):
        self.assertEqual(len(self.plants), 6 * 20 + 4 * 15)
        eids = [p["eid"] for p in self.plants]
        self.assertEqual(len(set(eids)), len(eids))
        for eid in eids:
            self.assertEqual(len(eid), 14)
            self.assertTrue(eid.isdigit())

    def test_coordinates_are_wgs84_and_grid_aligned(self):
        for plant in self.plants:
            self.assertGreater(plant["latitude"], 43.0)
            self.assertLess(plant["latitude"], 44.0)
            self.assertGreater(plant["longitude"], 11.0)
            self.assertLess(plant["longitude"], 12.0)
        # Adjacent plants in a row are ~0.8 m apart in longitude.
        p1 = next(p for p in self.plants if p["plant_id"] == "A-R01-P001")
        p2 = next(p for p in self.plants if p["plant_id"] == "A-R01-P002")
        self.assertAlmostEqual(p1["latitude"], p2["latitude"], places=8)
        dlon = p2["longitude"] - p1["longitude"]
        self.assertGreater(dlon, 0)

    def test_meters_to_degrees_origin(self):
        lat, lon = meters_to_degrees(0.0, 0.0)
        self.assertEqual((lat, lon), (43.7, 11.2))

    def test_eid_format(self):
        self.assertEqual(make_eid(1), "98200000000001")


class TestStorageAndExports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = generate_registry()

    def test_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = save_json(self.registry, Path(tmp) / "reg.json")
            self.assertEqual(load_json(path), self.registry)

    def test_sqlite_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = save_sqlite(self.registry, Path(tmp) / "reg.sqlite")
            loaded = load_sqlite(path)
        self.assertEqual(loaded["plants"], self.registry["plants"])
        self.assertEqual(loaded["registry"], self.registry["registry"])

    def test_geojson_structure(self):
        geojson = to_geojson(self.registry)
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertEqual(len(geojson["features"]), len(self.registry["plants"]))
        first = geojson["features"][0]
        self.assertEqual(first["geometry"]["type"], "Point")
        lon, lat = first["geometry"]["coordinates"]
        plant = self.registry["plants"][0]
        self.assertEqual((lat, lon), (plant["latitude"], plant["longitude"]))
        self.assertEqual(first["properties"]["eid"], plant["eid"])

    def test_kml_is_well_formed_xml(self):
        with tempfile.TemporaryDirectory() as tmp:
            kml_path = write_kml(self.registry, Path(tmp) / "v.kml")
            root = ET.parse(kml_path).getroot()
        ns = "{http://www.opengis.net/kml/2.2}"
        placemarks = root.findall(f".//{ns}Placemark")
        self.assertEqual(len(placemarks), len(self.registry["plants"]))


class TestDecisionAndCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = generate_registry()
        cls.summary = summarize(cls.registry)

    def test_summary_accounts_for_all_plants(self):
        total = sum(self.summary["by_health_status"].values())
        self.assertEqual(total, self.summary["plants_total"])
        audit = self.summary["traceability_audit"]
        self.assertEqual(audit["duplicate_eids"], 0)
        self.assertEqual(audit["plants_with_eid"], audit["plants_total"])

    def test_summary_json_serialisable(self):
        json.dumps(self.summary, sort_keys=True)

    def test_cli_demo_deterministic_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            self.assertEqual(main(["generate", "--data-dir", str(data_dir)]), 0)
            registry_path = str(data_dir / "plant_passports.json")
            self.assertEqual(
                main(["export", "--registry", registry_path, "--data-dir", str(data_dir)]), 0
            )
            self.assertEqual(
                main(["summary", "--registry", registry_path, "--data-dir", str(data_dir)]), 0
            )
            names = {
                "plant_passports.json", "plant_passports.sqlite",
                "virtual_vineyard.geojson", "virtual_vineyard.kml",
                "decision_summary.json",
            }
            self.assertTrue(names.issubset({p.name for p in data_dir.iterdir()}))
            # Determinism: regenerate into a second directory and compare text outputs.
            data_dir2 = Path(tmp) / "second"
            data_dir2.mkdir()
            self.assertEqual(main(["generate", "--data-dir", str(data_dir2)]), 0)
            self.assertEqual(
                (data_dir / "plant_passports.json").read_bytes(),
                (data_dir2 / "plant_passports.json").read_bytes(),
            )

    def test_cli_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            main(["generate", "--data-dir", str(data_dir)])
            registry_path = data_dir / "plant_passports.json"
            self.assertEqual(
                main(["lookup", "A-R01-P001", "--registry", str(registry_path)]), 0
            )
            self.assertEqual(
                main(["lookup", "99999999999999", "--registry", str(registry_path)]), 1
            )


if __name__ == "__main__":
    unittest.main()
