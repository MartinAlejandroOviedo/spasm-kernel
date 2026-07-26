# Contrato SpASM target Nice Kernel x86_64 v1

## Objetivo

Separar el consumidor Nice Kernel de la implementación provisional del backend.
Kbuild y `tools/spasm-kernel/project` no deben conocer el parser ni el generador
utilizados internamente.

El identificador público del target es:

```text
nice-kernel-x86_64
```

## Entrada ejecutable

Mientras el dispatcher externo `spasmc.py` incorpora soporte para extensiones,
la entrada canónica dentro de Nice Kernel es:

```sh
tools/spasm-kernel/spasm-target-nice-kernel-x86_64 \
    SOURCE.spasm --out-dir BUILD_DIR
```

Opciones:

- `SOURCE.spasm`: fuente obligatorio;
- `--out-dir DIR`: directorio obligatorio para artefactos generados;
- `--emit asm`: representación de salida; en v1 solamente `asm`;
- `--target nice-kernel-x86_64`: comprobación opcional del identificador;
- `--verbose`: muestra el backend ejecutado.

## Salidas

Si la compilación termina con estado cero, el directorio contiene:

```text
<module>_native.S
Makefile
```

El target no ejecuta Kbuild. El consumidor controla la configuración, versión
y árbol del kernel usados para producir el objeto y el módulo `.ko`.

## Errores

- errores de invocación: estado `2`;
- fuente inexistente o extensión incorrecta: estado `2`;
- rechazo sintáctico o semántico: estado distinto de cero;
- no se permite éxito silencioso ni fallback a C.

## Restricciones v1

- arquitectura exclusiva: x86_64;
- formato intermedio: ensamblador GNU para Kbuild;
- implementación nativa: nunca se genera C;
- backend provisional:
  `tools/spasm-kernel/spasm-kmod-native.py`.

Este contrato puede permanecer estable cuando el parser y el análisis semántico
pasen al frontend oficial de SpASM.
