# Migración dual C–SpASM v1

## Objetivo

La Fase 4 agrega una etapa verificable entre “candidata SpASM” y “reemplazo
definitivo”. Linux continúa llamando al símbolo y ABI habituales, mientras SpASM
Kernel puede construir tres variantes mutuamente excluyentes:

```text
C       -> gcd.c                         -> gcd
SpASM   -> gcd_spasm.spasm + entrada     -> gcd
DUAL    -> spasm_gcd_c + spasm_gcd   -> comparador -> gcd
```

No se duplica el algoritmo SpASM. Su único núcleo exporta internamente
`spasm_gcd`; el modo directo utiliza una entrada ensamblador que transfiere
el control sin alterar argumentos ni retorno.

## Semántica dual

Para cada llamada:

1. ejecuta la referencia Linux `spasm_gcd_c(a, b)`;
2. ejecuta la candidata `spasm_gcd(a, b)`;
3. incrementa el contador de llamadas;
4. si divergen, incrementa el contador de errores y emite un mensaje limitado
   por tasa con argumentos y resultados;
5. retorna el resultado SpASM.

Retornar SpASM hace que el modo dual pruebe el comportamiento que tendría la
migración promovida. No se recomienda para producción porque ejecuta dos
algoritmos y añade contabilidad atómica.

## Selección

```text
CONFIG_SPASM_KERNEL_GCD_C=y
CONFIG_SPASM_KERNEL_SPASM_GCD=y
CONFIG_SPASM_KERNEL_GCD_DUAL=y
```

Es un `choice` de Kconfig: exactamente una implementación queda activa.

## Contrato de símbolos

| Modo | Símbolo público | Símbolo C | Símbolo SpASM |
|---|---|---|---|
| C | `gcd` | `gcd` | — |
| SpASM | `gcd` | — | `spasm_gcd` |
| DUAL | `gcd` | `spasm_gcd_c` | `spasm_gcd` |

`gcd` continúa exportado mediante `EXPORT_SYMBOL_GPL`, por lo que consumidores,
módulos y herramientas no necesitan conocer el lenguaje de implementación.

## Verificación

```sh
KERNEL_BUILD=/home/martin/Disco3/kernelLinux/build-spasm-kernel-dual \
	tools/spasm-kernel/project dual-test
```

La prueba comprueba objetos, aislamiento de símbolos, llamadas a ambas
implementaciones, contabilidad atómica, unicidad de `gcd` y exportación en
`vmlinux`.

La promoción de una función a SpASM directo exige equivalencia determinista,
modo dual sin divergencias, ABI v2 conforme, aceptación por `objtool`, ausencia
de regresiones no aceptadas y una validación final en QEMU.
