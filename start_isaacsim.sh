#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
isaac_python="${ISAAC_SIM_PATH:-/opt/IsaacSim}/python.sh"
output_dir="${1:-$script_dir/outputs/interactive}"
exec "$isaac_python" "$script_dir/grasp_demo.py" \
  --isaaclab "${ISAAC_LAB_PATH:-/opt/IsaacLab}" \
  --gui --wait-for-start --keep-open --output "$output_dir"
