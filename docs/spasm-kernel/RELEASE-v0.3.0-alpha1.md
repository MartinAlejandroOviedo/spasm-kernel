# spasm-kernel v0.3.0-alpha1

Fecha: 2026-07-29  
Kernel: `6.19.14-spasm-kernel-desktop-amd64`  
Arquitectura: `x86_64`

## Alcance

Esta alpha cierra el Paso 0 de consolidación. Conserva las cuatro migraciones
originales e incorpora `_bin2bcd`, `int_pow`, `lcm` y `lcm_not_zero`. Las
funciones mantienen sus símbolos públicos Linux y permiten selección
C/SpASM/dual mediante Kconfig.

Machine Care v1 se distribuye como política SpASM y agente global
observacional. No cambia scheduler, frecuencia, prioridades ni cgroups.

## Verificación

- Build completo con GCC 14 y compilador propio
  `/home/martin/Documentos/SpASM/tools/spasmc.py`.
- `verify-all`: 9 aprobadas, 0 fallidas.
- Backend SpASM: 31 aprobadas, 0 fallidas.
- Equivalencia ampliada: 200.100 vectores sin discrepancias.
- Arranque QEMU con `/usr/bin/qemu-system-x86_64`: OK.
- Objtool/ORC: sin warnings después de eliminar saltos inalcanzables.
- 139 módulos empaquetados; 139 firmados con SHA-256; `vermagic` exacto.
- Ciclo Debian aislado: instalación, actualización, rollback, remove y purge:
  OK.

## Paquetes

- `spasm-kernel-image-6.19.14-spasm-kernel-desktop-amd64`
- `spasm-kernel-modules-core-6.19.14-1`
- `spasm-kernel-drivers-desktop-6.19.14-1`
- `spasm-kernel-machine-care`

Versión Debian: `0.3.0~alpha1-1`.

Los `.deb` se generan en `packages/0.3.0-alpha1/` y se publican como assets de
release, no dentro del historial Git.

## SHA-256

```text
cdd96012ca5c92ccdbc7404ce511fabf9758a943d7e3e8b89f05fa8d063edf9c  spasm-kernel-drivers-desktop-6.19.14-1_0.3.0~alpha1-1_amd64.deb
94705db9aae3a2712b225685a99e4baa2e0a856bd44896b458d8f20e25208c8e  spasm-kernel-image-6.19.14-spasm-kernel-desktop-amd64_0.3.0~alpha1-1_amd64.deb
62463c4a3dc032c0ca8a7a3ba1cb0df8c640b8649ec4024dc1d15a71101fde1d  spasm-kernel-machine-care_0.3.0~alpha1-1_amd64.deb
d20916f96f2b1db1f07aa16ebd4506fdb70ed96bc1c559a304b054e510326544  spasm-kernel-modules-core-6.19.14-1_0.3.0~alpha1-1_amd64.deb
```

## Límite conocido

El perfil usado para validar compatibilidad todavía habilita una matriz muy
amplia, incluidos drivers legacy y staging. El Paso 1 debe separar un
`desktop` contemporáneo de `drivers-extra/legacy`, manteniendo siempre en
`core` almacenamiento, filesystem raíz, USB HID y consola.

