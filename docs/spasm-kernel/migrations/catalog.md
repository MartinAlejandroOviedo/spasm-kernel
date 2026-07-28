# Catálogo de migración Linux → SpASM

Configuración: x86_64 defconfig + spasm-kernel Kconfig
Kernel: 6.19.14
Migración: símbolo `gcd` completada (Fase 1)

---

## 1. Funciones matemáticas y aritméticas puras

Sin estado global, sin efectos secundarios, contexto irrestricto.

| Función | Firma | Consumidores | Estado | Efectos | Riesgo |
|---|---|---|---|---|---|
| `int_sqrt` | `unsigned long -> unsigned long` | mm/, drivers/ | ✗ | ✗ | Bajo |
| `int_pow` | `u64, unsigned int -> u64` | drivers/ | ✗ | ✗ | Bajo |
| `intlog2` | `unsigned long -> unsigned int` | drivers/, lib/ | ✗ | ✗ | Bajo |
| `intlog10` | `unsigned int -> unsigned int` | drivers/ | ✗ | ✗ | Bajo |
| `reciprocal_value` | `u32 -> struct reciprocal_value` | mm/, drivers/ | ✗ | ✗ | Bajo |
| `reciprocal_value_adv` | `u32, u8 -> struct reciprocal_value_adv` | mm/ | ✗ | ✗ | Bajo |
| `lcm` | `unsigned long, unsigned long -> unsigned long` | lib/, mm/ | ✗ | ✗ | Bajo |
| `rational_best_approximation` | `u64,u64,u64,u64 -> void` | drivers/ | ✗ | ✗ | Medio |

**Pruebas requeridas**: unitarias con valores extremos, comparación C/SpASM, random fuzzing.

---

## 2. Manipulación de bits

Operaciones sin estado, usan registros o instrucciones especializadas.

| Función | Firma | Consumidores | Asm actual | Riesgo |
|---|---|---|---|---|
| `__sw_hweight32` | `unsigned int -> unsigned int` | todo el kernel | optimizado con `popcnt` | Bajo |
| `__sw_hweight64` | `unsigned long -> unsigned long` | todo el kernel | idem | Bajo |
| `_find_first_bit` | `const ulong*,ulong -> ulong` | mm/, drivers/ | `ffz`/`bsf` | Medio |
| `_find_next_bit` | `const ulong*,ulong,ulong -> ulong` | mm/, drivers/ | loop + `bsf` | Medio |
| `_find_first_zero_bit` | `const ulong*,ulong -> ulong` | mm/, drivers/ | `bsf` | Medio |
| `_find_last_bit` | `const ulong*,ulong -> ulong` | mm/, fs/ | `bsr` | Medio |
| `find_next_clump8` | `const ulong*,ulong,ulong,ulong* -> ulong` | drivers/ | loop | Bajo |
| `find_random_bit` | `const ulong*,ulong,ulong -> ulong` | drivers/ | loop | Bajo |

**Nota**: `find_bit` accede a memoria de buffers — requiere anotaciones de ownership.

---

## 3. Conversión y formateo

Operan sobre buffers, sin más estado que los argumentos.

| Función | Firma | Consumidores | Riesgo |
|---|---|---|---|
| `hex2bin` | `char*,const char*,int -> int` | crypto/, drivers/ | Bajo |
| `bin2hex` | `char*,const void*,int -> char*` | drivers/ | Bajo |
| `hex_to_bin` | `char -> int` | lib/, drivers/ | Bajo |
| `_bcd2bin` | `unsigned char -> unsigned char` | drivers/rtc/ | Bajo |
| `_bin2bcd` | `unsigned char -> unsigned char` | drivers/rtc/ | Bajo |
| `kstrtobool` | `const char*,bool* -> int` | fs/, kernel/ | Bajo |
| `kstrtoint` | `const char*,unsigned int,int* -> int` | todo | Bajo |
| `kstrtou8`–`kstrtoll` | familia de conversión string→int | todo | Bajo |
| `match_int` | `substring*,int* -> int` | drivers/, fs/ | Bajo |
| `match_u64` | `substring*,u64* -> int` | drivers/ | Bajo |
| `match_hex` | `substring*,int* -> int` | drivers/ | Bajo |
| `match_octal` | `substring*,int* -> int` | drivers/ | Bajo |
| `match_uint` | `substring*,unsigned int* -> int` | drivers/ | Bajo |
| `match_token` | `char*,const table*,substring* -> int` | drivers/ | Bajo |

**Dependencias**: `_kstrtol` usa `simple_strtoul` (kernel C library). Migrar requiere exponer esa dependencia.

---

## 4. Búsqueda y ordenamiento

Sin estado global, aritméticas puras o con callback.

| Función | Firma | Consumidores | Riesgo |
|---|---|---|---|
| `bsearch` | `const void*,const void*,size_t,size_t,cmp* -> void*` | drivers/, kernel/ | Medio |
| `sort` | `void*,size_t,size_t,cmp*,swap* -> void` | drivers/, fs/ | Medio |
| `sort_r` | `void*,size_t,size_t,cmp*,swap*,const void* -> void` | fs/ | Medio |
| `list_sort` | `void*,list_head*,cmp* -> void` | fs/, mm/ | Alto |

**Traba**: `bsearch` y `sort` reciben punteros a función (callbacks). Requiere soporte de punteros a función en SpASM (Fase 6).

---

## 5. Utilidades de buffers y cadenas

| Función | Firma | Riesgo |
|---|---|---|
| `base64_encode` | `const u8*,int,char*,int -> int` | Bajo |
| `base64_decode` | `const char*,int,u8*,int -> int` | Bajo |
| `memcpy_and_pad` | `void*,size_t,const void*,size_t,int -> void` | Bajo |
| `memweight` | `const void*,int -> size_t` | Bajo |
| `skip_spaces` | `const char* -> char*` | Bajo |
| `strim` | `char* -> char*` | Bajo |
| `strreplace` | `char*,char,char -> void` | Bajo |
| `match_string` | `const char**,size_t,const char* -> int` | Bajo |
| `sysfs_streq` | `const char*,const char* -> bool` | Bajo |

---

## 6. Funciones de arquitectura (x86_64 ya en ensamblador)

**No migrar**: estas funciones son intrínsecas de la plataforma y su implementación en ensamblador es imprescindible.

| Función | Objeto | Razón |
|---|---|---|
| `memcpy`, `__memcpy` | `memcpy_64.o` | optimizado SSE/AVX |
| `memset`, `__memset` | `memset_64.o` | idem |
| `memmove`, `__memmove` | `memmove_64.o` | idem |
| `__sw_hweight*` | `hweight.o` | `popcnt` hardware |
| `crc32_pclmul` | `x86/crc32-pclmul.o` | `pclmulqdq` |
| `blake2s_core` | `x86/blake2s-core.o` | SIMD |

---

## 7. Estructuras y manejo de datos (riesgo medio‑alto)

| Función | Riesgo | Traba |
|---|---|---|
| `bitmap_*` (familia) | Medio | acceden a `unsigned long*` como bitmap, requieren bucles sobre memoria |
| `hex_dump_to_buffer` | Medio | acceso a buffer linea a linea |
| `string_escape_mem` | Medio | tabla de escapes interna |
| `kstrdup*` | Alto | `kmalloc` + copia, requiere gestión de memoria SpASM |
| `kasprintf` | Alto | `kmalloc` + `vsnprintf` |

---

## 8. Concurrencia y sincronización

| Función | Riesgo | Nota |
|---|---|---|
| `refcount_*` | Alto | atomics, barreras |
| `rcuref_*` | Alto | idem |
| `llist_*` | Alto | lockless, barreras |
| `lwq_*` | Alto | lockless wait queue |

**No prioritarias aún**: requieren soporte de atomics y barreras (Fase 6).

---

## 9. Hardware y boot

| Categoría | Ejemplos | Riesgo |
|---|---|---|
| MSR access | `msr-smp.o`, `msr.o` | Alto |
| IO | `iomem.o` | Alto |
| Boot | `arch/x86/boot/` | Crítico |

**No migrar en esta fase** — contexto de ejecución restringido, dependen de estado de plataforma.

---

## 10. Criptografía

| Función | Riesgo |
|---|---|
| `aes_*`, `sha1_*`, `md5_*` | Alto — críticas para seguridad, deben validarse contra vectores de prueba oficiales |

---

## 11. Código excluido de spasm-kernel

Funciones de subsistemas no incluidos en la configuración spasm-kernel:

- `CONFIG_*` no habilitadas
- sistemas de archivos no usados
- controladores no incluidos

Se identificarán en Fase 9.

---

## Resumen de prioridad

| Prioridad | Categoría | Cantidad | Bloqueante |
|---|---|---|---|
| **1** | Matemáticas puras | 8 | ✗ |
| **2** | Manipulación de bits (sin memoria) | 2 | ✗ |
| **3** | Conversión simple | 12 | ✗ |
| **4** | Busqueda de bits en buffers | 8 | ownership |
| **5** | Buffers y cadenas | 9 | ✗ |
| **6** | Búsqueda y orden | 4 | function pointers |
| **7** | Estructuras (bitmap) | 20 | memory |
| **8** | Concurrencia | 10 | atomics |
| **9** | Criptografía | 8 | test vectors |

---

## Próximos candidatos inmediatos (Fase 5)

1. **`int_sqrt`** — función pura, 1 argumento, 1 retorno, sin estado.
2. **`hex_to_bin`** — conversión carácter → entero, sin estado.
3. **`int_pow`** — potencia entera, sin estado.
4. **`_bcd2bin` / `_bin2bcd`** — conversión BCD, sin estado.
5. **`__sw_hweight32`** — peso Hamming software, sin estado.

Proceso repetible por función:

```text
inventario → implementación SpASM → comparación C/SpASM → pruebas → Kconfig → arranque → reemplazo
```
