# SpASM Kernel

![SpASM Kernel](img/spasm-kernel.png)

Overlay para reemplazar funciones del kernel Linux 6.19.14 x86_64
con implementaciones en SpASM.

**Repo:** https://github.com/MartinAlejandroOviedo/spasm-kernel
**Release:** https://github.com/MartinAlejandroOviedo/spasm-kernel/releases
**Changelog:** [CHANGELOG.md](CHANGELOG.md)

---

## Instalar desde release (recomendado)

```sh
wget https://github.com/MartinAlejandroOviedo/spasm-kernel/releases/download/v0.1.0/linux-image-6.19.14-g83ce7f9bfbed-dirty_6.19.14-g83ce7f9bfbed-25_amd64.deb
wget https://github.com/MartinAlejandroOviedo/spasm-kernel/releases/download/v0.1.0/linux-headers-6.19.14-g83ce7f9bfbed-dirty_6.19.14-g83ce7f9bfbed-25_amd64.deb
sudo dpkg -i linux-image-*.deb linux-headers-*.deb
sudo reboot
```

O con bzImage directo (sin .deb):

```sh
wget https://github.com/MartinAlejandroOviedo/spasm-kernel/releases/download/v0.1.0/bzImage-spasm-kernel
sudo cp bzImage-spasm-kernel /boot/vmlinuz-spasm-kernel
sudo update-grub
sudo reboot
```

---

## Compilar desde fuente (overlay sobre Linux 6.19.14)

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
