# HFS Workspace (M1 Observability)

Este directorio contiene la base inicial de HFS dentro del arbol del kernel Linux 6.19.14.

Objetivo de M1:
- instrumentar observabilidad para decisiones de scheduler y salud del sistema
- definir contratos de eventos y metricas antes de cambios de politica
- habilitar baseline reproducible contra EEVDF

Estructura:
- `contracts/`: contratos de eventos y campos minimos
- `metrics/`: catalogo KPI, umbrales y metodo de medicion
- `observability/`: plan de instrumentacion por fuente (tracepoints, PSI, thermal)
- `scripts/`: utilidades de captura baseline

Alcance M1:
- sin cambios funcionales en ruta critica del scheduler
- solo captura y auditoria de señales

Reglas obligatorias vigentes:
- `HFS-SPASM-001`: SpASM sin heurística.
- `HFS-RESOURCE-001`: SCX/eBPF administra SATELLITE; CORE protegido queda fuera de su control directo.
- `HFS-EEVDF-001`: HFS no reemplaza EEVDF en CORE.
- `HFS-EEVDF-002`: SCX/eBPF inicia en SATELLITE/UNKNOWN.
- `HFS-LANG-001`: kernel inicial en C/asm/eBPF; Rust fuera de alcance inicial.
- `HFS-BRIDGE-001`: SpASM propone política; C valida; kernel aplica.
- `HFS-BRANCH-001`: `linux-6.19.14` se usa como rama de prototipo.
