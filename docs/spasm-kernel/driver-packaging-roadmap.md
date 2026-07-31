# Hoja de ruta: núcleo estable y controladores modulares

## Objetivo

`spasm-kernel` debe poder mantener un núcleo estable y actualizar o ampliar sus
controladores mediante paquetes Debian independientes. El sistema y las
aplicaciones continuarán utilizando las interfaces habituales del kernel: que
una función interna esté implementada en C, ensamblador o SpASM no debe cambiar
su contrato público.

Este diseño permite comenzar con computadoras x86_64 y crecer, de forma
controlada, hacia equipos industriales, televisores, vehículos o dispositivos
médicos. La presencia de un controlador en el proyecto no implica por sí sola
que el producto final esté validado o certificado para esos ámbitos.

## Principios

1. **Un solo nombre público:** proyecto y paquetes usan el prefijo
   `spasm-kernel`.
2. **Núcleo pequeño y estable:** solo se integran los componentes necesarios
   para arrancar, verificar y cargar módulos.
3. **Controladores separados:** los controladores que puedan ser módulos se
   distribuyen fuera del paquete de la imagen.
4. **ABI explícita:** ningún paquete de módulos se instala sobre un núcleo cuya
   ABI no sea compatible.
5. **Recuperación disponible:** una actualización no debe eliminar el kernel
   anterior que funciona.
6. **Seguridad por perfil:** firma, arranque verificado y políticas estrictas se
   incorporan antes de abordar usos industriales, vehiculares o médicos.

## Paquetes previstos

| Paquete | Contenido |
|---|---|
| `spasm-kernel-image-<kernel>` | Imagen del núcleo y componentes inseparables |
| `spasm-kernel-modules-core-<abi>` | Almacenamiento, sistema de archivos y módulos imprescindibles para arrancar |
| `spasm-kernel-drivers-desktop-<abi>` | Gráficos, red, audio y periféricos comunes |
| `spasm-kernel-drivers-extra-<abi>` | Hardware menos común y módulos opcionales |
| `spasm-kernel-headers-<kernel>` | Cabeceras y archivos necesarios para construir módulos |
| `spasm-kernel-sdk-<abi>` | Contratos, herramientas y ejemplos para controladores externos |

Cuando sea útil, un controlador podrá tener su propio paquete, por ejemplo:

```text
spasm-kernel-driver-amdgpu-<abi>
spasm-kernel-driver-r8169-<abi>
spasm-kernel-driver-<fabricante>-<modelo>-<abi>
```

Los grupos futuros podrán expresarse como metapaquetes que seleccionen módulos
ya validados:

```text
spasm-kernel-drivers-tv
spasm-kernel-drivers-automotive
spasm-kernel-drivers-industrial
spasm-kernel-drivers-medical
```

## Contrato ABI

La versión del proyecto y la versión de ABI son conceptos distintos. Una
revisión de controladores puede publicarse sin reemplazar el núcleo siempre que
mantenga la misma ABI.

Ejemplo inicial:

```text
Kernel release: 6.19.14-spasm-kernel-amd64
ABI provista:   spasm-kernel-abi-6.19.14-1
Drivers:        spasm-kernel-drivers-desktop-6.19.14-1
```

El paquete de imagen debe declarar:

```text
Provides: spasm-kernel-abi-6.19.14-1
```

Los paquetes de módulos deben declarar una dependencia exacta:

```text
Depends: spasm-kernel-abi-6.19.14-1
```

También deben instalar en el directorio de la versión correcta:

```text
/lib/modules/6.19.14-spasm-kernel-amd64/
```

Después de instalar o retirar módulos se ejecutarán `depmod` y la actualización
del initramfs correspondiente. Se verificará `vermagic`, las versiones de
símbolos cuando `CONFIG_MODVERSIONS` esté activo y, cuando corresponda, la firma
del módulo.

Cambiar estructuras internas, símbolos exportados, opciones ABI de compilación
o interfaces consumidas por los módulos obliga a incrementar la revisión ABI y
recompilar sus paquetes.

## Qué permanece integrado

La separación no debe impedir encontrar el sistema raíz. Permanecen integrados
en la imagen, o garantizados dentro del initramfs:

- cargador de módulos y formato ELF;
- consola mínima y diagnóstico de arranque;
- soporte EFI/ACPI necesario para la plataforma;
- seguridad y verificación requeridas por el perfil;
- controlador del almacenamiento raíz;
- sistema de archivos raíz;
- dependencias necesarias para cargar los dos anteriores.

La decisión exacta entre integrado (`=y`) y módulo (`=m`) se valida mediante una
prueba de arranque sin depender accidentalmente del sistema ya instalado.

## Flujo de publicación de un controlador

1. Identificar hardware, buses, firmware y dependencias.
2. Determinar si el controlador ya existe en Linux o requiere desarrollo.
3. Revisar licencia, procedencia y compatibilidad con la ABI vigente.
4. Compilarlo fuera de la imagen principal contra
   `spasm-kernel-headers-<kernel>`.
5. Ejecutar análisis estático, pruebas unitarias y pruebas ABI.
6. Probar carga, uso, suspensión, descarga y recuperación ante errores.
7. Construir un paquete Debian reproducible.
8. Probar instalación, actualización y desinstalación sin cambiar el núcleo.
9. Firmar y publicar el paquete junto con su matriz de hardware comprobado.

## Fases

### Fase A — Escritorio de referencia

- Congelar `spasm-kernel-abi-6.19.14-1`.
- Producir `image`, `modules-core`, `drivers-desktop` y `headers`.
- Validar AMDGPU, NVMe, EXT4, Realtek, audio, USB y EFI.
- Arrancar en QEMU y en la computadora de referencia.
- Confirmar que una revisión de `drivers-desktop` no reinstala la imagen.

**Criterio de salida:** arranque reproducible, escritorio funcional, red,
audio y recuperación con el kernel Debian anterior.

### Fase B — Distribución genérica amd64

- Ampliar la matriz a Intel y AMD, SATA/NVMe y adaptadores de red habituales.
- Automatizar pruebas de instalación y actualización.
- Publicar repositorio APT firmado y documentación de instalación.
- Mantener perfiles optimizados como opcionales, no como paquete genérico.

**Criterio de salida:** instalación repetible en varias máquinas y actualizaciones
de módulos con rechazo seguro cuando la ABI no coincide.

### Fase C — SDK de terceros

- Documentar el contrato C/SpASM y los símbolos permitidos.
- Proporcionar plantillas Kbuild y Debian.
- Añadir ejemplos mínimos de controlador en C y SpASM.
- Incorporar pruebas automáticas de ABI, `objtool`, carga y firma.

**Criterio de salida:** un tercero puede construir y empaquetar un módulo sin
modificar el árbol del núcleo.

### Fase D — Perfiles especializados

- Crear perfiles separados para TV, industria y automoción.
- Definir soporte a largo plazo, actualización atómica y recuperación.
- Incorporar secure boot, módulos firmados y trazabilidad.
- Trabajar con fabricantes para conocer protocolos y hardware reales.

**Criterio de salida:** cada perfil tiene hardware comprobado, responsable de
mantenimiento, política de seguridad y ciclo de actualización documentado.

### Fase E — Ámbitos regulados

Los dispositivos médicos o componentes críticos de vehículos requieren además
gestión de riesgos, evidencia de verificación, trazabilidad y validación del
producto completo bajo las normas aplicables. `spasm-kernel` aportará una base
técnica, pero no se declarará apto para uso clínico o de seguridad crítica solo
por compilar o cargar sus controladores.

## Próximo entregable

El siguiente hito es `spasm-kernel` 0.2.0 para escritorio x86_64:

```text
spasm-kernel-image-6.19.14-spasm-kernel-amd64_0.2.0-1_amd64.deb
spasm-kernel-modules-core-6.19.14-1_0.2.0-1_amd64.deb
spasm-kernel-drivers-desktop-6.19.14-1_0.2.0-1_amd64.deb
spasm-kernel-headers-6.19.14-spasm-kernel-amd64_0.2.0-1_amd64.deb
```

Antes de publicar se debe conservar un kernel de recuperación, verificar los
cuatro paquetes y probar el arranque. La instalación nunca debe reiniciar el
equipo automáticamente.

## Prototipo disponible

El primer componente del futuro administrador ya está definido en
`tools/spasm-driver-manager/`. `spasm-driver-detect` inspecciona dispositivos
PCI, USB, ACPI y de plataforma sin modificar el sistema. Su salida de texto
sirve para diagnóstico y su salida JSON será el contrato con la futura interfaz
gráfica.

La primera etapa recomienda grupos `core`, `desktop` y `extra`; los dispositivos
sin una regla conocida quedan como `unclassified` y no provocan instalaciones
automáticas. La instalación automática quedará deshabilitada hasta disponer de
paquetes firmados, comprobación estricta de ABI, reconstrucción segura del
initramfs y recuperación verificada.
