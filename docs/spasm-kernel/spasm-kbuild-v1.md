# Integración SpASM–Kbuild v1

## Objetivo

La Fase 3 convierte a SpASM en una fuente reconocida directamente por Kbuild.
Un subsistema solamente declara el objeto que necesita:

```make
obj-y += ejemplo.o
```

Si existe `ejemplo.spasm`, Kbuild ejecuta:

```text
ejemplo.spasm -> spasmc -> ejemplo.spasm.S -> CC/AS -> ejemplo.o
```

El Makefile del subsistema no conoce el parser, el backend ni la ubicación
personal del compilador.

## Variables

- `SPASMC`: ruta al compilador propio `spasmc.py`.
- `SPASM_TARGET`: target del compilador; por defecto
  `spasm-kernel-x86_64`.
- `SPASM_TARGET_PATH`: directorio de targets; por defecto
  `tools/spasm-kernel` dentro del árbol.

La ruta local usada actualmente se pasa al invocar `make` y no queda embebida
en el kernel:

```sh
make O=/ruta/build ARCH=x86_64 \
	SPASMC=/home/martin/Documentos/SpASM/tools/spasmc.py
```

## Propiedades

- La fuente, el compilador local cuando es una ruta, el dispatcher del target
  y el backend nativo participan en las dependencias.
- Los cambios de comando quedan en el archivo `.cmd` normal de Kbuild.
- Una segunda construcción sin cambios no recompila el objeto.
- El ensamblado generado queda en el directorio de build para diagnóstico y
  se registra como target limpiable.
- El ensamblado usa `KBUILD_AFLAGS`, el ensamblador del kernel, `objtool`,
  versionado de símbolos y las advertencias normales de objetos compartidos.
- `.S` conserva precedencia cuando un subsistema ofrece deliberadamente tanto
  una fuente `.S` como una `.spasm` con el mismo nombre base.
- La salida debe obedecer `docs/spasm-kernel/spasm-linux-abi-v2.md`; Kbuild no
  sustituye la validación semántica del backend.

## Primera migración

`lib/math/Makefile` declara `gcd_spasm.o` en los modos SpASM y dual. La
implementación está en
`lib/math/gcd_spasm.spasm`; no contiene ninguna regla de compilación especial.

## Verificación

```sh
tools/testing/selftests/spasm-kernel/run_kbuild_spasm
```

La prueba comprueba construcción incremental, reconstrucción determinista,
símbolos ELF, ausencia de entradas reservadas para módulos, aceptación por
`objtool` y presencia de ORC en `vmlinux`.

Estado de cierre de Fase 3:

- integración Kbuild: 3/3;
- backend: 30/30;
- ABI Linux–SpASM v2: 3/3;
- equivalencia `gcd`: 10 vectores y 250000 pares pseudoaleatorios;
- kernels completos C y SpASM: `bzImage` generado;
- módulo SpASM e initramfs: generados;
- arranque final QEMU: pendiente por falta de `qemu-system-x86_64` en el host.
