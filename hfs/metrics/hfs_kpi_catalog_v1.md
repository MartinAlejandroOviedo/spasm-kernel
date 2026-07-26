# HFS KPI Catalog v1

## Fluidez
- input latency p95/p99 (ms)
- wakeup-to-run latency p95/p99 (us)
- jitter de wakeups (stddev)
- audio underruns (count/min)

## Estabilidad
- softlockups (count)
- stalls de scheduler (count)
- PSI cpu full avg10/avg60/avg300
- PSI mem full avg10/avg60/avg300
- PSI io full avg10/avg60/avg300

## Hardware
- temperatura max/p95 por zona
- tiempo en throttling (s)
- frecuencia de throttling (count)
- tiempo en estado thermal `hot|critical`

## Justicia
- wait-time por clase p95/p99
- starvation_count por clase
- deuda media de cupo por clase
- cumplimiento de cupos por ventana (%)

## Baseline (obligatorio)
- comparar siempre contra scheduler base en mismo hardware/workload/config
- registrar fecha, kernel config y workload exacto
