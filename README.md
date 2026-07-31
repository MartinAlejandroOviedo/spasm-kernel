# spasm-kernel

![spasm-kernel](img/spasm-kernel.png)

Kernel x86_64 basado en Linux 6.19.14 que reemplaza funciones con
implementaciones en SpASM sin cambiar los contratos que consumen Kbuild,
el resto del kernel, sus módulos ni el espacio de usuario.

**Repo:** https://github.com/MartinAlejandroOviedo/spasm-kernel
**Release:** https://github.com/MartinAlejandroOviedo/spasm-kernel/releases
**Changelog:** [CHANGELOG.md](CHANGELOG.md)
**Hoja de ruta de controladores:** [núcleo estable y paquetes modulares](docs/spasm-kernel/driver-packaging-roadmap.md)

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
git apply overlay/spasm-kernel-phase0.patch
git apply overlay/patches/spasm-kernel-debian-packages.patch

# 3. Copiar archivos nuevos del overlay
cp -r overlay/* .

# 4. Build con release y compilador explícitos
export SPASMC=/ruta/al/compilador/SpASM/tools/spasmc.py
export KERNEL_RELEASE=6.19.14-spasm-kernel-desktop-amd64
make O=/ruta/build KERNELRELEASE="$KERNEL_RELEASE" -j"$(nproc)"
make O=/ruta/build KERNELRELEASE="$KERNEL_RELEASE" \
  INSTALL_MOD_PATH=/ruta/staging -j"$(nproc)" modules_install
```

---

## Estructura

```
spasm-kernel/
├── spasm-kernel.patch        # Parche para Kconfig, Makefile, gcd.c, etc.
├── spasm-kernel-phase0.patch # bin2bcd, int_pow y lcm validados
├── lib/                      # Funciones migradas (.spasm + wrappers)
│   ├── math/
│   │   ├── gcd_spasm.spasm
│   │   ├── int_sqrt_spasm.spasm
│   │   ├── int_pow_spasm.spasm
│   │   ├── lcm_spasm.spasm
│   │   └── *.h, *_dual.c, *_export.c, *_entry.S
│   ├── bcd2bin_spasm.spasm, bin2bcd_spasm.spasm, *.h, *_dual.c
│   └── hex_to_bin_spasm.spasm, *_export.c, *_entry.S
├── tools/
│   ├── spasm-kernel/         # Backend compilador SpASM → x86_64
│   ├── spasm-driver-manager/ # Detección y recomendación de drivers
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
| `_bin2bcd` | dominio decimal válido completo (0–99) |
| `hex_to_bin` | 256 valores |
| `int_pow` | 100k vectores |
| `lcm` / `lcm_not_zero` | 100k vectores |

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

- `spasm-kernel-image-<release>_<revisión>_amd64.deb`
- `spasm-kernel-modules-core-<abi>_<revisión>_amd64.deb`
- `spasm-kernel-drivers-desktop-<abi>_<revisión>_amd64.deb`
- `spasm-kernel-drivers-extra-<abi>_<revisión>_amd64.deb`
- `spasm-kernel-drivers-legacy-<abi>_<revisión>_amd64.deb` (opt-in)
- `spasm-kernel-machine-care_<revisión>_amd64.deb`

Los nombres compatibles con Linux que aparecen dentro del sistema de módulos
se conservan únicamente donde forman parte de la ABI o de la integración
esperada por Debian.

La evolución prevista separa la imagen, los módulos esenciales y los
controladores de escritorio. Esto permitirá publicar controladores compatibles
sin reemplazar el núcleo. La dependencia se controla mediante una versión de
ABI explícita; un módulo no se instalará si no coincide con el núcleo. El diseño
completo y sus fases están en la
[hoja de ruta de controladores](docs/spasm-kernel/driver-packaging-roadmap.md).

---

**Dependencia:** compilador propio SpASM (`tools/spasmc.py` en el proyecto SpASM).
