#!/usr/bin/env python3
"""
Create time-chunked symlink directories for GLORYS and SCHISM hindcasts.
Each chunk covers ~1 month of SCHISM files, with GLORYS files bracketing
the period. The i+1 chunk overlaps with chunk i (shares last GLORYS file
and first SCHISM file).
"""

import os
import glob
from datetime import datetime, timedelta
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
GLORYS_ROOT  = Path("/data4/hindcasts/GLORYS/Australia_global_2D_surface_only")
SCHISM_ROOT  = Path("/data4/hindcasts/SCHISM/New_Zealand_global_2D_surface_only_hourly")
STATIC_GLORYS = GLORYS_ROOT / "glorys_static.nc"
HGRID        = Path("/data4/hindcasts/SCHISM/New_Zealand_global_2D_surface_only/hgridNZ_run.gr3")
OUTPUT_ROOT  = Path("/data4/hindcasts/tmp2")
# ──────────────────────────────────────────────────────────────────────────────


def parse_glorys_files():
    """Return sorted list of (datetime, Path) for all GLORYS FullData files."""
    files = sorted(GLORYS_ROOT.glob("*/FullData_*.nc"))
    result = []
    for f in files:
        stem = f.stem  # e.g. FullData_20100101T00
        date_str = stem.split("_")[1][:8]  # '20100101'
        dt = datetime.strptime(date_str, "%Y%m%d")
        result.append((dt, f))
    return result


def parse_schism_files():
    """Return sorted list of (datetime, Path) for all SCHISM files."""
    files = sorted(SCHISM_ROOT.glob("*/*/schism_*.nc"))
    result = []
    for f in files:
        stem = f.stem  # e.g. schism_20100101T00
        date_str = stem.split("_")[1][:8]
        dt = datetime.strptime(date_str, "%Y%m%d")
        result.append((dt, f))
    return result


def chunk_by_month(schism_files):
    """
    Split SCHISM files into monthly chunks.
    Returns list of lists of (datetime, Path).
    """
    if not schism_files:
        return []
    chunks = []
    current_chunk = [schism_files[0]]
    current_month = (schism_files[0][0].year, schism_files[0][0].month)

    for item in schism_files[1:]:
        dt = item[0]
        month_key = (dt.year, dt.month)
        if month_key == current_month:
            current_chunk.append(item)
        else:
            chunks.append(current_chunk)
            current_chunk = [item]
            current_month = month_key
    chunks.append(current_chunk)
    return chunks


def get_glorys_for_chunk(chunk_schism, all_glorys):
    """
    For a SCHISM chunk, find the bracketing GLORYS files:
    - last GLORYS file with date <= first SCHISM date in chunk
    - first GLORYS file with date >= last SCHISM date in chunk
    Returns all GLORYS files in [bracket_before, bracket_after] inclusive.
    """
    first_schism_dt = chunk_schism[0][0]
    last_schism_dt  = chunk_schism[-1][0]

    glorys_dates = [g[0] for g in all_glorys]

    # Find last GLORYS <= first SCHISM
    before_idx = None
    for i, gdt in enumerate(glorys_dates):
        if gdt <= first_schism_dt:
            before_idx = i
        else:
            break

    # Find first GLORYS >= last SCHISM
    after_idx = None
    for i, gdt in enumerate(glorys_dates):
        if gdt >= last_schism_dt:
            after_idx = i
            break

    if before_idx is None or after_idx is None:
        print(f"  WARNING: Could not find bracketing GLORYS for chunk "
              f"{first_schism_dt.date()} – {last_schism_dt.date()}")
        # Fall back to whatever we found
        before_idx = before_idx or 0
        after_idx  = after_idx  or len(all_glorys) - 1

    return all_glorys[before_idx : after_idx + 1]


def make_symlink(target: Path, link: Path):
    """Create a symlink; skip if it already exists and points correctly."""
    if link.exists() or link.is_symlink():
        if link.resolve() == target.resolve():
            return  # already correct
        link.unlink()
    link.symlink_to(target)


def create_chunk_dir(chunk_idx, schism_chunk, glorys_chunk, prev_last_schism=None):
    """
    Create the time_chunk_N directory with symlinks.
    prev_last_schism: (datetime, Path) of the last SCHISM file from prev chunk
                      (for the required overlap).
    """
    chunk_name = OUTPUT_ROOT / f"time_chunk_{chunk_idx}"
    chunk_name.mkdir(parents=True, exist_ok=True)

    # SCHISM files (prepend previous chunk's last file for overlap)
    schism_files_to_link = []
    if prev_last_schism is not None:
        schism_files_to_link.append(prev_last_schism)
    schism_files_to_link.extend(schism_chunk)

    for dt, src in schism_files_to_link:
        link_name = chunk_name / src.name
        make_symlink(src, link_name)

    # GLORYS files
    for dt, src in glorys_chunk:
        link_name = chunk_name / src.name
        make_symlink(src, link_name)

    # Static files
    make_symlink(STATIC_GLORYS, chunk_name / "FullData_glorys_static.nc")
    make_symlink(HGRID,         chunk_name / HGRID.name)

    first_s = schism_files_to_link[0][0].date()
    last_s  = schism_files_to_link[-1][0].date()
    first_g = glorys_chunk[0][0].date()
    last_g  = glorys_chunk[-1][0].date()
    print(f"  {chunk_name.name}: SCHISM {first_s}–{last_s} | "
          f"GLORYS {first_g}–{last_g} | "
          f"{len(schism_files_to_link)} SCHISM + {len(glorys_chunk)} GLORYS files")


def main():
    print("Scanning GLORYS files...")
    all_glorys = parse_glorys_files()
    print(f"  Found {len(all_glorys)} GLORYS files "
          f"({all_glorys[0][0].date()} – {all_glorys[-1][0].date()})")

    print("Scanning SCHISM files...")
    all_schism = parse_schism_files()
    print(f"  Found {len(all_schism)} SCHISM files "
          f"({all_schism[0][0].date()} – {all_schism[-1][0].date()})")

    print("Chunking SCHISM files by month...")
    chunks = chunk_by_month(all_schism)
    print(f"  {len(chunks)} monthly chunks")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    print("\nCreating symlink directories...")
    prev_last_schism = None
    for i, schism_chunk in enumerate(chunks, start=1):
        glorys_chunk = get_glorys_for_chunk(schism_chunk, all_glorys)
        create_chunk_dir(i, schism_chunk, glorys_chunk,
                         prev_last_schism=prev_last_schism)
        prev_last_schism = schism_chunk[-1]

    print(f"\nDone. Created {len(chunks)} chunk directories in {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()