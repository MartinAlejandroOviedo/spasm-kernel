# M1 Instrumentation Plan

Objetivo: obtener baseline confiable sin alterar politicas de scheduling.

Fuentes:
1. Scheduler tracepoints (`sched_switch`, `sched_wakeup`, `sched_wakeup_new`)
2. PSI (`/proc/pressure/{cpu,memory,io}`)
3. Thermal (`/sys/class/thermal/thermal_zone*/`)
4. CPU freq/throttle cuando aplique (`cpufreq`, counters de throttling)

Herramientas sugeridas:
- `trace-cmd` o `perf sched`
- lectura periodica de `/proc` y `/sys`
- export a JSONL para correlacion temporal

Entregables M1:
- captura baseline de 10-30 min en idle + carga mixta
- reporte KPI inicial
- validacion de pipeline de eventos

No-go en M1:
- sin cambios en `kernel/sched/fair.c`, `rt.c` o `core.c`
- sin habilitar politica SCX custom
