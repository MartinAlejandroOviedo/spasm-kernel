# HFS-Linux Branch Manifesto

## Posición del proyecto
HFS-Linux es una bifurcación experimental de Linux 6.19.14 orientada a:
- estabilidad del sistema
- fluidez de experiencia de usuario
- protección de hardware
- reducción gradual de riesgos heredados de C mediante SpASM

No es un reemplazo total de Linux ni un parche menor aislado.

## Linaje y diferenciación
Linux original
├── Camino principal: C + Rust
│   ├── seguridad de memoria
│   ├── integración gradual
│   ├── coexistencia con C
│   └── evolución upstream
└── Camino alternativo: C + SpASM
    ├── política formal
    ├── código pequeño y auditable
    ├── sin heurística en SpASM
    ├── control CORE/SATELLITE
    ├── cuidado de hardware
    └── bifurcación experimental

Diferencia filosófica:
- Rust busca proteger al programador del error de memoria.
- SpASM obliga a declarar de forma explícita qué hace el código, qué toca, qué devuelve y qué límites respeta.

ADN compartido Linux:
- scheduler base
- cgroups
- eBPF
- VFS
- modelo monolítico
- compatibilidad POSIX
- drivers
- user space Linux

Frase oficial corta:
- Mismo ADN Linux, distinta evolución: uno aprende Rust; el otro aprende SpASM.

## Principios
1. No competir contra EEVDF en CORE protegido.
2. No intervenir en `stop/dl/rt/idle` en fase inicial.
3. No heurística en SpASM.
4. No acceso directo a hardware desde SpASM.
5. No reemplazo explosivo de C.
6. No `BUG()` evitables como estrategia de control de errores.
7. No inlining agresivo sin evidencia de mejora.
8. No typedefs decorativos en código nuevo de puente.
9. No saltos arbitrarios fuera de control estructurado.
10. Todo cambio debe tener fallback.

## Arquitectura de la rama
- Base Linux upstream-compatible (6.19.14 prototipo).
- CORE protegido sobre scheduler base/EEVDF.
- SATELLITE gobernado por cgroups + SCX/eBPF.
- HFS resource governor con perfiles y límites.
- SpASM policy engine formal (externo al fast path).
- Puente C validado: SpASM propone, C valida, kernel aplica.
- Rollback seguro al scheduler base.

## Promesa técnica
HFS-Linux promete explorar un camino más:
- predecible
- fluido bajo carga mixta
- conservador con el hardware
- auditable en política de recursos

No promete:
- compatibilidad total inmediata
- mejor rendimiento universal
- reemplazo de Rust
- eliminación total de bugs de memoria
- seguridad absoluta por usar SpASM

## Roadmap de bifurcación
R0 Base limpia:
- importar Linux 6.19.14
- compilar sin cambios
- medir baseline EEVDF

R1 HFS skeleton:
- jerarquía CORE/SATELLITE/UNKNOWN
- cgroups
- observabilidad
- logs

R2 Resource governor:
- cupos
- memory.low/high
- io.weight/io.max
- perfiles Balanced/Fluid/Longevity

R3 SCX/eBPF SATELLITE:
- scheduler experimental solo para SATELLITE
- fallback automático

R4 SpASM bridge:
- ABI C<->SpASM
- política formal
- implementación C de referencia
- pruebas de equivalencia

R5 SpASM modules:
- token bucket
- score formal
- FSM térmica
- validación de perfiles

R6 Hardening:
- soak 24h/72h
- watchdog
- rollback
- bloqueo de reactivación automática tras fallo

R7 Public experimental branch:
- documentación
- manifiesto
- benchmarks
- guía de contribución

## Regla filosófica
No bifurcamos Linux para hacerlo más complejo.
Lo bifurcamos para imponer límites más claros.
