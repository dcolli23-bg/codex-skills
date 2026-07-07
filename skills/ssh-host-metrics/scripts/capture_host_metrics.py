#!/usr/bin/env python3
"""Capture high-frequency CPU/RAM metrics from a Linux SSH host and plot SVG."""

from __future__ import annotations

import argparse
import csv
import html
import math
import re
import shlex
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


HEADER = [
    "ts",
    "host",
    "cpu",
    "user",
    "nice",
    "system",
    "idle",
    "iowait",
    "irq",
    "softirq",
    "steal",
    "mem_total_kb",
    "mem_available_kb",
]

REMOTE_SAMPLER = r"""
while true; do
  ts=$(date +%s.%N)
  mem_total=
  mem_available=
  while read -r key value _; do
    case "$key" in
      MemTotal:) mem_total=$value ;;
      MemAvailable:) mem_available=$value ;;
    esac
  done < /proc/meminfo
  awk -v ts="$ts" -v host="$HOST_NAME" -v mt="$mem_total" -v ma="$mem_available" '
    /^cpu[0-9]* / {
      printf "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n", ts, host, $1, $2, $3, $4, $5, $6, $7, $8, $9, mt, ma
    }
  ' /proc/stat
  sleep "$INTERVAL"
done
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture /proc CPU and RAM metrics over SSH and generate an SVG plot."
    )
    parser.add_argument("--host", help="SSH host to sample, such as bil-cell-4")
    parser.add_argument("--duration", type=float, help="Capture duration in seconds")
    parser.add_argument("--hz", type=float, default=10.0, help="Samples per second, default: 10")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory for CSV and SVG outputs, default: current directory",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="Regenerate an SVG from an existing CSV instead of running SSH",
    )
    return parser.parse_args()


def prompt_missing(args: argparse.Namespace) -> None:
    if args.csv:
        return
    if not args.host:
        args.host = input("SSH host: ").strip()
    if not args.duration:
        raw = input("Duration seconds [30]: ").strip()
        args.duration = float(raw) if raw else 30.0


def validate_args(args: argparse.Namespace) -> None:
    if args.csv:
        if not args.csv.exists():
            raise SystemExit(f"CSV not found: {args.csv}")
        return
    if not args.host:
        raise SystemExit("missing SSH host")
    if args.duration is None or args.duration <= 0:
        raise SystemExit("duration must be greater than 0")
    if args.hz <= 0:
        raise SystemExit("hz must be greater than 0")


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "host"


def valid_metric_row(line: str) -> bool:
    parts = line.rstrip("\n").split(",")
    if len(parts) != len(HEADER):
        return False
    try:
        float(parts[0])
        for item in parts[3:11]:
            int(item)
        int(parts[11])
        int(parts[12])
    except ValueError:
        return False
    return parts[2] == "cpu" or re.fullmatch(r"cpu\d+", parts[2]) is not None


def capture(args: argparse.Namespace) -> Path:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = args.out_dir / f"host-metrics-percpu-{safe_name(args.host)}-{stamp}.csv"
    interval = 1.0 / args.hz
    remote_command = (
        f"HOST_NAME={shlex.quote(args.host)} "
        f"INTERVAL={shlex.quote(f'{interval:.9f}')} "
        "bash -s"
    )
    command = [
        "timeout",
        f"{args.duration:.3f}",
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        args.host,
        remote_command,
    ]

    completed = subprocess.run(
        command,
        input=REMOTE_SAMPLER,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    rows = [line for line in completed.stdout.splitlines() if valid_metric_row(line)]
    with csv_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        for row in rows:
            writer.writerow(row.split(","))

    if completed.stderr.strip():
        print("remote stderr:", file=sys.stderr)
        print(completed.stderr.strip(), file=sys.stderr)

    if completed.returncode not in (0, 124):
        raise SystemExit(f"ssh sampler failed with exit code {completed.returncode}")
    if not rows:
        raise SystemExit(f"no metric rows captured; wrote header-only CSV at {csv_path}")
    return csv_path


def total_idle(row: dict[str, str]) -> tuple[int, int]:
    total = sum(
        int(row[key])
        for key in ["user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal"]
    )
    idle_all = int(row["idle"]) + int(row["iowait"])
    return total, idle_all


def usage_series(rows: list[dict[str, str]], start: float) -> list[tuple[float, float, dict[str, str]]]:
    out = []
    previous = None
    for row in rows:
        total, idle = total_idle(row)
        if previous is not None:
            total_delta = total - previous[0]
            idle_delta = idle - previous[1]
            if total_delta > 0:
                pct = 100.0 * (total_delta - idle_delta) / total_delta
                out.append((float(row["ts"]) - start, pct, row))
        previous = (total, idle)
    return out


def nice_range(values: list[float], pad_fraction: float = 0.12) -> tuple[float, float]:
    finite = [value for value in values if math.isfinite(value)]
    lo = min(finite)
    hi = max(finite)
    if abs(hi - lo) < 1e-9:
        pad = max(1.0, abs(hi) * 0.05)
        return lo - pad, hi + pad
    pad = (hi - lo) * pad_fraction
    lo -= pad
    hi += pad
    step = 10 ** math.floor(math.log10(hi - lo))
    return math.floor(lo / step) * step, math.ceil(hi / step) * step


def fmt_tick(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def load_csv(csv_path: Path) -> tuple[dict[str, list[dict[str, str]]], list[str]]:
    by_cpu: dict[str, list[dict[str, str]]] = defaultdict(list)
    with csv_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            by_cpu[row["cpu"]].append(row)
    if "cpu" not in by_cpu:
        raise SystemExit("missing aggregate cpu rows")
    cpus = sorted(
        (name for name in by_cpu if name.startswith("cpu") and name != "cpu"),
        key=lambda name: int(name[3:]),
    )
    if not cpus:
        raise SystemExit("missing per-cpu rows")
    return by_cpu, cpus


def draw_svg(csv_path: Path) -> dict[str, str]:
    by_cpu, cpus = load_csv(csv_path)
    host = by_cpu["cpu"][0]["host"]
    start = float(by_cpu["cpu"][0]["ts"])

    aggregate = usage_series(by_cpu["cpu"], start)
    if not aggregate:
        raise SystemExit("not enough aggregate samples")
    per_cpu = {cpu: usage_series(by_cpu[cpu], start) for cpu in cpus}
    per_cpu = {cpu: values for cpu, values in per_cpu.items() if values}
    if not per_cpu:
        raise SystemExit("not enough per-cpu samples")

    memory = []
    for t, _, row in aggregate:
        mem_total = int(row["mem_total_kb"])
        mem_available = int(row["mem_available_kb"])
        memory.append((t, 100.0 * (1.0 - mem_available / mem_total) if mem_total else math.nan))

    span = float(by_cpu["cpu"][-1]["ts"]) - start
    hz = (len(by_cpu["cpu"]) - 1) / span if span > 0 else math.nan
    x_max = max(t for t, _, _ in aggregate) or 1.0

    left, right = 84, 44
    top = 74
    panel_h = 175
    gap = 56
    legend_cols = 8
    legend_rows = math.ceil(len(cpus) / legend_cols)
    row_h = 16
    legend_top_extra = 64
    width = 1180
    y1_last = top + 2 * (panel_h + gap) + panel_h
    height = int(y1_last + 44 + legend_top_extra + legend_rows * row_h + 24)
    plot_w = width - left - right

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fff"/>',
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#222}.tick{font-size:12px;fill:#555}.label{font-size:14px;font-weight:700}.title{font-size:22px;font-weight:700}.sub{font-size:13px;fill:#555}.legend{font-size:11px;fill:#333}</style>",
        f'<text class="title" x="{left}" y="34">{html.escape(host)} high-frequency host metrics</text>',
        f'<text class="sub" x="{left}" y="56">{len(by_cpu["cpu"])} samples, {len(cpus)} logical CPUs, {span:.3f}s span, mean {hz:.2f} Hz. Source: {html.escape(str(csv_path))}</text>',
    ]

    def draw_panel(
        index: int,
        label: str,
        ymin: float,
        ymax: float,
        series: list[tuple[str, list[tuple[float, float]], str, float, float]],
    ) -> tuple[float, float, float, float]:
        y0 = top + index * (panel_h + gap)
        x0 = left
        x1 = left + plot_w
        y1 = y0 + panel_h
        parts.append(f'<text class="label" x="{x0}" y="{y0 - 14}">{html.escape(label)}</text>')
        parts.append(
            f'<rect x="{x0}" y="{y0}" width="{plot_w}" height="{panel_h}" fill="#fbfbfb" stroke="#cfcfcf"/>'
        )
        for tick in range(5):
            frac = tick / 4
            yy = y1 - frac * panel_h
            value = ymin + frac * (ymax - ymin)
            parts.append(
                f'<line x1="{x0}" y1="{yy:.2f}" x2="{x1}" y2="{yy:.2f}" stroke="#e7e7e7"/>'
            )
            parts.append(
                f'<text class="tick" x="{x0 - 10}" y="{yy + 4:.2f}" text-anchor="end">{fmt_tick(value)}</text>'
            )
        for tick in range(7):
            frac = tick / 6
            xx = x0 + frac * plot_w
            value = frac * x_max
            parts.append(
                f'<line x1="{xx:.2f}" y1="{y0}" x2="{xx:.2f}" y2="{y1}" stroke="#eeeeee"/>'
            )
            if index == 2:
                parts.append(
                    f'<text class="tick" x="{xx:.2f}" y="{y1 + 22}" text-anchor="middle">{value:.1f}s</text>'
                )

        def sx(t: float) -> float:
            return x0 + (t / x_max) * plot_w

        def sy(v: float) -> float:
            if ymax == ymin:
                return y0 + panel_h / 2
            return y1 - ((v - ymin) / (ymax - ymin)) * panel_h

        for _, points, color, line_width, opacity in series:
            coords = " ".join(
                f"{sx(t):.2f},{sy(v):.2f}" for t, v in points if math.isfinite(v)
            )
            parts.append(
                f'<polyline fill="none" stroke="{color}" stroke-width="{line_width}" stroke-opacity="{opacity}" points="{coords}"/>'
            )
        return x0, y0, x1, y1

    aggregate_points = [(t, pct) for t, pct, _ in aggregate]
    memory_points = memory
    all_per_cpu_values = [pct for values in per_cpu.values() for _, pct, _ in values]

    aggregate_ymax = max(100.0, math.ceil(max(v for _, v in aggregate_points) / 10.0) * 10.0)
    draw_panel(
        0,
        "Aggregate CPU utilization (%)",
        0.0,
        aggregate_ymax,
        [("cpu", aggregate_points, "#1f77b4", 2.0, 1.0)],
    )
    mem_min, mem_max = nice_range([value for _, value in memory_points], 0.25)
    draw_panel(
        1,
        "RAM used (%)",
        mem_min,
        mem_max,
        [("mem", memory_points, "#2ca02c", 2.0, 1.0)],
    )

    palette = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
        "#393b79",
        "#637939",
        "#8c6d31",
        "#843c39",
        "#7b4173",
        "#3182bd",
        "#e6550d",
        "#31a354",
        "#756bb1",
        "#636363",
        "#9ecae1",
        "#fdae6b",
        "#a1d99b",
        "#bcbddc",
    ]
    per_series = []
    for index, cpu in enumerate(cpus):
        points = [(t, pct) for t, pct, _ in per_cpu[cpu]]
        per_series.append((cpu, points, palette[index % len(palette)], 1.15, 0.72))
    _, _, _, y1 = draw_panel(
        2,
        "Per-logical-CPU utilization (%)",
        0.0,
        max(100.0, math.ceil(max(all_per_cpu_values) / 10.0) * 10.0),
        per_series,
    )
    parts.append(
        f'<text class="tick" x="{left + plot_w / 2:.2f}" y="{y1 + 44}" text-anchor="middle">Seconds since first sample</text>'
    )

    legend_y = y1 + legend_top_extra
    col_w = 90
    for index, cpu in enumerate(cpus):
        col = index % legend_cols
        row = index // legend_cols
        x = left + col * col_w
        y = legend_y + row * row_h
        color = palette[index % len(palette)]
        parts.append(
            f'<line x1="{x}" y1="{y - 4}" x2="{x + 22}" y2="{y - 4}" stroke="{color}" stroke-width="3"/>'
        )
        parts.append(f'<text class="legend" x="{x + 28}" y="{y}">{cpu}</text>')

    parts.append("</svg>")
    svg_path = csv_path.with_suffix(".svg")
    svg_path.write_text("\n".join(parts) + "\n")

    aggregate_values = [value for _, value in aggregate_points]
    memory_values = [value for _, value in memory_points]
    per_max_cpu, per_max_value = max(
        ((cpu, max(value for _, value, _ in values)) for cpu, values in per_cpu.items()),
        key=lambda item: item[1],
    )
    per_avg = sum(all_per_cpu_values) / len(all_per_cpu_values)
    return {
        "csv": str(csv_path),
        "svg": str(svg_path),
        "aggregate_samples": str(len(by_cpu["cpu"])),
        "logical_cpus": str(len(cpus)),
        "span_seconds": f"{span:.3f}",
        "mean_hz": f"{hz:.2f}",
        "aggregate_cpu_avg_pct": f"{sum(aggregate_values) / len(aggregate_values):.2f}",
        "aggregate_cpu_max_pct": f"{max(aggregate_values):.2f}",
        "per_cpu_avg_pct": f"{per_avg:.2f}",
        "per_cpu_max": f"{per_max_cpu}:{per_max_value:.2f}",
        "ram_used_avg_pct": f"{sum(memory_values) / len(memory_values):.2f}",
    }


def main() -> None:
    args = parse_args()
    prompt_missing(args)
    validate_args(args)
    csv_path = args.csv if args.csv else capture(args)
    summary = draw_svg(csv_path)
    for key, value in summary.items():
        print(f"{key.upper()}={value}")


if __name__ == "__main__":
    main()
