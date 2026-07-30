# spasm-driver-manager

Primer prototipo del administrador de controladores de `spasm-kernel`. Detecta
dispositivos PCI, USB, ACPI y de plataforma a partir de `sysfs`; consulta los
alias del sistema de módulos y recomienda grupos de paquetes ligados a la ABI.

La herramienta es deliberadamente de solo lectura. No instala paquetes, no
carga módulos y no modifica el initramfs.

## Uso

```sh
tools/spasm-driver-manager/spasm-driver-detect
tools/spasm-driver-manager/spasm-driver-detect --json
```

Para comprobar los alias de una versión instalada de `spasm-kernel`:

```sh
tools/spasm-driver-manager/spasm-driver-detect \
  --kernel-release 6.19.14-spasm-kernel-desktop-amd64
```

La salida JSON será el contrato inicial entre el detector, el futuro servicio
de instalación y la interfaz gráfica.

## Construcción inicial de paquetes

`build-debian-packages.py` toma un build ya validado y un staging generado con
`make modules_install`. Resuelve las dependencias de cada módulo mediante
`modprobe` y produce los paquetes `image`, `modules-core` y
`drivers-desktop` y `machine-care`. Esta es la primera implementación del
modelo separado; no instala los paquetes resultantes.

Los módulos se distribuyen como ELF `.ko` sin compresión. Primero se elimina su
información de depuración y después se agrega la firma PKCS#7 con la clave del
build del kernel. Este orden es obligatorio: modificar un módulo después de
firmarlo invalida la firma. Esto
evita depender de que el `kmod` reducido del initramfs pueda descomprimir XZ
antes de encontrar el dispositivo raíz. La compresión podrá reactivarse cuando
el perfil habilite y pruebe explícitamente la descompresión en kernel o en
espacio de usuario temprano.

`spasm-kernel-machine-care` instala la política SpASM, el agente observacional
y su servicio systemd. No modifica scheduler, frecuencias ni cgroups.

## Política inicial

- `core` siempre se recomienda porque contiene los módulos de arranque.
- `desktop` agrupa gráficos, red, audio y periféricos habituales.
- `extra` contiene dispositivos opcionales identificados mediante una regla.
- `unclassified` informa hardware todavía desconocido, pero no instala
  automáticamente `drivers-extra`.
- La base `hardware-db.json` debe versionarse junto con la ABI.

La resolución definitiva se realizará contra el índice firmado del repositorio
APT. La base local permite diagnosticar equipos sin conexión y elegir el paquete
offline apropiado.
