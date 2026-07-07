---
name: ssh-host-metrics
description: Capture high-frequency CPU and RAM metrics from Linux SSH hosts and plot them over time. Use when Codex needs to sample host load, aggregate CPU, per-logical-CPU utilization, or memory usage from hosts reachable by SSH, especially for short 10 Hz captures over tens of seconds to several minutes.
---

# SSH Host Metrics

## Workflow

Use `scripts/capture_host_metrics.py` to capture `/proc` metrics over SSH, save a CSV, and generate an SVG plot. The script uses one SSH session and runs the sampler remotely, so the sampling cadence is not driven by SSH round trips.

If the user does not provide an SSH host or duration, ask for:

- SSH host, for example `bil-cell-4`
- duration in seconds, for example `30`

Use 10 Hz by default unless the user asks for a different sample rate.

```bash
python3 ~/.codex/skills/ssh-host-metrics/scripts/capture_host_metrics.py --host bil-cell-4 --duration 30
```

Optional arguments:

```bash
python3 ~/.codex/skills/ssh-host-metrics/scripts/capture_host_metrics.py \
  --host bil-cell-4 \
  --duration 120 \
  --hz 10 \
  --out-dir /tmp
```

To run interactively, omit `--host` and/or `--duration`; the script prompts for missing values:

```bash
python3 ~/.codex/skills/ssh-host-metrics/scripts/capture_host_metrics.py
```

## Outputs

The script writes:

- `host-metrics-percpu-<host>-<timestamp>.csv`
- `host-metrics-percpu-<host>-<timestamp>.svg`

The SVG contains:

- aggregate CPU utilization
- RAM used percentage
- per-logical-CPU utilization

The CSV contains raw `/proc/stat` counters and memory values. CPU percentages are computed from adjacent counter deltas during plotting.

## Notes

- A `timeout` return code of `124` is expected when the local timeout stops the SSH sampler after the requested duration.
- Remote shell startup warnings on stderr can be reported as warnings; they do not affect the CSV.
- Per-CPU utilization at 10 Hz can be quantized by kernel CPU tick resolution. Treat single-sample spikes as approximate and look at the trend.
- If a sandbox or network restriction blocks SSH, rerun the command with the required approval.
