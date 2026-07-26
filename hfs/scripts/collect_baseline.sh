#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-./hfs/out}"
DURATION_SEC="${2:-60}"
INTERVAL_SEC="${3:-1}"

mkdir -p "$OUT_DIR"
TS="$(date +%Y%m%d_%H%M%S)"
OUT_FILE="$OUT_DIR/baseline_${TS}.jsonl"

end_ts=$((SECONDS + DURATION_SEC))

read_psi_full() {
  local file="$1"
  awk '/full/ { for(i=1;i<=NF;i++){ if($i ~ /^avg10=/){split($i,a,"="); v=a[2]} } } END{ if(v=="") v=0; print v }' "$file" 2>/dev/null || echo 0
}

read_max_temp_c() {
  local max_mc=0
  local t
  for t in /sys/class/thermal/thermal_zone*/temp; do
    [[ -r "$t" ]] || continue
    local v
    v=$(cat "$t" 2>/dev/null || echo 0)
    [[ "$v" =~ ^[0-9]+$ ]] || v=0
    (( v > max_mc )) && max_mc=$v
  done
  awk -v mc="$max_mc" 'BEGIN{ printf "%.2f", mc/1000.0 }'
}

while (( SECONDS < end_ts )); do
  now_ns=$(date +%s%N)
  cpu_full=$(read_psi_full /proc/pressure/cpu)
  mem_full=$(read_psi_full /proc/pressure/memory)
  io_full=$(read_psi_full /proc/pressure/io)
  temp_c=$(read_max_temp_c)

  printf '{"ts_ns":%s,"event":"baseline_sample","psi_cpu_full":%s,"psi_mem_full":%s,"psi_io_full":%s,"temp_c":%s}\n' \
    "$now_ns" "$cpu_full" "$mem_full" "$io_full" "$temp_c" >> "$OUT_FILE"

  sleep "$INTERVAL_SEC"
done

echo "baseline written to: $OUT_FILE"
