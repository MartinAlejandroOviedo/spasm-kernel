#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
busybox_bin=${BUSYBOX:-$(command -v busybox)}
output=${1:-"$script_dir/spasm-initramfs.cpio.gz"}

if [ ! -x "$busybox_bin" ]; then
	echo "No se encontró un BusyBox ejecutable: $busybox_bin" >&2
	exit 1
fi

work_dir=$(mktemp -d)
root_dir=$work_dir/root
trap 'rm -rf "$work_dir"' EXIT HUP INT TERM

mkdir -p "$root_dir/bin" "$root_dir/dev" "$root_dir/etc" "$root_dir/proc"
mkdir -p "$root_dir/run" "$root_dir/sys" "$root_dir/tmp"
cp "$busybox_bin" "$root_dir/bin/busybox"
cp "$script_dir/init" "$root_dir/init"
chmod 0755 "$root_dir/init" "$root_dir/bin/busybox"
ln -s busybox "$root_dir/bin/sh"

if [ -n "${SPASM_MODULE:-}" ]; then
	if [ ! -f "$SPASM_MODULE" ]; then
		echo "No se encontró el módulo SpASM: $SPASM_MODULE" >&2
		exit 1
	fi
	mkdir -p "$root_dir/lib/modules"
	cp "$SPASM_MODULE" "$root_dir/lib/modules/spasm_hello.ko"
fi

# Un BusyBox dinámico necesita el cargador ELF y sus bibliotecas. Para una
# versión estática, ldd no devuelve rutas y este bloque no copia nada.
ldd "$busybox_bin" 2>/dev/null |
	awk '
		/=> \// { print $3 }
		$1 ~ /^\// { print $1 }
	' |
	while IFS= read -r library; do
		[ -n "$library" ] || continue
		mkdir -p "$root_dir$(dirname "$library")"
		cp -L "$library" "$root_dir$library"
	done

mkdir -p "$(dirname "$output")"
(
	cd "$root_dir"
	find . -print0 |
		cpio --null -o --format=newc --owner=0:0 2>/dev/null |
		gzip -9
) >"$output"

echo "Initramfs creado: $output"
echo "Tamaño: $(stat -c %s "$output") bytes"
