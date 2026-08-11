"""Decision-support summary over the plant-passport registry.

Turns the virtual vineyard into managerial tasking: health and
certification breakdowns, per-block counts, the list of plants requiring
treatment, and audit/traceability spot-checks.
"""

from __future__ import annotations

from collections import Counter


def summarize(registry: dict) -> dict:
    plants = registry["plants"]
    total = len(plants)
    by_health = Counter(p["health_status"] for p in plants)
    by_certification = Counter(p["certification"] for p in plants)
    by_block: dict[str, Counter] = {}
    for plant in plants:
        by_block.setdefault(plant["block"], Counter())[plant["health_status"]] += 1

    needs_treatment = sorted(
        (p for p in plants if p["health_status"] == "treatment_required"),
        key=lambda p: p["plant_id"],
    )
    monitor_list = sorted(
        (p for p in plants if p["health_status"] == "monitor"),
        key=lambda p: p["plant_id"],
    )
    suggested_tasks = [
        {
            "task": "Targeted treatment",
            "scope": f"{len(needs_treatment)} plants flagged treatment_required",
            "plant_ids": [p["plant_id"] for p in needs_treatment],
            "basis": "plant-level health status from field scans",
        },
        {
            "task": "Monitoring round",
            "scope": f"{len(monitor_list)} plants on the watch list",
            "plant_ids": [p["plant_id"] for p in monitor_list],
            "basis": "early indicators; re-scan within two weeks",
        },
        {
            "task": "Compliance audit",
            "scope": (
                f"{by_certification.get('certified', 0)} certified (blue-label) plants "
                "with complete eID traceability"
            ),
            "basis": "certification class on each plant passport",
        },
    ]
    eids = [p["eid"] for p in plants]
    traceability = {
        "plants_total": total,
        "plants_with_eid": sum(1 for e in eids if len(e) == 14 and e.isdigit()),
        "duplicate_eids": total - len(set(eids)),
        "plants_with_coordinates": sum(
            1 for p in plants if p["latitude"] is not None and p["longitude"] is not None
        ),
    }
    return {
        "registry": registry["registry"],
        "plants_total": total,
        "blocks": {
            block: {
                "plants": sum(counts.values()),
                "by_health_status": dict(sorted(counts.items())),
            }
            for block, counts in sorted(by_block.items())
        },
        "by_health_status": dict(sorted(by_health.items())),
        "by_certification": dict(sorted(by_certification.items())),
        "treatment_required_count": len(needs_treatment),
        "monitor_count": len(monitor_list),
        "suggested_tasks": suggested_tasks,
        "traceability_audit": traceability,
    }


def render_text(summary: dict) -> str:
    lines = [
        "VineMIS decision-support summary",
        "================================",
        f"Registry: {summary['registry']}",
        f"Plants: {summary['plants_total']}",
        "",
        "Health status:",
    ]
    for status, count in summary["by_health_status"].items():
        lines.append(f"  {status}: {count}")
    lines.append("Certification classes:")
    for cert, count in summary["by_certification"].items():
        lines.append(f"  {cert}: {count}")
    lines.append("Blocks:")
    for block, info in summary["blocks"].items():
        lines.append(f"  Block {block}: {info['plants']} plants {info['by_health_status']}")
    lines.append("")
    lines.append("Suggested tasks:")
    for task in summary["suggested_tasks"]:
        lines.append(f"  - {task['task']}: {task['scope']}")
    audit = summary["traceability_audit"]
    lines.append("")
    lines.append(
        "Traceability audit: "
        f"{audit['plants_with_eid']}/{audit['plants_total']} plants with valid 14-digit eIDs, "
        f"{audit['duplicate_eids']} duplicates, "
        f"{audit['plants_with_coordinates']} geotagged."
    )
    return "\n".join(lines)
