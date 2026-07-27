#!/usr/bin/env python3
"""Executable Linux–SpASM x86_64 ABI v2 conformance checks."""

import argparse
from pathlib import Path
import re
import subprocess
import sys


class Failure(Exception):
    pass


def run(*command):
    result = subprocess.run(
        command, check=False, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    if result.returncode:
        raise Failure(
            f"{' '.join(map(str, command))} termino con "
            f"{result.returncode}:\n{result.stdout}"
        )
    return result.stdout


def require(condition, message):
    if not condition:
        raise Failure(message)


def section_table(path):
    output = run("readelf", "-SW", path)
    sections = {}
    for line in output.splitlines():
        match = re.match(
            r"\s*\[\s*(\d+)\]\s+(\S+)\s+\S+\s+\S+\s+\S+\s+\S+\s+"
            r"\S+\s+(\S*)\s+\S+\s+\S+\s+(\d+)",
            line,
        )
        if match:
            index, name, flags, alignment = match.groups()
            sections[name] = {
                "index": int(index),
                "flags": flags,
                "alignment": int(alignment),
            }
    return sections


def symbol_rows(path, name):
    output = run("readelf", "-Ws", path)
    rows = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) >= 8 and fields[-1] == name:
            rows.append(fields)
    return rows


def check_builtin(build):
    obj = build / "lib/math/gcd_spasm.o"
    require(obj.is_file(), f"falta objeto builtin: {obj}")

    symbols = symbol_rows(obj, "nice_gcd_spasm")
    require(len(symbols) == 1,
            "nice_gcd_spasm debe estar definido exactamente una vez")
    symbol = symbols[0]
    require(symbol[3] == "FUNC",
            "nice_gcd_spasm no es un simbolo ELF FUNC")
    require(symbol[4] == "GLOBAL",
            "nice_gcd_spasm no tiene visibilidad GLOBAL")
    require(symbol[6] != "UND", "nice_gcd_spasm quedo indefinido")

    sections = section_table(obj)
    require(".text" in sections, "falta seccion .text")
    text = sections[".text"]
    require("A" in text["flags"] and "X" in text["flags"],
            ".text no tiene flags AX")
    require(text["alignment"] >= 16, ".text no esta alineada a 16 bytes")
    require(".note.GNU-stack" in sections, "falta .note.GNU-stack")
    require("X" not in sections[".note.GNU-stack"]["flags"],
            "la pila quedo marcada ejecutable")
    forbidden = {".modinfo", ".spasm.text", ".init.text", ".exit.text"}
    require(not forbidden.intersection(sections),
            "objeto builtin contiene secciones de modulo")

    relocations = run("readelf", "-rW", obj)
    relocation_symbols = set()
    for line in relocations.splitlines():
        if "R_X86_64_" not in line:
            continue
        fields = line.split()
        if len(fields) >= 5:
            relocation_symbols.add(fields[4])
    require(
        relocation_symbols <= {"__x86_return_thunk"},
        f"relocaciones builtin no autorizadas: {sorted(relocation_symbols)}",
    )

    disassembly = run(
        "objdump", "-dr", "--disassemble=nice_gcd_spasm", obj
    )
    require("endbr64" in disassembly,
            "nice_gcd_spasm no comienza con ENDBR64")
    require(re.search(r"\bpush\s+%rbp", disassembly), "falta prologo rbp")
    require(re.search(r"\bpop\s+%rbp", disassembly), "falta epilogo rbp")
    require("__x86_return_thunk" in disassembly,
            "los retornos no usan RET del kernel")
    require(not re.search(r"%(?:rbx|r12|r13|r14|r15)\b", disassembly),
            "nice_gcd_spasm modifica registros callee-saved no soportados")

    entry = build / "lib/math/gcd_spasm_entry.o"
    require(entry.is_file(), f"falta entrada Linux: {entry}")
    entry_symbols = symbol_rows(entry, "gcd")
    require(len(entry_symbols) == 1 and entry_symbols[0][3] == "FUNC"
            and entry_symbols[0][4] == "GLOBAL",
            "la entrada gcd no preserva GLOBAL FUNC")
    entry_disassembly = run("objdump", "-dr", "--disassemble=gcd", entry)
    require("nice_gcd_spasm" in entry_disassembly,
            "gcd no transfiere control al nucleo SpASM")

    reserved = [
        int(value, 16)
        for value in re.findall(r"\bsub\s+\$0x([0-9a-f]+),%rsp", disassembly)
    ]
    restored = [
        int(value, 16)
        for value in re.findall(r"\badd\s+\$0x([0-9a-f]+),%rsp", disassembly)
    ]
    require(reserved and all(value % 16 == 0 for value in reserved),
            "la reserva de pila no es multiplo de 16")
    require(set(restored) == set(reserved),
            "los caminos de retorno no restauran la reserva de pila")

    objtool = build / "tools/objtool/objtool"
    require(objtool.is_file(), f"falta objtool: {objtool}")
    run(
        objtool,
        "--stackval",
        "--orc",
        "--rethunk",
        "--sls",
        "--no-unreachable",
        "--dry-run",
        "--werror",
        obj,
    )


def check_vmlinux(build):
    vmlinux = build / "vmlinux"
    require(vmlinux.is_file(), f"falta vmlinux: {vmlinux}")
    symbols = run("nm", "-n", vmlinux)
    require(len(re.findall(r" T gcd$", symbols, re.MULTILINE)) == 1,
            "vmlinux no contiene exactamente un simbolo T gcd")
    require(re.search(r" r __ksymtab_gcd$", symbols, re.MULTILINE),
            "vmlinux no exporta __ksymtab_gcd")
    require(re.search(r" r __kstrtab_gcd$", symbols, re.MULTILINE),
            "vmlinux no exporta __kstrtab_gcd")
    sections = section_table(vmlinux)
    require(".orc_unwind" in sections and ".orc_unwind_ip" in sections,
            "vmlinux no contiene metadatos ORC")


def check_module(build):
    module = build / "spasm-modules/hello/spasm_hello.ko"
    require(module.is_file(), f"falta modulo comparativo: {module}")
    sections = section_table(module)
    for name in (".spasm.text", ".init.text", ".exit.text", ".modinfo"):
        require(name in sections, f"modulo sin seccion requerida {name}")

    symbols = run("readelf", "-Ws", module)
    require(re.search(
        r"\bFUNC\s+LOCAL\s+\S+\s+\S+\s+spasm_fn_nice_gcd$",
        symbols,
        re.MULTILINE,
    ), "nice_gcd interna no tiene visibilidad LOCAL")
    for name in ("init_module", "cleanup_module"):
        rows = symbol_rows(module, name)
        require(len(rows) == 1 and rows[0][3] == "FUNC"
                and rows[0][4] == "GLOBAL",
                f"{name} no cumple el contrato de modulo")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel-build", type=Path, required=True)
    args = parser.parse_args()
    build = args.kernel_build.resolve()

    try:
        config = (build / ".config").read_text(encoding="utf-8")
        require("CONFIG_NICE_KERNEL_GCD_SPASM=y" in config,
                "el build no selecciona CONFIG_NICE_KERNEL_GCD_SPASM=y")
        check_builtin(build)
        print("ok - builtin ELF y ABI")
        check_vmlinux(build)
        print("ok - simbolo Linux y ORC en vmlinux")
        check_module(build)
        print("ok - modulo, entradas y visibilidad")
    except (Failure, OSError) as error:
        print(f"not ok - {error}", file=sys.stderr)
        return 1

    print("1..3")
    print("# Linux-SpASM x86_64 ABI v2: CONFORME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
