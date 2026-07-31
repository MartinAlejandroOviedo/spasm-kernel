# SpASM Kernel v0.7.0 — Optimización de subsistemas

## Objetivo

Reducir el código innecesario del kernel Linux base eliminando subsistemas
que no aplican a hardware x86_64 moderno.

## Assembly eliminado (≈15,800 líneas de 43,501 → 36% del total)

| Subsistema | Líneas ASM | Motivo |
|---|---|---|
| `math-emu/` (FPU emulation) | 3,569 | x86_64 siempre tiene FPU/SSE |
| `serpent*.S` (Serpent) | 2,791 | Cifrador obsoleto (perdió AES 2001) |
| `twofish*.S` (Twofish) | 1,310 | Otro finalista AES sin uso real |
| `camellia*.S` (Camellia) | 2,540 | Solo usado en Japón |
| `aria*.S` (ARIA) | 3,756 | Solo usado en Corea |
| `sm3*.S / sm4*.S` (SM3/SM4) | 1,494 | Solo obligatorio en China |
| `um/*.S` (UML) | 114 | User Mode Linux |
| `efi-mixed.S` | ~200 | Boot 32-bit EFI (Macs 2006-2008) |

## Subsistemas C eliminados (31 opciones de config)

| Categoría | Qué se eliminó |
|---|---|
| Crypto | Serpent, Twofish, Camellia, ARIA (aesni/avx/avx2) |
| Legacy buses | ISDN, Firewire, PCMCIA, ATM, ARCNET, FDDI |
| Industrial | COMEDI, MTD, W1, IIO, CAN, IEEE 802.15.4, 6LoWPAN |
| Staging | STAGING (drivers experimentales) |
| Media | Analog TV, Digital TV, Radio, SDR |
| Mac | MACINTOSH_DRIVERS |
| Virtualización especializada | VDPA, USB_GADGET, USBIP_CORE |
| Networking niche | HAMRADIO, NFC, WWAN, NET_DSA, GREYBUS, MOST |

## Comparación de tamaños

| Métrica | v0.6.0 (antes) | v0.7.0 (optimizado) |
|---|---|---|
| Opciones =y | 2,635 | 2,579 (-56) |
| Opciones =m | 3,798 | 3,185 (-613) |
| bzImage | ? | ? |
| Módulos totales | ? | ? |

## Riesgo

**Bajo.** Solo se eliminaron subsistemas que requieren hardware específico
que no está presente en una máquina x86_64 moderna estándar. Los drivers
esenciales (NVMe, SATA, ext4, AMD GPU, Intel GPU, red, USB, audio) siguen intactos.

## Cómo probar

```sh
# Verificar que módulos necesarios cargan
lsmod | grep -E "nvme|amdgpu|iwlwifi|r8169"

# Probar módulo crypto descartado
modprobe serpent  # Debe fallar: "not found"
```
