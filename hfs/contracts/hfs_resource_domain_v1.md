# HFS Resource Domain v1

## Regla obligatoria
`HFS-RESOURCE-001`:
- SCX/eBPF no administra la totalidad del sistema.
- SCX/eBPF administra el dominio `SATELLITE` y, opcionalmente, solo la parte flexible de `CORE`.
- SCX/eBPF nunca puede invadir la reserva mínima protegida de `CORE`.

## Modelo formal

```text
TOTAL = CORE_RESERVED + SATELLITE_POOL + EMERGENCY_RESERVE
```

Definiciones:
- `CORE_RESERVED`: piso protegido, intocable para SATELLITE cuando CORE lo demanda.
- `SATELLITE_POOL`: remanente administrado por SCX/eBPF.
- `EMERGENCY_RESERVE`: no asignado normalmente; se activa para input/audio/compositor/fallback.

Préstamo controlado:
- SATELLITE puede usar recursos ociosos de CORE solo como préstamo revocable.
- Si CORE despierta o exige recursos, SATELLITE devuelve el préstamo inmediatamente.

## Perfiles iniciales
`Balanced`:
- CORE protegido 40%
- SATELLITE administrado 45%
- reserva emergencia 15%

`Fluid UX`:
- CORE protegido 55%
- SATELLITE administrado 30%
- reserva emergencia 15%

`Hardware Longevity`:
- CORE protegido 45%
- SATELLITE administrado 25%
- reserva cooldown 30%

`Emergency`:
- CORE protegido 70%
- SATELLITE administrado 5%
- reserva emergencia 25%

## Autoridad de SCX/eBPF
Permitido:
- planificar `/hfs/satellite/*`
- planificar `/hfs/unknown/*` con cupo bajo
- observar métricas de CORE para liberar presión

Prohibido:
- degradar `/hfs/core/critical`
- degradar `/hfs/core/input`
- degradar `/hfs/core/audio`
- degradar `/hfs/core/compositor`
- consumir `EMERGENCY_RESERVE` sin transición de estado formal

## Estructura cgroup sugerida
```text
/sys/fs/cgroup/hfs/
├── core/
│   ├── critical/
│   ├── input/
│   ├── audio/
│   ├── compositor/
│   └── interactive/
├── satellite/
│   ├── batch/
│   ├── besteffort/
│   ├── ioheavy/
│   └── throttled/
└── unknown/
```
