#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
isaac_python="${ISAAC_SIM_PATH:-/opt/IsaacSim}/python.sh"
output_dir="${1:-$script_dir/outputs/run}"
"$isaac_python" "$script_dir/grasp_demo.py" --isaaclab "${ISAAC_LAB_PATH:-/opt/IsaacLab}" --render --output "$output_dir"
"$isaac_python" "$script_dir/compose_video.py" "$output_dir"
