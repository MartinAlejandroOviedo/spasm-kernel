#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# SpASM Kernel — Install script
set -eu

ARCH=$(uname -m)
if [ "$ARCH" != "x86_64" ]; then
    echo "SpASM Kernel solo soporta x86_64. Arquitectura detectada: $ARCH"
    exit 1
fi

RELEASE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
KVER="6.19.14-spasm"

echo "=== SpASM Kernel v0.1.0 — Instalación ==="

if [ "$(id -u)" -ne 0 ]; then
    echo "Ejecutar como root: sudo $0"
    exit 1
fi

if [ -f "$RELEASE_DIR/linux-image-"*".deb" ]; then
    echo "Instalando paquetes .deb..."
    dpkg -i "$RELEASE_DIR"/linux-image-*.deb "$RELEASE_DIR"/linux-headers-*.deb
else
    echo "Instalando bzImage directo..."
    cp "$RELEASE_DIR/bzImage-spasm-kernel" "/boot/vmlinuz-$KVER"
    cp "$RELEASE_DIR/config-spasm-kernel" "/boot/config-$KVER"
fi

echo "Actualizando GRUB..."
update-grub || grub-mkconfig -o /boot/grub/grub.cfg

echo ""
echo "=== Instalación completa ==="
echo "Reinicia y selecciona 'SpASM Kernel' en el menú de GRUB."
echo ""
echo "Para verificar después de reiniciar:"
echo "  uname -r"
echo "  cat /sys/kernel/spasm/mode"
echo "  dmesg | grep spasm"
