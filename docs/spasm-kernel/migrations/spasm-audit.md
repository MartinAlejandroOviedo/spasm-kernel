# Auditoría SpASM — Estado de características (Fase 6)

Compilador spasmc + backend spasm-kernel-x86_64 (spasm-kmod-native.py)
Fecha: 2026-07-27

---

## Características implementadas ✅

| Feature | Sintaxis | Notas |
|---|---|---|
| Funciones internas | `fn nombre(a: tipo) -> tipo { }` | Hasta 6 params, `export fn` para símbolo global |
| Tipos enteros | `u8`–`u64`, `i8`–`i64`, `usize`, `isize`, `bool` | System V ABI x86_64 |
| Variables locales | `var x = 42;` / `var x: i64 = 42;` | Stack-allocated, sin estado global |
| Reasignación | `x = x + 1;` | Sólo variables no-recurso |
| Aritmética | `+`, `-`, `*`, `/`, `%` | División protegida: /0 → `-EDOM` |
| Condicionales | `if (a == b) { } else { }` | Anidables, con comparadores `<`, `>`, `<=`, `>=`, `==`, `!=` |
| Bucles | `while (i < 10) { }` | Presupuesto de 100k iteraciones, `-ELOOP` si se agota |
| return | `return expr;` / `return -ENOENT;` | Libera recursos automáticamente |
| klog | `klog("mensaje")` | Llama a `_printk` con nivel 6 |
| Recursos (kmalloc) | `recurso buf = kalloc<u8>(256) else return -ENOMEM` | Límite 1 MiB, check estático de uso/liberación |
| Memoria tipada | `guardar<u32>(buf, 0, val)` / `cargar<u32>(buf, 0)` | Check alineación + bounds, estático y dinámico |
| Punteros tipados | `ptr<u8>` / `ptr<u8>?` | Nullable con `?`, sin aritmética de punteros |
| Funciones externas | `extern fn gcd(a: usize, b: usize) -> usize` | Lista blanca KERNEL_EXTERN_ALLOWLIST |
| Built-in objects | `--kind builtin` | Sin bloques on load/on unload |
| Encabezados modinfo | `module "name"`, `license "GPL"`, etc. | Sólo en modo module |
| Bounds checking | Acceso dinámico a memoria con índice variable | Offset validado en runtime |
| Budget loops | `while` con contador de 100k | Retorno `-ELOOP` si se agota |
| objtool compliance | `ENDBR`, `.p2align`, `.size`, `.type` | Sección `.text`/`.spasm.text` |

---

## Características pendientes ❌ (Fase 6)

| # | Feature | Prioridad | Justificación (función kernel) | Complejidad |
|---|---|---|---|---|
| 1 | **Estructuras compatibles con C** | Alta | `reciprocal_value`, `rational_best_approximation`, acceso a campos | Media |
| 2 | **Arrays de tamaño fijo** | Alta | Tablas de lookup, `hex_asc[]`, buffers locales | Media |
| 3 | **Enums y constantes con nombre** | Alta | Códigos de error, flags, constantes como `GFP_KERNEL` | Baja |
| 4 | **Punteros a función / callbacks** | Alta | `bsearch`, `sort`, `sort_r`, `list_sort` | Alta |
| 5 | **Volatile** | Media | MMIO, registros de dispositivo | Baja |
| 6 | **Variables globales (.data/.bss)** | Media | Contadores, flags, tablas estáticas | Media |
| 7 | **Atomics** | Media | `refcount_*`, `rcuref_*`, `llist_*` | Alta |
| 8 | **Barreras de memoria** | Media | `smp_mb()`, `barrier()`, sincronización | Media |
| 9 | **Bitfields** | Baja | Campos de bits en registros HW | Baja |
| 10 | **per-CPU** | Baja | Variables por CPU, estadísticas | Alta |
| 11 | **Inline assembly controlado** | Baja | Optimizaciones específicas de plataforma | Alta |
| 12 | **Slices dinámicos** | Baja | Manipulación de buffers con longitud | Alta |
| 13 | **Anotaciones de contexto/ownership** | Baja | Verificación estática de locks, IRQ context | Alta |

---

## Recomendaciones

1. **Empezar con structs + arrays + enums** (prioridad alta, baja complejidad) — desbloquean las siguientes funciones del catálogo:
   - `reciprocal_value` (usa struct)
   - `hex_asc[]` (array constante)
   - `rational_best_approximation` (struct + aritmética)

2. **Luego function pointers** — necesarios para `bsearch`/`sort`. Requiere:
   - Sintaxis de tipo `fn(usize, usize) -> i32`
   - Declaración `var cmp: fn(usize, usize) -> i32 = ...`
   - Llamada indirecta `call *%rax`

3. **Posponer atomics + per-CPU** hasta tener funciones concretas que los justifiquen (Fase 7).

---

## Archivos relevantes

| Archivo | Rol |
|---|---|
| `tools/spasm-kernel/spasm-kmod-native.py` (1458 líneas) | Backend nativo: parser + codegen x86_64 |
| `tools/spasm-kernel/spasm-target-spasm-kernel-x86_64` (73 líneas) | Entry point para target externo |
| `~/Documentos/SpASM/tools/spasmc.py` (159 líneas) | Dispatcher central |
| `~/Documentos/SpASM/tools/spasm-asm-gen.py` (2121 líneas) | Backend Linux userspace (str_slice, etc.) |
