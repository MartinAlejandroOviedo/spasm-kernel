# Changelog

## v0.3.0-alpha1 (2026-07-29)

### Cambiado

- Unificada la identidad pública bajo el nombre exacto `spasm-kernel`.
- Renombrados los paquetes Debian a `spasm-kernel-image`,
  `spasm-kernel-headers` y `spasm-kernel-libc-dev`.
- Actualizados README, documentación, instaladores, mensajes y rutas de build.
- Agregada la integración Debian que conserva la compatibilidad técnica con
  el ecosistema Linux sin exponer nombres genéricos en los paquetes.
- Documentada la hoja de ruta para separar imagen, módulos esenciales y
  controladores en paquetes Debian ligados a una ABI explícita.
- Definidas las fases de escritorio, distribución amd64, SDK de terceros y
  perfiles especializados, junto con sus criterios de salida.
- Agregado `spasm-driver-detect`, prototipo de solo lectura que clasifica el
  hardware y recomienda paquetes `core`, `desktop` o `extra`.
- Definido un primer contrato JSON para la futura interfaz gráfica del
  administrador de controladores.
- Corregido el empaquetado temprano de módulos: `core` y `desktop` distribuyen
  `.ko` sin compresión para que el `kmod` del initramfs pueda cargar NVMe antes
  de montar la raíz.
- Agregado el motor determinista `spasm_care_level_v1`, escrito en SpASM, como
  núcleo común de decisión Machine Care para el futuro agente global.
- Incorporados nueve vectores nativos que cubren los niveles GREEN, YELLOW,
  ORANGE, RED y EMERGENCY, y su ejecución en `verify-all`.
- Agregado el primer agente Machine Care global en modo observacional, con
  política nativa SpASM, instantánea JSON atómica y aislamiento systemd.
- Migradas y verificadas `_bin2bcd`, `int_pow`, `lcm` y `lcm_not_zero`, con
  selección C/SpASM/dual y 200.100 comparaciones nativas sin discrepancias.
- Corregida la integración Kbuild de `lcm` para impedir símbolos duplicados y
  normalizada la extensión ABI de 32 a 64 bits en `int_pow`.
- Corregida la firma de módulos Debian: ahora `strip` se ejecuta antes de
  `sign-file`, evitando firmas PKCS#7 inválidas y errores `EINVAL`.
- Agregado el paquete independiente `spasm-kernel-machine-care`.
- Ampliada `verify-all` para comprobar las ocho funciones públicas migradas,
  la equivalencia ampliada y los dos componentes Machine Care.

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
