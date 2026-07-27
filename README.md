# SpASM Kernel

Overlay para reemplazar funciones del kernel Linux 6.19.14 x86_64
con implementaciones en SpASM.

**Repo:** https://github.com/MartinAlejandroOviedo/spasm-kernel

---

## Aplicar sobre Linux 6.19.14 limpio

```sh
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.19.14.tar.xz
tar xf linux-6.19.14.tar.xz
cd linux-6.19.14

# 1. Clonar el overlay
git clone https://github.com/MartinAlejandroOviedo/spasm-kernel.git overlay

# 2. Aplicar parche a archivos existentes del kernel
git apply overlay/spasm-kernel.patch

# 3. Copiar archivos nuevos del overlay
cp -r overlay/* .
```

---

## Estructura

```
spasm-kernel/
├── spasm-kernel.patch        # Parche para Kconfig, Makefile, gcd.c, etc.
├── lib/                      # Funciones migradas (.spasm + wrappers)
│   ├── math/
│   │   ├── gcd_spasm.spasm
│   │   ├── int_sqrt_spasm.spasm
│   │   └── *.h, *_dual.c, *_export.c, *_entry.S
│   ├── bcd2bin_spasm.spasm, *.h, *_dual.c
│   └── hex_to_bin_spasm.spasm, *_export.c, *_entry.S
├── tools/
│   ├── spasm-kernel/         # Backend compilador SpASM → x86_64
│   ├── spasm-initramfs/      # Initramfs para QEMU
│   └── testing/selftests/spasm-kernel/  # Tests
├── docs/spasm-kernel/        # Documentación
├── samples/spasm/            # Módulo ejemplo
└── SPASM-KERNEL.md           # Documentación principal
```

---

## Funciones migradas

| Función | Pruebas |
|---|---|
| `gcd` | Equivalencia Ring 0 |
| `int_sqrt` | 100k secuenciales + 100k aleatorios |
| `_bcd2bin` | 256 valores |
| `hex_to_bin` | 256 valores |

---

## Verificación

```sh
export SPASMC=/ruta/spasmc.py
KERNEL_BUILD=/ruta/build \
  tools/testing/selftests/spasm-kernel/verify-all
```

---

**Dependencia:** [spasmc](https://github.com/quamagi/spasm) — compilador SpASM.
