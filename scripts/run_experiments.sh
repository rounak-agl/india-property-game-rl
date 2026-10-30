#!/usr/bin/env bash
# Run every experiment config x seed, N jobs in parallel (default 3).
#   scripts/run_experiments.sh [jobs] [config ...]
set -euo pipefail
cd "$(dirname "$0")/.."
JOBS="${1:-3}"; shift || true
CONFIGS=("$@")
[ ${#CONFIGS[@]} -eq 0 ] && CONFIGS=(experiments/e[0-9]*.yaml)
mkdir -p results/logs
for cfg in "${CONFIGS[@]}"; do
  for seed in 0 1 2; do echo "$cfg $seed"; done
done | xargs -P "$JOBS" -L 1 bash -c '
  name=$(basename "$0" .yaml)
  .venv/bin/python -W ignore -m src.rl.train --config "$0" --seeds "$1" > "results/logs/${name}_s$1.log" 2>&1 \
    && echo "done  ${name}_s$1" || echo "FAIL  ${name}_s$1"'
