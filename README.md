# spasm-kernel

`spasm-kernel` es un kernel x86_64 basado en Linux 6.19.14 que integra
funciones compiladas desde SpASM sin cambiar los contratos que consumen el
resto del kernel, sus módulos ni el espacio de usuario.

El proyecto sigue la filosofía **Machine and User Care**: preservar la
estabilidad de la máquina, hacer visibles las decisiones técnicas y migrar
funciones en unidades pequeñas, reversibles y verificables.

## Estado

- Arranque completo en QEMU con initramfs.
- ABI Linux–SpASM x86_64 v2 conforme.
- Integración SpASM → ensamblador x86_64 → ELF → `vmlinux` → `bzImage`.
- Módulos SpASM cargables y descargables en Ring 0.
- Modos Kconfig C, SpASM y dual.
- Implementaciones SpASM activas para `gcd`, `int_sqrt`, `_bcd2bin` y
  `hex_to_bin`.

## Requisitos

- Sistema host x86_64.
- Toolchain habitual del kernel Linux.
- Compilador SpASM:
  `/home/martin/Documentos/SpASM/tools/spasmc.py`.
- QEMU en `/usr/bin/qemu-system-x86_64` para las pruebas de arranque.

## Verificación

```sh
git clone https://github.com/MartinAlejandroOviedo/spasm-kernel.git
cd spasm-kernel

PATH="$PWD/tools/spasm-kernel/host-tools:$PATH" \
KERNEL_BUILD=../build-spasm-kernel \
tools/testing/selftests/spasm-kernel/verify-all
```

## Paquetes Debian

Los paquetes propios utilizan la identidad del proyecto:

- `spasm-kernel-image-<versión>_<revisión>_amd64.deb`
- `spasm-kernel-headers-<versión>_<revisión>_amd64.deb`
- `spasm-kernel-libc-dev_<revisión>_amd64.deb`
- `spasm-kernel-image-<versión>-dbg_<revisión>_amd64.deb`, cuando corresponde

```sh
sudo dpkg -i spasm-kernel-image-*.deb spasm-kernel-headers-*.deb
sudo update-grub
```

## Documentación

- [Descripción y comandos del proyecto](spasm-kernel.md)
- [Contrato ABI Linux–SpASM v2](docs/spasm-kernel/spasm-linux-abi-v2.md)
- [Catálogo de migración](docs/spasm-kernel/migrations/catalog.md)
- [Release v0.1.0](docs/spasm-kernel/RELEASE-v0.1.0.md)
- [Historial de cambios](CHANGELOG.md)

## Licencia y base

El árbol conserva la licencia y los avisos del kernel Linux del que deriva.
Las incorporaciones de `spasm-kernel` usan identificadores SPDX compatibles
con los archivos en los que se integran.
