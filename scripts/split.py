#!/usr/bin/env python3
"""
split.py — Split a FLINT Rule Editor export JSON into three files:
  metadata.json    — task identity, ownership, timestamps, export provenance
  FLINT_spec.json  — FLINT frames, source documents, interpretation
  eflint.eflint    — eFLINT specification (plain text), scenario and query as comments

Output folder name: model_v<N>_<YYYY-MM-DD>/

Usage:
    python3 scripts/split.py <export_file.json> [--out <output_dir>] [--model-version <N>]

Examples:
    python3 scripts/split.py rental_subsidy_export.json
    python3 scripts/split.py export.json --model-version 2
    python3 scripts/split.py export.json --out ./my_output
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ── helpers ──────────────────────────────────────────────────────────────────

def _parse_date(value):
    """Accept either '$date' dict or plain ISO string."""
    if isinstance(value, dict):
        return value.get("$date")
    if isinstance(value, str):
        return value
    return None


def _slug(text):
    """Turn a title into a filesystem-safe slug."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _auto_version(raw):
    """
    Derive a version string. Priority:
      1. eflint.generator_version  (e.g. "1.0.3")
      2. metadata.modified_at date (e.g. "2026-03-31")
      3. fallback "1"
    """
    gen_ver = raw.get("eflint", {}).get("generator_version")
    if gen_ver and gen_ver.strip():
        return gen_ver.strip()

    modified = _parse_date(raw.get("metadata", {}).get("modified_at"))
    if modified:
        return modified[:10]   # "YYYY-MM-DD"

    return "1"


def _build_eflint_text(eflint_block):
    """
    Build a plain-text .eflint file.
    Specification is the main content.
    Scenario and query are appended as commented-out blocks.
    """
    parts = []

    spec = eflint_block.get("specification", "")
    if spec:
        parts.append(spec.rstrip())

    scenario = eflint_block.get("scenario", "")
    if scenario and scenario.strip():
        parts.append("\n// -- SCENARIO --")
        for line in scenario.splitlines():
            parts.append(f"// {line}")

    query = eflint_block.get("query", "")
    if query and query.strip():
        parts.append("\n// -- QUERY --")
        for line in query.splitlines():
            parts.append(f"// {line}")

    return "\n".join(parts) + "\n"


# ── split ─────────────────────────────────────────────────────────────────────

def split(export_path, out_dir, model_version=1):
    with export_path.open(encoding="utf-8") as f:
        raw = json.load(f)

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    today   = now_iso[:10]

    title   = (
        raw.get("metadata", {}).get("title")
        or raw.get("flint_spec", {}).get("label")
        or "untitled"
    )
    version = _auto_version(raw)

    # ── default output dir: model_v<N>_<date> ────────────────────────────────
    if out_dir is None:
        folder_name = f"model_v{model_version}_{today}"
        out_dir = export_path.parent / folder_name

    out_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. metadata.json ─────────────────────────────────────────────────────
    meta_block = raw.get("metadata", {})
    metadata = {
        "task_id":     raw.get("task_id"),
        "name":        title,
        "slug":        _slug(title),
        "model_version": f"v{model_version}",
        "data_version":  version,

        "owner":       meta_block.get("owner"),
        "owner_group": meta_block.get("owner_group"),
        "created_at":  _parse_date(meta_block.get("created_at")),
        "modified_at": _parse_date(meta_block.get("modified_at")),

        "executable_selection": raw.get("executable_selection"),

        "export": {
            "exported_at":    now_iso,
            "source_file":    export_path.name,
            "script_version": "1.1",
        },
    }

    # ── 2. FLINT_spec.json ────────────────────────────────────────────────────
    flint_spec = raw.get("flint_spec", {})
    flint = {
        "schema_version": "1.0",
        "task_id":        raw.get("task_id"),
        "id":             flint_spec.get("id"),
        "type":           flint_spec.get("type"),
        "label":          flint_spec.get("label"),
        "description":    flint_spec.get("description"),
        "hasEditor":      flint_spec.get("hasEditor"),
        "interpretation": flint_spec.get("interpretation"),
        "frames":         flint_spec.get("frames", []),
        "sourceDocs":     flint_spec.get("sourceDocs", []),
        "saved_artifact": raw.get("saved_artifact"),
    }

    # ── 3. eflint.eflint (plain text) ─────────────────────────────────────────
    eflint_block = raw.get("eflint", {})
    eflint_text  = _build_eflint_text(eflint_block)

    # also keep a small eflint metadata sidecar so combine.py can reconstruct
    eflint_meta = {
        "generator_version": eflint_block.get("generator_version"),
        "generated_at":      _parse_date(eflint_block.get("generated_at")),
        "scenario":          eflint_block.get("scenario"),
        "query":             eflint_block.get("query"),
    }

    # ── write ─────────────────────────────────────────────────────────────────
    p_meta       = out_dir / "metadata.json"
    p_flint      = out_dir / "FLINT_spec.json"
    p_eflint     = out_dir / "eflint.eflint"
    p_eflint_meta = out_dir / "eflint_meta.json"

    p_meta.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    p_flint.write_text(json.dumps(flint, indent=2, ensure_ascii=False), encoding="utf-8")
    p_eflint.write_text(eflint_text, encoding="utf-8")
    p_eflint_meta.write_text(json.dumps(eflint_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    return out_dir, p_meta, p_flint, p_eflint, p_eflint_meta


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Split a FLINT export JSON into metadata / FLINT_spec / eflint."
    )
    parser.add_argument("export_file", help="Path to the export JSON file")
    parser.add_argument("--out", default=None, help="Output directory (default: model_v<N>_<date>/)")
    parser.add_argument("--model-version", type=int, default=1, metavar="N",
                        help="Model version number used in folder name (default: 1)")
    args = parser.parse_args()

    export_path = Path(args.export_file).resolve()
    if not export_path.exists():
        print(f"ERROR: File not found: {export_path}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out).resolve() if args.out else None

    out_dir, p_meta, p_flint, p_eflint, p_eflint_meta = split(
        export_path, out_dir, model_version=args.model_version
    )

    print(f"Split complete → {out_dir}/")
    print(f"  metadata.json      {p_meta.stat().st_size:>8,} bytes")
    print(f"  FLINT_spec.json    {p_flint.stat().st_size:>8,} bytes")
    print(f"  eflint.eflint      {p_eflint.stat().st_size:>8,} bytes")
    print(f"  eflint_meta.json   {p_eflint_meta.stat().st_size:>8,} bytes")


if __name__ == "__main__":
    main()
