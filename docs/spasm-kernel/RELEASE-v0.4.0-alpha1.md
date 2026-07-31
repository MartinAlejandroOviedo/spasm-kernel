# spasm-kernel v0.4.0-alpha1

Esta alpha completa el Paso 1 de la arquitectura modular de controladores:
define un perfil estándar reproducible y separa los módulos instalables por
función, sin alterar la ABI Linux que ve el sistema.

## Resultado

- Kernel: `6.19.14-spasm-kernel-standard-amd64`
- Perfil estándar: 2.876 módulos configurados
- Reducción frente al perfil de referencia: 922 módulos (24,3 %)
- Validación integral: 10/10
- Arranque QEMU: OK
- Módulos empaquetados y firmados: 181/181
- Firmas inválidas: 0
- `vermagic` incorrectos: 0
- Ciclo aislado instalar/configurar/purgar: OK

## Paquetes

- `spasm-kernel-image-6.19.14-spasm-kernel-standard-amd64`
- `spasm-kernel-modules-core-6.19.14-1`
- `spasm-kernel-drivers-desktop-6.19.14-1`
- `spasm-kernel-drivers-extra-6.19.14-1`
- `spasm-kernel-machine-care`

La instalación estándar requiere `image`, `modules-core` y
`drivers-desktop`. El paquete `drivers-extra` es optativo y se instala bajo
demanda. Los controladores `legacy` quedan fuera de este perfil y requieren
una compilación explícita con `profiles/legacy-amd64.config`.

## Alcance

Esta versión no intenta ser un kernel mínimo para una sola computadora.
Conserva el hardware contemporáneo habitual de escritorio y elimina familias
históricas o especializadas del perfil estándar. La siguiente etapa ampliará
la resolución automática de hardware y la cobertura de equipos distintos.
