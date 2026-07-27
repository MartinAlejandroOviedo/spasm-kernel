# SpASM Kernel 0.0.1 PoC

Este documento congela la primera prueba reproducible de ejecución de código
SpASM nativo en Ring 0.

## Identidad

- Proyecto: SpASM Kernel
- Filosofía: Machine and User Care
- Arquitectura: x86_64
- Base: Linux 6.19.14
- Commit base: `b020e7796023`
- Rama de desarrollo: `spasm/main`
- Compilador SpASM:
  `/home/martin/Documentos/SpASM/tools/spasmc.py`
- Backend kernel experimental:
  `tools/spasm-kernel/spasm-kmod-native.py`

El backend experimental aún se invoca directamente. Integrarlo como backend
formal del compilador SpASM es el siguiente hito del proyecto.

## Construcción

```sh
tools/spasm-kernel/project config
tools/spasm-kernel/project build
tools/spasm-kernel/project module
tools/spasm-kernel/verify-poc
```

Directorio de construcción utilizado:

```text
/home/martin/Disco3/kernelLinux/build-x86_64-baseline
```

## Herramientas de la prueba

```text
Python 3.13.5
gcc (Debian 14.2.0-19) 14.2.0
GNU ld (GNU Binutils for Debian) 2.44
GNU Make 4.4.1
QEMU 10.0.11
BusyBox 1.37.0
```

SHA-256 del dispatcher `spasmc.py` usado:

```text
90f6b1d395ee257c658563e5173066ecf596c635c4880d8bc57925c57a54dfde
```

## Evidencia congelada

Configuración `.config`:

```text
115e754f4590e21b45ebacd1cede2da1c5b2dce75351abb02dfcbbf072a8e194
```

Artefactos de la ejecución validada:

```text
bzImage
44130387bfc3890c04304daab1d10e500e560b8831b82685b002d3264f00929b

spasm-initramfs.cpio.gz
f75fad0cb7fb55f29280cce7c39bef7aa43917ded1036647d093c86a0a3fddd8

spasm_hello_native.S
f6bf1ee710a6330a980b997813b7f57e02e375c7ed6fe1203ec428353c87bf03

spasm_hello.ko
898540436dc3861784c951cc9249146a47519842292c34d1d67f5e8b249e948a
```

Los binarios no se incorporan al repositorio. Los hashes identifican la
ejecución congelada; una reconstrucción posterior puede variar en metadatos sin
alterar el comportamiento comprobado.

## Criterio de éxito

La prueba solamente se considera aprobada si QEMU muestra todas estas señales:

```text
[spasm-init] Nice_Kernel_Machine_and_User_Care
spasm: SpASM Kernel: SpASM nativo activo en Ring 0
spasm: Condicional SpASM nativo correcto
spasm: Bucle SpASM nativo correcto
spasm: Division y modulo SpASM correctos
[spasm-init] Modulo SpASM: CARGADO
[spasm-init] Modulo SpASM: DESCARGADO
[spasm-init] RESULTADO: OK
```
