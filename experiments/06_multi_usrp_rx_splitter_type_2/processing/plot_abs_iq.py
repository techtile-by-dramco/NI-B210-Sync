import os
import re
import argparse
import numpy as np
import yaml
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path

# ---------- IO helpers ----------

def load_metadata_from_yml(npy_path: str):
    yml_path = npy_path.replace('data_', 'metadata_').replace('.npy', '.yml')
    if os.path.exists(yml_path):
        with open(yml_path, 'r') as f:
            return yaml.safe_load(f)
    print(f"[WARN] Metadata file not found for {npy_path} -> {yml_path}")
    return None

def load_iq(npy_path: str) -> np.ndarray:
    """Load IQ data and normalize shape to (C, N)."""
    arr = np.load(npy_path)
    if arr.ndim != 2:
        raise ValueError(f"Unexpected IQ ndim={arr.ndim} for {npy_path}. Expected 2D.")
    if arr.shape[0] == 2:      # (2, N)
        return arr
    elif arr.shape[1] == 2:    # (N, 2)
        return arr.T
    else:
        raise ValueError(f"Unexpected IQ shape {arr.shape} for {npy_path} (need 2 channels).")

def extract_tile_from_filename(filename: str, default="A00"):
    m = re.search(r'_([A-Za-z]\d{2})_', filename)
    return m.group(1) if m else default

def extract_hostname(metadata: dict, filename: str):
    if metadata and "hostname" in metadata and metadata["hostname"]:
        return str(metadata["hostname"])
    m = re.search(r"data_(t\d{2})_", filename, re.IGNORECASE)
    return m.group(1).upper() if m else "HOST"

# ---------- Core ----------

def collect_abs_by_gainB(in_dir: str,
                         gain_a_target: int = 30,
                         channel_index_for_abs: int = 1,
                         max_samples_per_file: int = 20000):
    """
    Returns:
      data[hostname][gain_b] -> list of 1D arrays (|IQ_B| samples)
      tiles: set of tile names observed
    """
    data = defaultdict(lambda: defaultdict(list))
    tiles = set()

    for fn in os.listdir(in_dir):
        if not fn.endswith(".npy"):
            continue

        npy_path = os.path.join(in_dir, fn)
        meta = load_metadata_from_yml(npy_path)
        if meta is None:
            continue

        try:
            gain_a = int(meta["rx_gain_a"])
            gain_b = int(meta["rx_gain_b"])
        except Exception:
            print(f"[WARN] Missing rx_gain_a or rx_gain_b in metadata for {fn}")
            continue

        if gain_a != gain_a_target:
            continue

        try:
            iq = load_iq(npy_path)
        except Exception as e:
            print(f"[WARN] {e}")
            continue

        ch = iq[channel_index_for_abs, :]
        mags = np.abs(ch).astype(np.float64)

        if max_samples_per_file and mags.size > max_samples_per_file:
            idx = np.random.default_rng(0).choice(mags.size, size=max_samples_per_file, replace=False)
            mags = mags[idx]

        hostname = extract_hostname(meta, fn)
        tile = extract_tile_from_filename(fn)
        tiles.add(tile)

        data[hostname][gain_b].append(mags)

    return data, tiles

def make_violin_plots(data, tiles, out_dir: str, gain_a_target: int, channel_label: str):
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    for hostname, by_gain in data.items():
        if not by_gain:
            continue

        gains_sorted = sorted(by_gain.keys())
        datasets = [np.concatenate(by_gain[g]) for g in gains_sorted]

        plt.figure(figsize=(10, 5))
        plt.violinplot(datasets, positions=gains_sorted, showmeans=True, showextrema=True, showmedians=True)
        plt.xlabel("RX Gain B [dB]")
        plt.ylabel(f"|IQ| magnitude ({channel_label})")
        tile_str = ", ".join(sorted(tiles)) if tiles else "TILE"
        plt.title(f"Violin of |IQ| vs RX Gain B (RX Gain A = {gain_a_target} dB)\nHost: {hostname} • {tile_str}")
        plt.grid(True, which="both", axis="y", linestyle=":", linewidth=0.7)
        plt.tight_layout()

        stem = f"{tile_str}_{hostname}_violin_absIQ_gainA{gain_a_target}"
        plt.savefig(os.path.join(out_dir, f"{stem}.png"), dpi=200)
        plt.savefig(os.path.join(out_dir, f"{stem}.pdf"))
        plt.close()

        print(f"[OK] Saved plots for {hostname}")

# ---------- CLI ----------

def main():
    parser = argparse.ArgumentParser(description="Plot |IQ| violin per RX Gain B, filtered by RX Gain A.")
    parser.add_argument("--in-dir", type=str, default="data", help="Directory with data_*.npy and metadata_*.yml files")
    parser.add_argument("--out-dir", type=str, default="results", help="Output directory for figures")
    parser.add_argument("--gain-a", type=int, default=30, help="Filter: include only files where RX Gain A equals this value")
    parser.add_argument("--channel", type=str, default="B", choices=["A","B"], help="Channel whose |IQ| to plot")
    parser.add_argument("--max-samples-per-file", type=int, default=20000, help="Subsample per file for speed/memory (0 = no limit)")
    args = parser.parse_args()

    # Resolve absolute paths relative to script location
    script_dir = Path(__file__).resolve().parent
    in_dir = (script_dir / args.in_dir).resolve()
    out_dir = (script_dir / args.out_dir).resolve()

    if not in_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {in_dir}")

    channel_index = 1 if args.channel.upper() == "B" else 0

    data, tiles = collect_abs_by_gainB(
        in_dir=str(in_dir),
        gain_a_target=args.gain_a,
        channel_index_for_abs=channel_index,
        max_samples_per_file=(args.max_samples_per_file if args.max_samples_per_file > 0 else None),
    )

    if not data:
        print("[INFO] No matching data found. Check --in-dir and --gain-a.")
        return

    make_violin_plots(
        data=data,
        tiles=tiles,
        out_dir=str(out_dir),
        gain_a_target=args.gain_a,
        channel_label=f"CH{channel_index} ({'A' if channel_index==0 else 'B'})",
    )

if __name__ == "__main__":
    main()
