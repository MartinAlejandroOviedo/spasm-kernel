# Initramfs de desarrollo de SpASM Kernel

Este initramfs proporciona una consola mínima y una prueba automática para el
kernel x86_64 del proyecto SpASM Kernel, basado en la filosofía *Machine and
User Care*. Su comportamiento se configura desde la línea de comandos del
kernel, sin reconstruir el archivo. El prefijo técnico `spasm.*` se conserva
porque identifica la interfaz de la cadena de herramientas SpASM.

## Construcción

```sh
tools/spasm-initramfs/build.sh
```

El resultado predeterminado es `tools/spasm-initramfs/spasm-initramfs.cpio.gz`.
También se puede indicar otra ruta como primer argumento. La variable
`BUSYBOX=/ruta/busybox` permite seleccionar otra compilación de BusyBox.

## Parámetros

- `spasm.mode=shell`: abre una consola interactiva; es el modo predeterminado.
- `spasm.mode=test`: comprueba procfs, sysfs, devtmpfs y la arquitectura, imprime
  `RESULTADO: OK` y apaga la máquina.
- `spasm.mode=poweroff`: apaga inmediatamente después de inicializar.
- `spasm.mode=reboot`: reinicia inmediatamente después de inicializar.
- `spasm.message=texto`: mensaje de arranque sin espacios.
- `spasm.hostname=nombre`: nombre del sistema dentro del initramfs.
- `spasm.delay=N`: espera N segundos antes de ejecutar el modo.
- `spasm.debug=1`: muestra la línea de comandos y los sistemas montados.

## Ejemplo con QEMU

```sh
qemu-system-x86_64 \
  -m 512M -smp 2 \
  -kernel ../build-x86_64-baseline/arch/x86/boot/bzImage \
  -initrd tools/spasm-initramfs/spasm-initramfs.cpio.gz \
  -append "console=ttyS0 spasm.mode=test spasm.message=Prueba_base spasm.debug=1" \
  -nographic -no-reboot
```
