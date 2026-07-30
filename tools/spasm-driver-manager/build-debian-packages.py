#!/usr/bin/env python3
"""Build the first split Debian packages for spasm-kernel."""

from __future__ import annotations

import argparse
from pathlib import Path
import os
import shutil
import subprocess
import sys


CORE_SEEDS = (
    "nvme",
    "ext4",
    # Filesystems needed by a normal Debian installation and its boot flow.
    "vfat",
    "nls_cp437",
    "nls_ascii",
    "squashfs",
    "loop",
    "binfmt_misc",
    "autofs4",
    "configfs",
    "ahci",
    "ata_piix",
    "sd_mod",
    "usb_storage",
    "uas",
    "xhci_pci",
    "usbhid",
    "hid_generic",
    "evdev",
    "dm_mod",
    "dm_crypt",
)

DESKTOP_SEEDS = (
    "amdgpu",
    "i915",
    "nouveau",
    "r8169",
    "tun",
    # VPNs and container/network tools use the nftables backend on Debian.
    "nf_tables",
    "nft_compat",
    "nft_chain_nat",
    "nft_masq",
    "nft_ct",
    "xt_mark",
    "xt_connmark",
    "xt_comment",
    "xt_multiport",
    "xt_tcpudp",
    "xt_addrtype",
    "xt_conntrack",
    "xt_MASQUERADE",
    "e1000e",
    "igc",
    "iwlwifi",
    "ath9k",
    "rtw88_pci",
    "rtw89_pci",
    "snd_hda_intel",
    "snd_hda_codec_hdmi",
    "snd_usb_audio",
    "btusb",
    "uvcvideo",
    "uinput",
    "mousedev",
    "psmouse",
    # Common desktop/system services request these during early userspace.
    "lp",
    "ppdev",
    "parport_pc",
    "i2c_dev",
    "msr",
    "snd_seq",
    "snd_timer",
)


def run(*command: str, capture: bool = False) -> str:
    result = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"{' '.join(command)} falló: {detail}")
    return result.stdout if capture else ""


def resolve_modules(stage: Path, release: str, seeds: tuple[str, ...]) -> set[Path]:
    modules: set[Path] = set()
    modprobe = shutil.which("modprobe") or "/usr/sbin/modprobe"
    for seed in seeds:
        output = run(
            modprobe,
            "-d",
            str(stage),
            "-S",
            release,
            "--show-depends",
            seed,
            capture=True,
        )
        for line in output.splitlines():
            if not line.startswith("insmod "):
                continue
            module = Path(line.split(maxsplit=2)[1]).resolve()
            try:
                module.relative_to(stage.resolve())
            except ValueError as error:
                raise RuntimeError(f"módulo fuera del staging: {module}") from error
            modules.add(module)
    return modules


def write_control(
    root: Path,
    package: str,
    version: str,
    description: str,
    depends: tuple[str, ...] = (),
    provides: tuple[str, ...] = (),
) -> None:
    debian = root / "DEBIAN"
    debian.mkdir(parents=True)
    fields = [
        f"Package: {package}",
        f"Version: {version}",
        "Section: kernel",
        "Priority: optional",
        "Architecture: amd64",
        "Maintainer: spasm-kernel project <noreply@spasm-kernel.local>",
    ]
    if depends:
        fields.append(f"Depends: {', '.join(depends)}")
    if provides:
        fields.append(f"Provides: {', '.join(provides)}")
    fields.extend(
        (
            f"Description: {description}",
            " Kernel x86_64 con integración SpASM y módulos separados por ABI.",
        )
    )
    (debian / "control").write_text("\n".join(fields) + "\n", encoding="utf-8")


def write_script(root: Path, name: str, content: str) -> None:
    path = root / "DEBIAN" / name
    path.write_text("#!/bin/sh\nset -e\n" + content.strip() + "\n", encoding="utf-8")
    path.chmod(0o755)


def copy_module_set(
    stage: Path, build: Path, package_root: Path, modules: set[Path]
) -> None:
    sign_file = build / "scripts/sign-file"
    signing_key = build / "certs/signing_key.pem"
    signing_cert = build / "certs/signing_key.x509"
    for required in (sign_file, signing_key, signing_cert):
        if not required.is_file():
            raise RuntimeError(f"falta insumo para firmar módulos: {required}")

    for source in sorted(modules):
        relative = source.relative_to(stage)
        parts = relative.parts
        try:
            kernel_index = parts.index("kernel")
        except ValueError as error:
            raise RuntimeError(f"ruta de módulo inesperada: {relative}") from error
        build_relative = Path(*parts[kernel_index + 1 :])
        if build_relative.suffix == ".xz":
            build_relative = build_relative.with_suffix("")
        original = build / build_relative
        if not original.is_file():
            raise RuntimeError(f"falta módulo original: {original}")
        destination_relative = relative.with_suffix("") if relative.suffix == ".xz" else relative
        destination = package_root / destination_relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, destination)
        strip = shutil.which("strip") or "/usr/bin/strip"
        run(strip, "--strip-debug", str(destination))
        # La firma debe ser la última modificación del .ko. Firmar antes de
        # strip invalida el apéndice PKCS#7 y modprobe responde EINVAL.
        run(
            str(sign_file),
            "sha256",
            str(signing_key),
            str(signing_cert),
            str(destination),
        )


def build_deb(root: Path, output: Path, package: str, version: str) -> Path:
    destination = output / f"{package}_{version}_amd64.deb"
    run("dpkg-deb", "--root-owner-group", "-Zxz", "--build", str(root), str(destination))
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", default="0.2.0-1")
    parser.add_argument("--abi", default="6.19.14-1")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build = args.build.resolve()
    stage = args.stage.resolve()
    output = args.output.resolve()
    release = (build / "include/config/kernel.release").read_text(encoding="utf-8").strip()
    expected = "6.19.14-spasm-kernel-desktop-amd64"
    if release != expected:
        raise RuntimeError(f"release inesperada: {release!r}; se esperaba {expected!r}")

    module_root = stage / "lib/modules" / release
    if not module_root.is_dir():
        raise RuntimeError(f"falta staging de módulos: {module_root}")

    output.mkdir(parents=True, exist_ok=True)
    work = output / ".work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()

    core_modules = resolve_modules(stage, release, CORE_SEEDS)
    desktop_modules = resolve_modules(stage, release, DESKTOP_SEEDS) - core_modules

    image_name = f"spasm-kernel-image-{release}"
    core_name = f"spasm-kernel-modules-core-{args.abi}"
    desktop_name = f"spasm-kernel-drivers-desktop-{args.abi}"
    care_name = "spasm-kernel-machine-care"
    image_dependency = f"{image_name} (= {args.version})"

    image = work / image_name
    write_control(
        image,
        image_name,
        args.version,
        "imagen estándar de spasm-kernel para escritorio amd64",
        provides=(f"spasm-kernel-abi-{args.abi}",),
    )
    boot = image / "boot"
    boot.mkdir()
    shutil.copy2(build / "arch/x86/boot/bzImage", boot / f"vmlinuz-{release}")
    shutil.copy2(build / ".config", boot / f"config-{release}")
    shutil.copy2(build / "System.map", boot / f"System.map-{release}")
    installed_modules = image / "lib/modules" / release
    installed_modules.mkdir(parents=True)
    for metadata in ("modules.builtin", "modules.builtin.modinfo", "modules.order"):
        shutil.copy2(module_root / metadata, installed_modules / metadata)
    write_script(
        image,
        "postinst",
        f"""
depmod {release}
if [ -e /boot/initrd.img-{release} ]; then
    update-initramfs -u -k {release}
else
    update-initramfs -c -k {release}
fi
update-grub
""",
    )
    write_script(
        image,
        "postrm",
        f"""
if [ "$1" = purge ] || [ "$1" = remove ]; then
    update-initramfs -d -k {release} || true
fi
update-grub || true
""",
    )

    core = work / core_name
    write_control(
        core,
        core_name,
        args.version,
        "módulos esenciales de arranque para spasm-kernel",
        depends=(image_dependency,),
    )
    copy_module_set(stage, build, core, core_modules)
    write_script(
        core,
        "postinst",
        f"depmod {release}\nupdate-initramfs -u -k {release}",
    )
    write_script(
        core,
        "postrm",
        f"depmod {release} || true\nupdate-initramfs -u -k {release} || true",
    )

    desktop = work / desktop_name
    write_control(
        desktop,
        desktop_name,
        args.version,
        "controladores habituales de escritorio para spasm-kernel",
        depends=(image_dependency, f"{core_name} (= {args.version})"),
    )
    copy_module_set(stage, build, desktop, desktop_modules)
    write_script(
        desktop,
        "postinst",
        f"depmod {release}\nupdate-initramfs -u -k {release}",
    )
    write_script(
        desktop,
        "postrm",
        f"depmod {release} || true\nupdate-initramfs -u -k {release} || true",
    )

    care = work / care_name
    write_control(
        care,
        care_name,
        args.version,
        "protección observacional Machine Care para spasm-kernel",
        depends=("python3",),
    )
    repository = Path(__file__).resolve().parents[2]
    care_source = repository / "tools/spasm-care-agent"
    care_lib = care / "usr/lib/spasm-kernel"
    care_lib.mkdir(parents=True)
    shutil.copy2(care_source / "spasm-care-agent", care_lib / "spasm-care-agent")
    (care_lib / "spasm-care-agent").chmod(0o755)
    run(
        str(care_source / "build-policy-library"),
        str(care_lib / "libspasm-care-policy.so"),
    )
    unit_dir = care / "usr/lib/systemd/system"
    unit_dir.mkdir(parents=True)
    shutil.copy2(
        care_source / "spasm-care-agent.service",
        unit_dir / "spasm-care-agent.service",
    )
    write_script(
        care,
        "postinst",
        """
if command -v systemctl >/dev/null 2>&1; then
    systemctl daemon-reload || true
    systemctl enable --now spasm-care-agent.service || true
fi
""",
    )
    write_script(
        care,
        "prerm",
        """
if command -v systemctl >/dev/null 2>&1; then
    systemctl disable --now spasm-care-agent.service || true
fi
""",
    )
    write_script(
        care,
        "postrm",
        """
if command -v systemctl >/dev/null 2>&1; then
    systemctl daemon-reload || true
fi
""",
    )

    artifacts = (
        build_deb(image, output, image_name, args.version),
        build_deb(core, output, core_name, args.version),
        build_deb(desktop, output, desktop_name, args.version),
        build_deb(care, output, care_name, args.version),
    )
    print(f"release={release}")
    print(f"core_modules={len(core_modules)}")
    print(f"desktop_modules={len(desktop_modules)}")
    for artifact in artifacts:
        print(artifact)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError) as error:
        print(f"build-debian-packages: {error}", file=sys.stderr)
        raise SystemExit(1)
