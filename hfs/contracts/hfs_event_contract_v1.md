# HFS Event Contract v1

Regla global:
- `HFS-SPASM-001`: SpASM no usa heurística.

Eventos mínimos:
- `process_classified`
- `process_reclassified`
- `score_changed`
- `budget_exhausted`
- `budget_refilled`
- `thermal_state_changed`
- `memory_pressure_detected`
- `io_pressure_detected`
- `fallback_level_changed`
- `spasm_policy_updated`
- `spasm_timeout`
- `scx_error`

Campos mínimos por evento:
- `ts_ns`: timestamp monotonic en ns
- `event`: nombre del evento
- `pid`: process id
- `tgid`: thread group id
- `comm`: command name
- `class_prev`: clase anterior o `""`
- `class_new`: clase nueva o `""`
- `score`: score efectivo o `-1` si no aplica
- `cpu`: cpu id o `-1`
- `cgroup`: path de cgroup o `""`
- `reason`: motivo corto basado en contrato
- `profile`: perfil activo (`balanced|fluid_ux|longevity|safe_mode`)
- `thermal_state`: `normal|warm|hot|critical|cooldown`
- `psi_cpu_full`: valor actual PSI cpu full
- `psi_mem_full`: valor actual PSI mem full
- `psi_io_full`: valor actual PSI io full

Formato recomendado:
- JSON Lines (un evento por línea)

Ejemplo:
```json
{"ts_ns": 1234567890, "event": "process_reclassified", "pid": 1822, "tgid": 1822, "comm": "firefox", "class_prev": "UNKNOWN", "class_new": "CORE-INTERACTIVE", "score": 742, "cpu": 5, "cgroup": "/hfs/core/interactive", "reason": "cgroup_contract_match", "profile": "fluid_ux", "thermal_state": "warm", "psi_cpu_full": 0.02, "psi_mem_full": 0.00, "psi_io_full": 0.01}
```
