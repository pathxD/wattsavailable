#!/usr/bin/env python3
"""Refresh data/measures.js from BPA's published UES Measures List.

BPA updates the Implementation Manual and UES Measures List every April and
October. Run this script after each update, sanity-check the site locally,
then redeploy.

Usage:
    python3 tools/update_data.py                     # download latest from bpa.gov
    python3 tools/update_data.py path/to/list.xlsx   # use a local copy
    python3 tools/update_data.py --version "October 2026" --effective 2026-10-01

Requires: openpyxl  (pip3 install openpyxl)
"""
import argparse
import datetime
import json
import re
import sys
import urllib.request
from pathlib import Path

UES_URL = "https://www.bpa.gov/-/media/Aep/energy-efficiency/document-library/beets-ues-measure-list.xlsx"
ROOT = Path(__file__).resolve().parent.parent


def clean(v, maxlen=200):
    if v is None:
        return ""
    return re.sub(r"\s+", " ", str(v)).strip()[:maxlen]


def num(v):
    if v is None:
        return None
    try:
        return round(float(v), 1)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx", nargs="?", help="local xlsx path (downloads from bpa.gov if omitted)")
    ap.add_argument("--version", default=None, help='catalog version label, e.g. "October 2026"')
    ap.add_argument("--effective", default=None, help="effective date YYYY-MM-DD")
    args = ap.parse_args()

    import openpyxl

    if args.xlsx:
        path = Path(args.xlsx)
    else:
        path = ROOT / "data" / "ues-measures-latest.xlsx"
        print(f"Downloading {UES_URL} ...")
        req = urllib.request.Request(UES_URL, headers={"User-Agent": "Mozilla/5.0"})
        path.write_bytes(urllib.request.urlopen(req).read())
        print(f"Saved {path} ({path.stat().st_size // 1024} KB)")

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    idx = {h: i for i, h in enumerate(header)}
    today = datetime.datetime.now()

    out = []
    skipped_expired = skipped_nopay = 0
    for r in rows:
        exp = r[idx["BPA Expiration Date"]]
        if exp is not None and isinstance(exp, datetime.datetime) and exp < today:
            skipped_expired += 1
            continue
        pay = num(r[idx["Payment ($/unit)"]])
        if not pay:
            skipped_nopay += 1
            continue
        out.append({
            "id": clean(r[idx["UES Reference Number"]]),
            "hz": clean(r[idx["Heating Zone"]]).replace("Heating Zone ", "HZ").replace("All Heating Zones", "All"),
            "cz": clean(r[idx["Cooling Zone"]]).replace("Cooling Zone ", "CZ").replace("All Cooling Zones", "All"),
            "sec": clean(r[idx["Sector"]]),
            "eu": clean(r[idx["End Use"]]),
            "cat": clean(r[idx["Category"]]),
            "tech": clean(r[idx["Technology/Activity/Practice"]]),
            "k1": clean(r[idx["Key Characteristics 1"]], 160),
            "k2": clean(r[idx["Key Characteristics 2"]], 160),
            "k3": clean(r[idx["Key Characteristics 3"]], 160),
            "k4": clean(r[idx["Key Characteristics 4"]], 160),
            "pay": pay,
            "unit": clean(r[idx["Unit Type of Savings/Payment"]], 60),
            "kwh": num(r[idx["Annual Savings @ Site (kwh/yr)"]]),
            "life": num(r[idx["Measure Life (years)"]]),
            "bldg": clean(r[idx["Primary Building Type"]], 60),
            "vint": clean(r[idx["Vintage"]]),
            "prog": clean(r[idx["Program"]], 40),
            "mtype": clean(r[idx["Measures Types"]]),
            "cap": num(r[idx["Unit Cost Cap"]]),
            "ptcs": clean(r[idx["PTCS"]]),
            "eff": clean(r[idx["Installed Efficiency Level/Rating"]], 160),
            "base": clean(r[idx["Baseline Characteristics"]], 160),
            "forms": clean(r[idx["Forms required at time of invoice review"]], 120),
        })

    version = args.version or clean(ws.title).replace(" Measure List", "")
    meta = {
        "version": version,
        "effective": args.effective or "",
        "extracted": today.strftime("%Y-%m-%d"),
        "count": len(out),
    }
    dst = ROOT / "data" / "measures.js"

    # Skip the write when the measure data itself is unchanged, so automated
    # runs (GitHub Actions) don't produce commits that only bump the date.
    new_data_line = "window.UES_DATA=" + json.dumps(out, separators=(",", ":")) + ";"
    if dst.exists():
        for line in dst.read_text().splitlines():
            if line.startswith("window.UES_DATA="):
                if line == new_data_line:
                    print(f"No change: {dst} already matches the published list ({len(out)} measures).")
                    return 0
                break

    with dst.open("w") as f:
        f.write(f"// BPA UES Measures List — {version}, extracted {meta['extracted']}\n")
        f.write("// Source: https://www.bpa.gov/energy-and-services/conservation/implementation-manual\n")
        f.write("window.UES_DATA=" + json.dumps(out, separators=(",", ":")) + ";\n")
        f.write("window.UES_META=" + json.dumps(meta) + ";\n")
    print(f"Wrote {dst}: {len(out)} measures "
          f"(skipped {skipped_expired} expired, {skipped_nopay} without payment)")
    print("Next: open index.html locally to sanity-check, then redeploy.")


if __name__ == "__main__":
    sys.exit(main())
