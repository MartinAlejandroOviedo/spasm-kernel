# spasm-kernel

![spasm-kernel](img/spasm-kernel.png)

Kernel x86_64 basado en Linux 6.19.14 que reemplaza funciones con
implementaciones en SpASM sin cambiar los contratos que consumen Kbuild,
el resto del kernel, sus módulos ni el espacio de usuario.

**Repo:** https://github.com/MartinAlejandroOviedo/spasm-kernel
**Release:** https://github.com/MartinAlejandroOviedo/spasm-kernel/releases
**Changelog:** [CHANGELOG.md](CHANGELOG.md)

---

## Instalar desde release (recomendado)

```sh
wget https://github.com/MartinAlejandroOviedo/spasm-kernel/releases/download/v0.1.0/spasm-kernel-image-6.19.14-spasm-kernel_0.1.0-1_amd64.deb
wget https://github.com/MartinAlejandroOviedo/spasm-kernel/releases/download/v0.1.0/spasm-kernel-headers-6.19.14-spasm-kernel_0.1.0-1_amd64.deb
sudo dpkg -i spasm-kernel-image-6.19.14-spasm-kernel_0.1.0-1_amd64.deb spasm-kernel-headers-6.19.14-spasm-kernel_0.1.0-1_amd64.deb
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
git apply overlay/patches/spasm-kernel-debian-packages.patch

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
├── patches/                  # Integración adicional con el árbol Linux
└── spasm-kernel.md           # Documentación principal
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

## Paquetes Debian

La identidad pública de los paquetes también es `spasm-kernel`:

- `spasm-kernel-image-<versión>_<revisión>_amd64.deb`
- `spasm-kernel-headers-<versión>_<revisión>_amd64.deb`
- `spasm-kernel-libc-dev_<revisión>_amd64.deb`
- `spasm-kernel-image-<versión>-dbg_<revisión>_amd64.deb`, cuando corresponde

Los nombres compatibles con Linux que aparecen dentro del sistema de módulos
se conservan únicamente donde forman parte de la ABI o de la integración
esperada por Debian.

---

**Dependencia:** compilador propio SpASM (`tools/spasmc.py` en el proyecto SpASM).
