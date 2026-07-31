# Perfiles de controladores v1

## Objetivo

El kernel y los paquetes de `spasm-kernel` separan capacidad de arranque,
escritorio habitual, funciones opcionales contemporáneas y hardware histórico.
La clasificación es explícita y versionada; un módulo nunca cambia de grupo
por una heurística silenciosa.

## Grupos

| Grupo | Instalación | Contenido |
|---|---|---|
| `core` | obligatoria | raíz, almacenamiento, device mapper, xHCI y USB HID |
| `desktop` | estándar | GPU, Ethernet/Wi‑Fi, audio, cámara y entrada habitual |
| `extra` | bajo demanda | virtualización, filesystems y redes opcionales actuales |
| `legacy` | opt-in | buses, staging y hardware histórico |

Las semillas están en `profiles/module-groups-v1.json`. El empaquetador resuelve
recursivamente sus dependencias contra el `modules.dep` del mismo release.

## Perfil standard-amd64

`profiles/standard-amd64.config` se combina con la configuración validada de
escritorio. Conserva los controladores contemporáneos como módulos y desactiva
familias completas que no son necesarias para un equipo común:

- staging y Comedi;
- ATM, ARCnet, FDDI, PCMCIA y MTD;
- InfiniBand, SCSI HBA/target, CAN, 802.15.4 y WWAN;
- IIO industrial, USB gadget/IP y media analógica/radio/SDR/test.

La primera aplicación sobre la configuración final de la alpha reduce las
opciones `=m` de 3.798 a 2.876: 922 módulos menos (24,3 %) sin eliminar NVMe,
AHCI, ext4, USB HID, GPU, red ni audio.

## Reglas de seguridad

1. `core` debe instalarse antes de generar el initramfs.
2. Un paquete sólo acepta el release y ABI exactos.
3. `desktop`, `extra` y `legacy` no contienen duplicados de `core`.
4. Todos los `.ko` se modifican, después se firman; nunca al revés.
5. El detector recomienda paquetes, pero no instala automáticamente `legacy`.
6. Un driver retirado de `standard` debe permanecer recuperable mediante un
   perfil o paquete opt-in antes de eliminarse del catálogo.

## Construcción

```sh
tools/spasm-driver-manager/build-standard-config \
  /ruta/linux-6.19.14 \
  /ruta/config-base \
  /ruta/build-standard
```

El comando combina el fragmento, ejecuta `olddefconfig` y exige que
`profile-audit` termine sin violaciones.
