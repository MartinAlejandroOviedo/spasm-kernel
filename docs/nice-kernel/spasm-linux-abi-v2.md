# Contrato Linux–SpASM x86_64 ABI v2

## Estado y alcance

Este documento es la norma ejecutable de Fase 2 para funciones de Nice Kernel
compiladas desde SpASM. Define qué debe observar Linux sin depender del lenguaje
fuente. Aplica al target:

```text
nice-kernel-x86_64
```

V2 cubre funciones ordinarias incorporadas a `vmlinux` y el módulo comparativo
Ring 0. Entradas de interrupción, syscalls, `noinstr`, cambio de contexto,
`naked`, `noreturn`, CFI/KCFI tipado y ABI vectorial quedan fuera del contrato:
el compilador debe rechazarlos o no ofrecer sintaxis para declararlos.

## Entrada y modos de salida

Módulo:

```sh
SPASMC_TARGET_PATH=tools/spasm-kernel \
	python3 /ruta/spasmc.py modulo.spasm \
	--target nice-kernel-x86_64 --out-dir BUILD_DIR
```

Objeto builtin:

```sh
SPASMC_TARGET_PATH=tools/spasm-kernel \
	python3 /ruta/spasmc.py funcion.spasm \
	--target nice-kernel-x86_64 --out BUILD_DIR/funcion.S
```

No existe fallback a C. Un error sintáctico, semántico o ABI produce estado
distinto de cero y no debe dejar un artefacto que parezca válido.

## Identidad de símbolos

Una función builtin publica exactamente el nombre declarado:

```text
export fn nice_gcd_spasm(a: usize, b: usize) -> usize
```

Reglas:

- el símbolo ELF se llama exactamente como la función exportada;
- es `GLOBAL`, `FUNC`, definido una sola vez;
- las funciones sin `export` son `LOCAL` y usan el prefijo `spasm_fn_`;
- `export fn` sólo se admite en el modo builtin;
- `init_module` y `cleanup_module` están reservados;
- `EXPORT_SYMBOL_GPL` continúa siendo responsabilidad explícita de Kbuild o de
  un objeto de metadatos separado;
- los consumidores existentes no cambian sus declaraciones ni llamadas.

Una migración puede usar una entrada ABI mínima para desacoplar el nombre
público Linux del núcleo reutilizable. En `gcd`, `gcd_spasm_entry.S` preserva
el único símbolo público `gcd` y transfiere el control a
`nice_gcd_spasm`. El modo dual reemplaza esa entrada por el comparador, sin
cambiar la firma observada por consumidores.

## Convención de llamada

V2 sigue la ABI usada por el kernel Linux x86_64 para enteros y punteros:

| Posición | Registro |
|---:|:---|
| 1 | `rdi` |
| 2 | `rsi` |
| 3 | `rdx` |
| 4 | `rcx` |
| 5 | `r8` |
| 6 | `r9` |
| retorno | `rax` |

No se admiten más de seis argumentos. Los tipos exportables estables son:

```text
u64 i64 usize isize ptr<T> ptr<T>?
```

Los tipos `u8/i8/u16/i16/u32/i32/bool` siguen disponibles internamente, pero
V2 los rechaza en una firma `export fn` hasta que el backend implemente
extensión, truncado y compatibilidad C completos.

## Registros y pila

- `rbx`, `rbp`, `r12`, `r13`, `r14` y `r15` son preservados por el callee.
- El backend actual sólo usa `rbp` de ese grupo y lo restaura en cada retorno.
- Después de la dirección de retorno, `rsp % 16 == 8`; el prólogo guarda `rbp`
  y reserva un múltiplo de 16, por lo que cada `call` sale alineado.
- No se utiliza red zone.
- Cada camino normal y de error restaura exactamente el tamaño reservado.
- Los retornos usan `RET` del kernel, no un `ret` escrito directamente, para
  respetar `CONFIG_RETHUNK`.
- V2 no permite modificar el direction flag ni asumir estado de SIMD/FPU.

## Secciones ELF

Objeto builtin:

| Contenido | Sección |
|:---|:---|
| funciones exportadas | `.text`, `AX` |
| datos mutables | `.data`, `WA` |
| datos cero | `.bss`, `WA` |
| pila no ejecutable | `.note.GNU-stack`, sin `X` |

Módulo:

| Contenido | Sección |
|:---|:---|
| funciones internas | `.spasm.text`, `AX` |
| entrada | `.init.text`, `AX` |
| salida | `.exit.text`, `AX` |
| mensajes | `.rodata.str1.1`, `AMS` |
| licencia y descripción | `.modinfo`, `A` |

Las funciones se alinean a 16 bytes. Un objeto builtin no puede contener
`.modinfo`, `init_module`, `cleanup_module` ni secciones `.spasm.*`.

## IBT, objtool y unwinding

- Toda función comienza con `ENDBR`; con `CONFIG_X86_KERNEL_IBT=y` se materializa
  como `endbr64`.
- El patrón de prólogo y epílogo debe ser reconocido por `objtool --stackval`.
- `objtool --rethunk` y `--sls` no deben emitir advertencias.
- `objtool --orc` debe poder producir metadatos sin excepciones
  `STACK_FRAME_NON_STANDARD`.
- El enlace completo debe generar `.orc_unwind` y `.orc_unwind_ip`.
- Las entradas del módulo usan una función SpASM real y alias compatibles
  `init_module/cleanup_module`, más referencias addressable, equivalentes al
  contrato de `module_init()`/`module_exit()`.

No se aceptan excepciones para silenciar objtool en una función ordinaria.

## Relocaciones y llamadas externas

- Las llamadas internas resuelven a símbolos locales `spasm_fn_*`.
- Una llamada Linux requiere `extern fn` y una firma incluida en la allowlist.
- Una firma o símbolo no autorizado se rechaza antes de generar ensamblador.
- Para el núcleo `nice_gcd_spasm`, las únicas relocaciones de texto esperadas
  son las del `RET` del kernel hacia `__x86_return_thunk`.
- No se permiten relocaciones absolutas en `.text`.

## Atributos aún no autorizados

V2 no expone atributos de fuente `init`, `exit`, `noinstr`, `noreturn`,
`__percpu`, `__user`, `__iomem`, `naked` o secciones arbitrarias. Su ausencia
es deliberada: cada atributo modifica reglas de lifetime, instrumentation,
unwinding o memoria y deberá incorporarse con validación propia.

Hasta entonces:

- `on load` y `on unload` son las únicas entradas de módulo;
- una función builtin ordinaria siempre va a `.text`;
- cualquier migración que necesite otro atributo queda bloqueada por contrato.

## Criterio de conformidad

Una migración V2 se acepta solamente si:

1. pasa `run_backend_tests`;
2. pasa `run_abi_conformance`;
3. construye el objeto y el kernel completo con Kbuild;
4. conserva nombre, tipo, visibilidad y exportación Linux;
5. objtool no informa advertencias;
6. el kernel arranca y completa `verify-poc` en QEMU.

El punto 6 continúa siendo obligatorio aunque los cinco anteriores pasen.
