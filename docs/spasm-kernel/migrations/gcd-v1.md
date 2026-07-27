# Migración candidata: Linux `gcd` a SpASM

## Alcance

- Implementación de referencia: `lib/math/gcd.c`
- Símbolo Linux: `gcd`
- Exportación: `EXPORT_SYMBOL_GPL`
- Implementación integrada: `gcd` en `lib/math/gcd_spasm.spasm`
- Implementación comparativa: `spasm_gcd_internal` en `samples/spasm/hello_kmod.spasm`
- Tipo ABI x86_64: `(usize, usize) -> usize`

La implementación original no se retira: Kconfig permite seleccionar C o
SpASM durante la fase de estabilización.

## Estrategia

SpASM Kernel llama al símbolo original de Linux y a la implementación SpASM con
los mismos argumentos dentro del módulo cargado en Ring 0. Solamente registra
éxito si cada resultado coincide con Linux y con el valor esperado.

Vectores Ring 0:

| a | b | resultado |
|---:|---:|---:|
| 1071 | 462 | 21 |
| 48 | 18 | 6 |
| 17 | 13 | 1 |
| 0 | 25 | 25 |
| 0 | 0 | 0 |
| `ULONG_MAX` | 0 | `ULONG_MAX` |
| `ULONG_MAX` | `ULONG_MAX - 1` | 1 |
| 2^63 | 2^62 | 2^62 |
| 7540113804746346429 | 4660046610375530309 | 1 |
| 2^32 | 2^16 | 2^16 |

El selftest de host agrega 250000 pares pseudoaleatorios deterministas y
compara la implementación generada con una referencia independiente.

## Selección de construcción

```text
CONFIG_SPASM_KERNEL_GCD_C=y
  -> lib/math/gcd.c

CONFIG_SPASM_KERNEL_SPASM_GCD=y
  -> gcd_spasm.spasm + gcd_spasm_entry.S + gcd_export.c

CONFIG_SPASM_KERNEL_GCD_DUAL=y
  -> gcd.c(spasm_gcd_c) + gcd_spasm.spasm(spasm_gcd) + gcd_dual.c
```

En los tres modos existe un único símbolo público `gcd`. El modo dual llama a
ambas implementaciones, registra cada ejecución y divergencia y retorna el
resultado SpASM.

Los dos builds completos producen un `bzImage`. En ambos `vmlinux` contiene:

```text
T gcd
r __ksymtab_gcd
r __kstrtab_gcd
```

El objeto SpASM entra por la regla genérica `.spasm -> .o` de Kbuild y conserva
el ensamblado intermedio para auditoría. Después usa las mismas opciones de
ensamblado, `objtool`, ORC y controles que una fuente `.S`; mantiene `.text`,
`ENDBR`, ABI x86_64, símbolo global y exportación GPL.

## Diferencia de implementación

Linux utiliza actualmente un algoritmo GCD binario optimizado. La candidata
SpASM utiliza el algoritmo euclídeo con módulo:

```text
while (b != 0) {
	resto = a % b;
	a = b;
	b = resto;
}
return a;
```

La equivalencia requerida es semántica, no una traducción instrucción por
instrucción.

## Estado

El reemplazo seleccionable está implementado y ambos kernels construyen
completos. Las pruebas del backend pasan 30/30, la conformidad ABI v2 pasa
3/3 grupos y la equivalencia de host pasa
10 vectores más 250000 casos pseudoaleatorios.

La medición inicial de un millón de llamadas muestra que la implementación
euclídea SpASM tarda aproximadamente 3,2 veces el algoritmo binario optimizado
de Linux en este host. Es una deuda de rendimiento conocida; la ruta C no debe
retirarse hasta implementar u optimizar el algoritmo SpASM.

La validación final de arranque está pendiente únicamente porque el entorno
actual no dispone de `qemu-system-x86_64`. De acuerdo con la regla del proyecto,
este milestone no se integra en Git hasta obtener en QEMU:

```text
spasm: Equivalencia Linux gcd y SpASM correcta
[spasm-init] RESULTADO: OK
```
