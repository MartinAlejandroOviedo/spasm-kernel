# Changelog

## Sin publicar

### Cambiado

- Unificada la identidad pública bajo el nombre exacto `spasm-kernel`.
- Renombrados los paquetes Debian a `spasm-kernel-image`,
  `spasm-kernel-headers` y `spasm-kernel-libc-dev`.
- Actualizados README, documentación, instaladores, mensajes y rutas de build.
- Agregada la integración Debian que conserva la compatibilidad técnica con
  el ecosistema Linux sin exponer nombres genéricos en los paquetes.

## v0.1.0 (2026-07-27)

### Primera versión de spasm-kernel

- **4 funciones migradas a SpASM:**
  - `gcd` — algoritmo de máximo común divisor (Stein binario)
  - `int_sqrt` — raíz cuadrada entera (shift-and-subtract)
  - `_bcd2bin` — conversión BCD a binario
  - `hex_to_bin` — conversión hexadecimal a entero

- **Infraestructura Kbuild:**
  - Regla `%.spasm → %.spasm.S → %.o` integrada en Kbuild
  - Compilación reproducible (deterministic rebuild)
  - Verificación objtool + ORC unwinder

- **Sistema de configuración:**
  - `CONFIG_SPASM_KERNEL_MODE_SPASM` — switch global para todas las funciones
  - `CONFIG_SPASM_KERNEL_MODE_C` — revertir a implementaciones originales
  - `CONFIG_SPASM_KERNEL_MODE_DUAL` — comparación C/SpASM en runtime
  - Opciones individuales por función

- **Compilador SpASM nativo:**
  - Backend `spasm-kmod-native.py` (1800+ líneas)
  - Soporte para structs compatibles con C (alineación, padding, sizeof)
  - Tipos ABI: u8–u64, i8–i64, usize, isize, bool
  - Parámetros 8/16/32-bit con zero/sign-extension correcta
  - Funciones internas puras con hasta 6 argumentos
  - Bucles con presupuesto de iteraciones (anti-bucle infinito)
  - `kalloc`/`kfree` con verificación estática de uso

- **Verificación:**
  - `verify-all`: 6 pruebas automatizadas (kbuild, ABI, dual, QEMU, símbolos, tamaño)
  - 100k+ pruebas de equivalencia por función (0 discrepancias)

- **Reducción del kernel:**
  - vmlinux: 51 MB → 24.7 MB (-52%)
  - bzImage: 14 MB → 8.1 MB (-42%)
  - 242 opciones Kconfig eliminadas

- **Documentación:**
  - Catálogo de migración: 60+ funciones clasificadas
  - Frontera de ensamblador: ~155 funciones imprescindibles documentadas
  - Contrato ABI Linux–SpASM v2
  - Manual de integración Kbuild

- **Release:**
  - Paquetes `.deb` instalables
  - `bzImage` para arranque directo
  - Script `install.sh` automatizado
