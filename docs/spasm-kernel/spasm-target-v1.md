# Contrato SpASM target spasm-kernel x86_64 v1

## Objetivo

Separar el consumidor spasm-kernel de la implementación provisional del backend.
Kbuild y `tools/spasm-kernel/project` no deben conocer el parser ni el generador
utilizados internamente.

El identificador público del target es:

```text
spasm-kernel-x86_64
```

## Entrada oficial

spasm-kernel registra el directorio del target mediante `SPASMC_TARGET_PATH` y
compila siempre a través del dispatcher oficial:

```sh
SPASMC_TARGET_PATH=tools/spasm-kernel \
    /home/martin/Documentos/SpASM/tools/spasmc.py \
    SOURCE.spasm \
    --target spasm-kernel-x86_64 \
    --out-dir BUILD_DIR
```

El dispatcher descubre esta entrada ejecutable:

```text
tools/spasm-kernel/spasm-target-spasm-kernel-x86_64
```

Opciones del target:

- `SOURCE.spasm`: fuente obligatorio;
- `--out-dir DIR`: directorio obligatorio para artefactos generados;
- `--emit asm`: representación de salida; en v1 solamente `asm`;
- `--target spasm-kernel-x86_64`: comprobación opcional del identificador;
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

Este contrato permanece estable cuando el parser y el análisis semántico pasen
al frontend compartido de SpASM. Un target desconocido o no registrado produce
un error explícito; nunca se utiliza el generador C como fallback.

El contrato de compatibilidad con Linux, ABI y objetos builtin se amplía en
`spasm-linux-abi-v2.md`. V1 continúa describiendo la entrada histórica para
módulos; V2 es la norma aplicable a nuevas migraciones.
