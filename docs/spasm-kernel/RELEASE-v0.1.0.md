# spasm-kernel — Release v0.1.0

**Filosofía:** Machine and User Care.
**Kernel base:** Linux 6.19.14
**Arquitectura:** x86_64
**Compilador:** SpASM (spasmc + backend nativo)

---

## Artefactos

| Archivo | Descripción |
|---|---|
| `bzImage-spasm-kernel` | Kernel comprimido listo para arrancar |
| `config-spasm-kernel` | Configuración Kconfig utilizada |
| `spasm-kernel-image-*.deb` | Imagen y módulos instalables |
| `spasm-kernel-headers-*.deb` | Headers para compilar módulos |
| `spasm-kernel-libc-dev_*.deb` | Headers para desarrollo en espacio de usuario |

---

## Instalación

```sh
# Opción 1: .deb
sudo dpkg -i spasm-kernel-image-*.deb spasm-kernel-headers-*.deb
sudo update-grub
sudo reboot

# Opción 2: bzImage directo
sudo cp bzImage-spasm-kernel /boot/vmlinuz-spasm-kernel
sudo update-grub
sudo reboot
```

---

## Funciones migradas a SpASM

| Función | Archivo fuente | Tests | Discrepancias |
|---|---|---|---|
| `gcd` | `lib/math/gcd_spasm.spasm` | Módulo Ring 0 | 0 |
| `int_sqrt` | `lib/math/int_sqrt_spasm.spasm` | 100k sec + 100k rand | 0 |
| `_bcd2bin` | `lib/bcd2bin_spasm.spasm` | 256 valores | 0 |
| `hex_to_bin` | `lib/hex_to_bin_spasm.spasm` | 256 valores | 0 |

---

## Configuración

```kconfig
# Activar todas las funciones SpASM (por defecto)
CONFIG_SPASM_KERNEL_MODE_SPASM=y

# O seleccionar por función:
CONFIG_SPASM_KERNEL_GCD_SPASM=y
CONFIG_SPASM_KERNEL_INT_SQRT_SPASM=y
CONFIG_SPASM_KERNEL_BCD_SPASM=y
CONFIG_SPASM_KERNEL_HEX_TO_BIN_SPASM=y

# Revertir a C:
CONFIG_SPASM_KERNEL_MODE_C=y
```

---

## Verificación

```sh
cd linux-6.19.14
KERNEL_BUILD=../build-spasm-kernel \
  tools/testing/selftests/spasm-kernel/verify-all
```

---

## Estructura del proyecto

```
linux-6.19.14/           # Kernel Linux 6.19.14 + spasm-kernel
├── lib/
│   ├── math/
│   │   ├── gcd_spasm.spasm       # gcd en SpASM
│   │   └── int_sqrt_spasm.spasm  # int_sqrt en SpASM
│   ├── bcd2bin_spasm.spasm       # _bcd2bin en SpASM
│   └── hex_to_bin_spasm.spasm    # hex_to_bin en SpASM
├── tools/spasm-kernel/           # Backend nativo SpASM
│   ├── spasm-kmod-native.py      # Compilador SpASM → x86_64
│   └── spasm-target-spasm-kernel-x86_64
├── docs/spasm-kernel/            # Documentación
│   ├── assembly-frontier.md      # Frontera de ensamblador (155 funciones)
│   ├── migrations/catalog.md     # Catálogo de migración (60+ funciones)
│   └── spasm-linux-abi-v2.md     # Contrato ABI Linux–SpASM
├── tools/testing/selftests/spasm-kernel/
│   └── verify-all                # Prueba integral automatizada
└── releases/                     # Artefactos de release
    ├── bzImage-spasm-kernel
    ├── config-spasm-kernel
    └── *.deb
```

---

## Repositorio

```sh
git clone <url-del-repo>
cd linux-6.19.14
git checkout spasm/main
```

**Dependencia externa:** Compilador SpASM en `~/Documentos/SpASM/tools/spasmc.py`

---

## Métricas

| Métrica | Valor |
|---|---|
| Kernel base | Linux 6.19.14 |
| Funciones migradas | 4 |
| Funciones catalogadas | 60+ |
| Frontera asm | ~155 funciones imprescindibles |
| bzImage | 8.1 MB |
| vmlinux | 24.7 MB |
| Reducción vs defconfig | -52% vmlinux, -42% bzImage |
| Tests automatizados | 6 (verify-all) |
| Modos Kconfig | C / SpASM / Dual |

---

## Machine and User Care

- **Cuidado de la máquina:** sin degradación de estabilidad, memoria o diagnóstico.
- **Cuidado de la persona:** errores explícitos, configuración visible, comportamiento seguro por defecto.
- **Compatibilidad:** Linux consume los artefactos normalmente aunque la implementación sea SpASM.
- **Migración verificable:** reemplazo por módulos pequeños, reversibles y probados en x86_64.
