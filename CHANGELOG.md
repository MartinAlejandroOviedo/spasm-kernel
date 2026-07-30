# Changelog

Todos los cambios relevantes de `spasm-kernel` se documentan en este archivo.

## Sin publicar

### Cambiado

- Unificada la identidad del proyecto, documentación, herramientas, mensajes
  de ejecución y directorios de build bajo el nombre `spasm-kernel`.
- Renombrados los paquetes Debian propios de `linux-image`,
  `linux-headers` y `linux-libc-dev` a `spasm-kernel-image`,
  `spasm-kernel-headers` y `spasm-kernel-libc-dev`.
- Actualizadas las rutas y órdenes de instalación para los nuevos paquetes.

## 0.1.0

### Agregado

- Pipeline SpASM → ensamblador x86_64 → ELF integrado con Kbuild.
- Contrato ABI Linux–SpASM x86_64 v2.
- Modos Kconfig C, SpASM y dual.
- Migraciones iniciales de `gcd`, `int_sqrt`, `_bcd2bin` y `hex_to_bin`.
- Módulo SpASM de validación en Ring 0.
- Initramfs configurable y prueba de arranque automatizada en QEMU.
- Verificaciones de Kbuild, ABI, símbolos, equivalencia y tamaño.
