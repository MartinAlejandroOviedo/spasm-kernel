# SpASM Kernel — Frontera de Ensamblador Imprescindible

Funciones en `.S` que **no pueden migrarse a SpASM** porque dependen de instrucciones privilegiadas, transiciones de modo de CPU, o convenciones de hardware que no tienen equivalente en un lenguaje de alto nivel.

---

## Categoría 1: Entry/Exit de Hardware (~30 funciones)

**Archivos**: `entry_64.S`, `entry_64_compat.S`, `entry_32.S`, `entry_64_fred.S`

| Función | Razón |
|---|---|
| `entry_SYSCALL_64` | Instrucción `SYSCALL` del hardware, `swapgs`, `sysretq` |
| `entry_SYSENTER_compat` | Hardware SYSENTER con MSRs implícitos |
| `int80_emulation` | Emulación INT $0x80 con `CLEAR_BRANCH_HISTORY` |
| `asm_exc_nmi` | Lógica de nesting de NMI, comparación manual de stacks |
| `asm_exc_double_fault` | Task gate, no interrupt gate normal |
| `paranoid_entry` | `SAVE_AND_SWITCH_TO_KERNEL_CR3`, MSRs de CPU |
| `error_entry` | Corrección de RIP truncado en K8, faults IRET |
| `common_interrupt_return` | `swapgs` + `IRET` + PTI/ESPFIX/Xen |
| `__switch_to_asm` | Context switch: layout exacto de `inactive_task_frame` |
| `ret_from_fork_asm` | Entry point post-fork sin stack frame normal |
| Todas las de `thunk.S` | Salvado de registros para inline assembly |
| `x86_verw_sel` | Operando VERW en `.entry.text` mapeada con KPTI |
| `__vsyscall_page` | Página de 4K con offsets fijos (ABI vsyscall) |

---

## Categoría 2: Boot y Modos de CPU Tempranos (~25 funciones)

**Archivos**: `header.S`, `pmjump.S`, `copy.S`, `bioscall.S`, `head_64.S`, `compressed/*`

| Función | Razón |
|---|---|
| `protected_mode_jump` | Transición real→protegido: `mov CR0`, `ljmpl` |
| `intcall` | Self-modifying code, llamadas BIOS en real mode |
| `startup_32` / `startup_64` | Configuración de GDT/IDT, CR3, PAE, long mode |
| `trampoline_32bit_src` | Thunk 64→32→64 bit para toggle LA57 |
| `efi_enter32` | Deshabilita paging y long mode para EFI 32-bit |
| `relocate_kernel` (kexec) | Apaga paging, copia páginas en modo identidad |
| `sev_verify_cbit` | Cambia CR3 con stack efímero, `RDRAND`, `hlt` |
| Handlers IDT tempranos | `early_idt_handler_array`, pre-configuración |

---

## Categoría 3: Mitigaciones de Seguridad (~40 funciones)

**Archivos**: `retpoline.S`, `bhi.S`, `entry.S`

| Función | Razón |
|---|---|
| `__x86_indirect_thunk_*` | Retpoline: alternative rewriting con posiciones fijas |
| `__x86_return_thunk` | Return thunk universal |
| `srso_untrain_ret` | Manipula Return Stack Buffer con `CALL`+`INT3` |
| `retbleed_untrain_ret` | Mitigación Retbleed |
| `clear_bhb_loop` | Secuencia precisa para limpiar BHB |
| `write_ibpb` | Escritura MSR `IA32_PRED_CMD` |
| `__bhi_args` | Gadgets BHI para FineIBT con alineación de 32 bytes |

---

## Categoría 4: Acceso a Userspace con Excepciones (~20 funciones)

**Archivos**: `getuser.S`, `putuser.S`, `copy_user_64.S`, `copy_mc_64.S`, `csum-copy_64.S`

| Función | Razón |
|---|---|
| `__get_user_*` / `__put_user_*` | `STAC`/`CLAC` + `_ASM_EXTABLE_UA`, ABI no estándar |
| `copy_mc_fragile` | Machine Check safe copy con exception table por load/store |
| `csum_partial_copy_generic` | Checksum + copy con manejo de excepciones combinado |

---

## Categoría 5: Operaciones de Página y Memcpy Optimizado (~15 funciones)

**Archivos**: `memcpy_64.S`, `memset_64.S`, `memmove_64.S`, `clear_page_64.S`, `copy_page_64.S`

| Función | Razón |
|---|---|
| `__memcpy` / `__memset` / `__memmove` | FSRM/FSRS alternative rewriting |
| `clear_page` / `copy_page` | Selección dinámica por alternative() en boot |
| `__sw_hweight32` / `__sw_hweight64` | Software fallback de POPCNT |

---

## Categoría 6: Atomicidad y Sincronización (~15 funciones)

**Archivos**: `cmpxchg8b_emu.S`, `cmpxchg16b_emu.S`, `atomic64_*.S`, `msr-reg.S`

| Función | Razón |
|---|---|
| `cmpxchg8b_emu` / `cmpxchg16b_emu` | Emulación de CMPXCHG con `cli`/`popfl` |
| `atomic64_*_cx8` / `atomic64_*_386` | `LOCK CMPXCHG8B`, barreras `cli` para 386 |
| `rdmsr_safe_regs` / `wrmsr_safe_regs` | MSR access con `_ASM_EXTABLE` |

---

## Categoría 7: Kernel Self-Test y Debug (~10 funciones)

**Archivos**: `ibt_selftest.S`, `ftrace_64.S`

| Función | Razón |
|---|---|
| `ibt_selftest_noendbr` | Función deliberadamente sin `ENDBR` |
| `__fentry__` / `ftrace_caller` | Posiciones fijas requeridas por `-mfentry` |

---

## Resumen

| Categoría | Funciones | Migrable |
|---|---|---|
| Entry/Exit HW | ~30 | No |
| Boot/Modos CPU | ~25 | No |
| Mitigaciones | ~40 | No |
| Userspace + exc | ~20 | No |
| Mem ops opt | ~15 | No |
| Atomicidad | ~15 | No |
| Debug | ~10 | No |
| **Total** | **~155** | **0** |

**Conclusión**: ~155 funciones en ensamblador son imprescindibles y no migrables. Representan la frontera inferior del kernel. Todo el resto (~70k funciones en C) es potencialmente migrable a SpASM.

---

## Progreso de migración (Fase 10)

| Funciones C totales | ~70,000 |
|---|---|
| Migradas a SpASM | 4 (gcd, int_sqrt, _bcd2bin, hex_to_bin) |
| Documentadas en catálogo | 60+ |
| Frontera asm documentada | ~155 funciones |
