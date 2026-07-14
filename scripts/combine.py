#!/usr/bin/env python3
"""
combine.py — Reassemble split FLINT parts back into a single export JSON
             that the Rule Editor can load.

Usage:
    python3 scripts/combine.py <split_dir> [--out <output.json>]

Examples:
    python3 scripts/combine.py model_v1_2026-07-12/
    python3 scripts/combine.py model_v1_2026-07-12/ --out combined_export.json
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ── helpers ──────────────────────────────────────────────────────────────────

def _load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _wrap_date(iso_str):
    """Restore the MongoDB-style {'$date': '...'} wrapper."""
    if iso_str is None:
        return None
    return {"$date": iso_str}


def _read_eflint_spec(eflint_path):
    """
    Read eflint.eflint and extract just the specification lines
    (strip the commented-out scenario / query blocks).
    """
    lines = eflint_path.read_text(encoding="utf-8").splitlines()
    spec_lines = []
    for line in lines:
        # commented blocks start with "// --"
        if line.startswith("// --"):
            break
        spec_lines.append(line)
    return "\n".join(spec_lines).rstrip() + "\n"


# ── combine ───────────────────────────────────────────────────────────────────

def combine(split_dir):
    p_meta        = split_dir / "metadata.json"
    p_flint       = split_dir / "FLINT_spec.json"
    p_eflint      = split_dir / "eflint.eflint"
    p_eflint_meta = split_dir / "eflint_meta.json"

    for p in (p_meta, p_flint, p_eflint, p_eflint_meta):
        if not p.exists():
            print(f"ERROR: Missing file: {p}", file=sys.stderr)
            sys.exit(1)

    meta        = _load_json(p_meta)
    flint       = _load_json(p_flint)
    eflint_meta = _load_json(p_eflint_meta)
    spec_text   = _read_eflint_spec(p_eflint)

    combined = {
        "task_id": meta.get("task_id"),

        "metadata": {
            "owner":       meta.get("owner"),
            "owner_group": meta.get("owner_group"),
            "created_at":  _wrap_date(meta.get("created_at")),
            "modified_at": _wrap_date(meta.get("modified_at")),
            "title":       meta.get("name"),
        },

        "flint_spec": {
            "id":             flint.get("id"),
            "type":           flint.get("type"),
            "description":    flint.get("description"),
            "label":          flint.get("label"),
            "hasEditor":      flint.get("hasEditor"),
            "sourceDocs":     flint.get("sourceDocs", []),
            "interpretation": flint.get("interpretation"),
            "frames":         flint.get("frames", []),
        },

        "saved_artifact": flint.get("saved_artifact"),

        "eflint": {
            "specification":     spec_text,
            "scenario":          eflint_meta.get("scenario"),
            "query":             eflint_meta.get("query"),
            "generated_at":      _wrap_date(eflint_meta.get("generated_at")),
            "generator_version": eflint_meta.get("generator_version"),
        },

        "executable_selection": meta.get("executable_selection"),
    }

    return combined


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Combine split FLINT parts back into a single export JSON."
    )
    parser.add_argument("split_dir", help="Directory containing metadata.json, FLINT_spec.json, eflint.eflint, eflint_meta.json")
    parser.add_argument("--out", default=None, help="Output file path (default: auto-named next to split_dir)")
    args = parser.parse_args()

    split_dir = Path(args.split_dir).resolve()
    if not split_dir.is_dir():
        print(f"ERROR: Not a directory: {split_dir}", file=sys.stderr)
        sys.exit(1)

    result = combine(split_dir)

    if args.out:
        out_path = Path(args.out).resolve()
    else:
        name      = result["metadata"]["title"].replace(" ", "_")
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        out_path  = split_dir.parent / f"{name}_{timestamp}_combined.json"

    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Combined → {out_path}")
    print(f"  {out_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
