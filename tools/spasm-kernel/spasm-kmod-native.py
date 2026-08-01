#!/usr/bin/env python3
"""Compile the minimal SpASM kernel-module subset to native x86_64 assembly."""

import argparse
import pathlib
import re
import sys


class CompileError(Exception):
    pass


HEADER_RE = re.compile(
    r'^\s*(module|license|author|description)\s+"((?:[^"\\]|\\.)*)"\s*$'
)
KLOG_RE = re.compile(r'klog\s*\(\s*"((?:[^"\\]|\\.)*)"\s*\)')
RETURN_RE = re.compile(r"return\s+([^;{}\n]+)\s*;?")
RESOURCE_RE = re.compile(
    r"recurso\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
    r"kalloc<u8>\(\s*([0-9]+)\s*\)\s+else\s+return\s+(-?[A-Za-z0-9_]+)"
)
USE_RE = re.compile(r"usar\s+([A-Za-z_][A-Za-z0-9_]*)")
FREE_RE = re.compile(r"liberar\s+([A-Za-z_][A-Za-z0-9_]*)")
STORE_RE = re.compile(
    r"guardar<([A-Za-z_][A-Za-z0-9_]*)>\(\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*,\s*"
    r"([0-9]+|[A-Za-z_][A-Za-z0-9_]*)\s*,\s*"
    r"(-?[0-9]+|[A-Za-z_][A-Za-z0-9_]*)\s*\)\s*;?"
)
VAR_RE = re.compile(
    r"(var|let)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^;{}]+)\s*;"
)
TYPED_VAR_RE = re.compile(
    r"(var|let)\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*"
    r"((?:[A-Za-z_][A-Za-z0-9_]*(?:<[A-Za-z_][A-Za-z0-9_]*>)?(?:\[[0-9]+\])?\??)|"
    r"(?:fn\s*\([^()]*\)\s*->\s*[A-Za-z_][A-Za-z0-9_]*(?:<[A-Za-z_][A-Za-z0-9_]*>)?\??))"
    r"\s*=\s*([^;{}]+)\s*;"
)
ASSIGN_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^;{}]+)\s*;")
ARRAY_ASSIGN_RE = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*(-?[0-9]+|[A-Za-z_][A-Za-z0-9_]*)\s*\]\s*=\s*([^;{}]+)\s*;"
)
ARRAY_ACCESS_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*(-?[0-9]+|[A-Za-z_][A-Za-z0-9_]*)\s*\]\s*$"
)
FIELD_ASSIGN_RE = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*)((?:\s*\.\s*[A-Za-z_][A-Za-z0-9_]*)*)\s*=\s*([^;{}]+)\s*;"
)
IF_HEAD_RE = re.compile(r"if\s*\(([^()]*)\)\s*\{")
WHILE_HEAD_RE = re.compile(r"while\s*\(([^()]*)\)\s*\{")
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
ERRNOS = {"ENOMEM": -12}
ERRNOS.update({
    "EINVAL": -22,
    "ENOSYS": -38,
    "ENODEV": -19,
    "EIO": -5,
    "EBUSY": -16,
    "ENOENT": -2,
    "ENOSPC": -28,
    "ENODATA": -61,
    "ERANGE": -34,
    "EFAULT": -14,
})
ENUM_VALUES = {}
STATIC_DATA = {}

STATIC_RE = re.compile(
    r"\bstatic\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*"
    r"([A-Za-z_][A-Za-z0-9_]*(?:<[A-Za-z_][A-Za-z0-9_]*>)?)\s*"
    r"\[([0-9]+)\]\s*=\s*\{([^}]*)\}\s*;"
)
INTEGER_TYPES = {
    "u8": (0, 2**8 - 1),
    "i8": (-(2**7), 2**7 - 1),
    "u16": (0, 2**16 - 1),
    "i16": (-(2**15), 2**15 - 1),
    "u32": (0, 2**32 - 1),
    "i32": (-(2**31), 2**31 - 1),
    "u64": (0, 2**64 - 1),
    "i64": (-(2**63), 2**63 - 1),
    "usize": (0, 2**64 - 1),
    "isize": (-(2**63), 2**63 - 1),
    "bool": (0, 1),
}
ARG_REGISTERS = ("rdi", "rsi", "rdx", "rcx", "r8", "r9")
ARG_REGISTERS_32 = ("edi", "esi", "edx", "ecx", "r8d", "r9d")
EXPR_RE = re.compile(
    r"^\s*(-?[0-9]+|[A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s*(<<|>>|[+\-*/%&|^])\s*(-?[0-9]+|[A-Za-z_][A-Za-z0-9_]*))?\s*$"
)
COND_RE = re.compile(
    r"^\s*(-?[0-9]+|[A-Za-z_][A-Za-z0-9_]*)\s*"
    r"(==|!=|<=|>=|<|>)\s*"
    r"(-?[0-9]+|[A-Za-z_][A-Za-z0-9_]*)\s*$"
)
CALL_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(([^()]*)\)\s*$"
)
FUNCTION_HEAD_RE = re.compile(
    r"\b(?:(export)\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.+)\)\s*"
    r"->\s*([A-Za-z_][A-Za-z0-9_]*(?:<[A-Za-z_][A-Za-z0-9_]*>)?\??)"
    r"\s*\{"
)
EXTERN_FUNCTION_RE = re.compile(
    r"\bextern\s+fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^()]*)\)\s*"
    r"->\s*([A-Za-z_][A-Za-z0-9_]*(?:<[A-Za-z_][A-Za-z0-9_]*>)?\??)"
)
PARAM_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*"
    r"((?:[A-Za-z_][A-Za-z0-9_]*(?:<[A-Za-z_][A-Za-z0-9_]*>)?\??)|"
    r"(?:fn\s*\([^()]*\)\s*->\s*[A-Za-z_][A-Za-z0-9_]*(?:<[A-Za-z_][A-Za-z0-9_]*>)?\??))\s*$"
)
POINTER_TYPE_RE = re.compile(
    r"^ptr<([A-Za-z_][A-Za-z0-9_]*)>(\?)?$"
)
STRUCT_HEAD_RE = re.compile(
    r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{"
)
FIELD_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*"
    r"([A-Za-z_][A-Za-z0-9_]*(?:<[A-Za-z_][A-Za-z0-9_]*>)?(?:\[[0-9]+\])?\??)\s*;?\s*$"
)
DOT_ACCESS_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\.\s*([A-Za-z_][A-Za-z0-9_]*)\s*$"
)
CHAINED_DOT_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)(\s*\.\s*[A-Za-z_][A-Za-z0-9_]*)*\s*$"
)
FIELD_PATH_RE = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*)"
)
LOAD_RE = re.compile(
    r"^\s*cargar<([A-Za-z_][A-Za-z0-9_]*)>\(\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*,\s*"
    r"([0-9]+|[A-Za-z_][A-Za-z0-9_]*)\s*\)\s*$"
)
TYPE_WIDTHS = {
    "u8": 1,
    "i8": 1,
    "bool": 1,
    "u16": 2,
    "i16": 2,
    "u32": 4,
    "i32": 4,
    "u64": 8,
    "i64": 8,
    "usize": 8,
    "isize": 8,
}
ABI_V2_EXPORTED_TYPES = {"u8", "i8", "u16", "i16", "u32", "i32", "u64", "i64", "usize", "isize", "bool"}
KERNEL_EXTERN_ALLOWLIST = {
    "gcd": (("usize", "usize"), "usize"),
    "int_sqrt": (("usize",), "usize"),
    "lcm": (("usize", "usize"), "usize"),
    "int_pow": (("u64", "u64"), "u64"),
    "hex_to_bin": (("i32",), "i32"),
}
ATOMIC_EXPR_RE = re.compile(
    r"\s*(atomic_load|atomic_xchg|atomic_cmpxchg|atomic_add|atomic_sub)"
    r"<([A-Za-z_][A-Za-z0-9_]*)>\s*\(\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*(?:,\s*(-?[0-9]+|[A-Za-z_][A-Za-z0-9_]*))?"
    r"(?:\s*,\s*(-?[0-9]+|[A-Za-z_][A-Za-z0-9_]*))?\s*\)\s*;?\s*"
)
PTR_OP_RE = re.compile(
    r"\s*(ptr_load|ptr_store|ptr_offset)"
    r"<([A-Za-z_][A-Za-z0-9_]*)>\s*\(\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*(?:,\s*(-?[0-9]+|[A-Za-z_][A-Za-z0-9_]*))?"
    r"\s*\)\s*;?\s*"
)
BARRIER_CALL_RE = re.compile(
    r"\s*(smp_mb|smp_rmb|smp_wmb|barrier)\s*\(\s*\)\s*;?\s*"
)

STRUCT_LAYOUTS = {}

FN_TYPE_RE = re.compile(
    r"^fn\s*\(([^()]*)\)\s*->\s*"
    r"([A-Za-z_][A-Za-z0-9_]*(?:<[A-Za-z_][A-Za-z0-9_]*>)?\??)\s*$"
)

INTERNAL_FN_RE = re.compile(
    r"^\s*(spasm_fn_[A-Za-z_][A-Za-z0-9_]*)\s*$"
)

ENUM_HEAD_RE = re.compile(
    r"\benum\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{"
)
ENUM_MEMBER_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(-?[0-9]+)\s*,?\s*$"
)


def format_array_type(type_name, count):
    return f"{type_name}[{count}]"


def parse_array_type(type_name):
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:<[A-Za-z_][A-Za-z0-9_]*>)?)\[([0-9]+)\]$", type_name)
    if not match:
        return None, None
    return match.group(1), int(match.group(2))


def is_fn_type(type_name):
    return FN_TYPE_RE.match(type_name) is not None


def fn_type_info(type_name):
    match = FN_TYPE_RE.match(type_name)
    if not match:
        return None
    params_text, return_type = match.groups()
    params = []
    if params_text.strip():
        for raw in smart_split(params_text):
            raw = raw.strip()
            if raw:
                params.append(raw)
    return tuple(params), return_type


def extract_enums(source):
    enum_entries = []
    spans = []
    position = 0
    while True:
        match = ENUM_HEAD_RE.search(source, position)
        if not match:
            break
        name = match.group(1)
        open_index = match.end() - 1
        close_index = find_closing_brace(source, open_index)
        body = source[open_index + 1 : close_index]
        members = {}
        next_auto = 0
        for piece in body.split(","):
            piece = piece.strip()
            if not piece:
                continue
            member_match = ENUM_MEMBER_RE.match(piece)
            if not member_match:
                raise CompileError(
                    f"miembro invalido en enum {name}: {piece!r}"
                )
            member_name, value_text = member_match.groups()
            value = int(value_text)
            if member_name in members:
                raise CompileError(
                    f"miembro duplicado en enum {name}: {member_name}"
                )
            members[member_name] = value
            ENUM_VALUES[member_name] = (value, name)
            next_auto = value + 1
        if not members:
            raise CompileError(f"enum {name} sin miembros")
        enum_entries.append((name, members))
        spans.append((match.start(), close_index + 1))
        position = close_index + 1
    remaining = list(source)
    for start, end in spans:
        remaining[start:end] = " " * (end - start)
    return dict(enum_entries), "".join(remaining)


def extract_static_data(source):
    entries = {}
    spans = []
    position = 0
    while True:
        match = STATIC_RE.search(source, position)
        if not match:
            break
        name, elem_type, count_text, values_text = match.groups()
        if name in entries:
            raise CompileError(f"dato estatico duplicado: {name}")
        if not is_supported_type(elem_type):
            raise CompileError(f"tipo no soportado en static {name}: {elem_type}")
        raw_values = [v.strip() for v in smart_split(values_text) if v.strip()]
        count = int(count_text)
        values = []
        for raw in raw_values:
            if raw.startswith("0x") or raw.startswith("0X"):
                values.append(int(raw, 16))
            elif raw.lstrip("-").isdigit():
                values.append(int(raw))
            else:
                raise CompileError(f"valor invalido en static {name}: {raw}")
        entries[name] = (elem_type, count, values)
        spans.append((match.start(), match.end()))
        position = match.end()
    remaining = list(source)
    for start, end in spans:
        remaining[start:end] = " " * (end - start)
    STATIC_DATA.update(entries)
    return entries, "".join(remaining)


def compute_struct_layout(name, fields):
    offset = 0
    max_align = 1
    field_info = {}
    for field_name, field_type in fields:
        field_width, field_align = type_size_and_align(field_type)
        padding = (field_align - (offset % field_align)) % field_align
        offset += padding
        field_info[field_name] = (offset, field_type)
        offset += field_width
        max_align = max(max_align, field_align)
    tail_padding = (max_align - (offset % max_align)) % max_align
    total_size = offset + tail_padding
    result = {
        "size": total_size,
        "align": max_align,
        "fields": field_info,
    }
    STRUCT_LAYOUTS[name] = result
    return result


def type_size_and_align(type_name):
    if is_fn_type(type_name):
        return 8, 8
    inner_type, count = parse_array_type(type_name)
    if inner_type is not None:
        elem_width, elem_align = type_size_and_align(inner_type)
        return elem_width * count, elem_align
    if type_name in TYPE_WIDTHS:
        w = TYPE_WIDTHS[type_name]
        return w, w
    if is_struct_type(type_name):
        layout = STRUCT_LAYOUTS.get(type_name)
        if layout:
            return layout["size"], layout["align"]
    if is_pointer_type(type_name):
        return 8, 8
    raise CompileError(f"tipo sin tamano conocido: {type_name}")


def is_struct_type(type_name):
    return type_name in STRUCT_LAYOUTS


def extract_structs(source):
    structs = {}
    spans = []
    position = 0
    while True:
        match = STRUCT_HEAD_RE.search(source, position)
        if not match:
            break
        name = match.group(1)
        if name in structs:
            raise CompileError(f"struct duplicado: {name}")
        if name in INTEGER_TYPES:
            raise CompileError(f"struct {name} colisiona con tipo integrado")
        open_index = match.end() - 1
        close_index = find_closing_brace(source, open_index)
        body = source[open_index + 1 : close_index]
        fields = []
        field_names = set()
        for piece in body.split(";"):
            if not piece.strip():
                continue
            field_match = FIELD_RE.match(piece)
            if not field_match:
                raise CompileError(
                    f"declaracion invalida en struct {name}: {piece.strip()!r}"
                )
            fname, ftype = field_match.groups()
            if fname in field_names:
                raise CompileError(
                    f"campo duplicado en struct {name}: {fname}"
                )
            if not is_supported_type(ftype) and ftype not in structs:
                raise CompileError(
                    f"tipo de campo no soportado en struct {name} "
                    f"campo {fname}: {ftype}"
                )
            field_names.add(fname)
            fields.append((fname, ftype))
        if not fields:
            raise CompileError(f"struct {name} sin campos")
        structs[name] = fields
        spans.append((match.start(), close_index + 1))
        position = close_index + 1

    remaining = list(source)
    for start, end in spans:
        remaining[start:end] = " " * (end - start)
    for sname, sfields in structs.items():
        compute_struct_layout(sname, sfields)
    return structs, "".join(remaining)


def decode_string(value):
    try:
        return bytes(value, "utf-8").decode("unicode_escape")
    except UnicodeDecodeError as exc:
        raise CompileError(f"cadena SpASM invalida: {exc}") from exc


def asm_string(value):
    raw = value.encode("utf-8")
    escaped = []
    for byte in raw:
        if byte == 0x22:
            escaped.append(r"\"")
        elif byte == 0x5C:
            escaped.append(r"\\")
        elif 0x20 <= byte <= 0x7E:
            escaped.append(chr(byte))
        else:
            escaped.append(f"\\{byte:03o}")
    return "".join(escaped)


def parse_source(source, kind="module"):
    metadata = {}
    STRUCT_LAYOUTS.clear()
    ENUM_VALUES.clear()
    STATIC_DATA.clear()
    block_texts, source_without_blocks = extract_on_blocks(source)
    static_entries, source_without_blocks = extract_static_data(source_without_blocks)
    enums, source_without_blocks = extract_enums(source_without_blocks)
    structs, source_without_blocks = extract_structs(source_without_blocks)
    functions, source_without_blocks = extract_functions(source_without_blocks)
    externs, source_without_blocks = extract_externs(source_without_blocks)
    functions.extend(externs)
    function_names = [function["name"] for function in functions]
    if len(function_names) != len(set(function_names)):
        raise CompileError("funcion interna o externa duplicada")
    function_signatures = {
        function["name"]: function for function in functions
    }
    for function in functions:
        if not function.get("exported"):
            continue
        if kind != "builtin":
            raise CompileError(
                "export fn solo se admite en objetos builtin"
            )
        if function["name"] in ("init_module", "cleanup_module"):
            raise CompileError(
                f"simbolo exportado reservado: {function['name']}"
            )
        abi_types = [
            param_type for _param_name, param_type in function["params"]
        ]
        abi_types.append(function["return_type"])
        for type_name in abi_types:
            if (
                type_name not in ABI_V2_EXPORTED_TYPES
                and not is_pointer_type(type_name)
                and not is_struct_type(type_name)
                and not is_fn_type(type_name)
            ):
                raise CompileError(
                    f"export fn {function['name']}: {type_name} "
                    "no tiene representacion ABI v2 estable"
                )
    for function in functions:
        if function.get("external"):
            continue
        function["statements"] = parse_statements(
            function.pop("body"),
            "function",
            variables=dict(function["params"]),
            functions=function_signatures,
            return_type=function["return_type"],
        )
        if not any(
            statement[0] == "return_expr"
            for statement in function["statements"]
        ):
            raise CompileError(
                f"funcion {function['name']}: falta return"
            )

    for line_number, line in enumerate(source_without_blocks.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith(("#", "//")):
            continue
        if kind == "builtin":
            raise CompileError(
                f"linea {line_number}: declaracion no soportada en objeto builtin"
            )
        match = HEADER_RE.match(line)
        if not match:
            raise CompileError(f"linea {line_number}: declaracion no soportada")
        key, value = match.groups()
        if key in metadata:
            raise CompileError(f"linea {line_number}: {key} duplicado")
        metadata[key] = decode_string(value)

    if kind == "module":
        for required in ("module", "license"):
            if not metadata.get(required):
                raise CompileError(f"falta declaracion {required}")
        if not NAME_RE.match(metadata["module"]):
            raise CompileError("nombre de modulo invalido")
    elif not any(function.get("exported") for function in functions):
        raise CompileError("objeto builtin sin funciones exportadas")

    blocks = {}
    for kind, body in block_texts:
        if kind in blocks:
            raise CompileError(f"bloque on {kind} duplicado")
        blocks[kind] = parse_statements(
            body, kind, functions=function_signatures
        )

    if kind == "module" and ("load" not in blocks or "unload" not in blocks):
        raise CompileError("se requieren bloques on load y on unload")
    if kind == "builtin" and blocks:
        raise CompileError("un objeto builtin no admite bloques on load/on unload")
    return (
        metadata,
        blocks,
        [function for function in functions if not function.get("external")],
    )


def smart_split(text, sep=","):
    parts = []
    current = []
    depth = 0
    for char in text:
        if char in "({[<":
            depth += 1
        elif char in ")}]>":
            depth -= 1
        if char == sep and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    if current:
        parts.append("".join(current))
    return parts


def find_closing_brace(text, open_index):
    depth = 0
    in_string = False
    escaped = False
    for index in range(open_index, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    raise CompileError("bloque sin llave de cierre")


def extract_on_blocks(source):
    head_re = re.compile(r"\bon\s+(load|unload)\s*\{")
    blocks = []
    spans = []
    position = 0
    while True:
        match = head_re.search(source, position)
        if not match:
            break
        open_index = match.end() - 1
        close_index = find_closing_brace(source, open_index)
        blocks.append((match.group(1), source[open_index + 1 : close_index]))
        spans.append((match.start(), close_index + 1))
        position = close_index + 1
    remaining = list(source)
    for start, end in spans:
        remaining[start:end] = " " * (end - start)
    return blocks, "".join(remaining)


def extract_functions(source):
    functions = []
    spans = []
    names = set()
    position = 0
    while True:
        match = FUNCTION_HEAD_RE.search(source, position)
        if not match:
            break
        exported, name, params_text, return_type = match.groups()
        if name in names:
            raise CompileError(f"funcion duplicada: {name}")
        if not is_supported_type(return_type):
            raise CompileError(f"tipo de retorno no soportado: {return_type}")
        params = []
        param_names = set()
        if params_text.strip():
            for raw_param in smart_split(params_text):
                param_match = PARAM_RE.match(raw_param)
                if not param_match:
                    raise CompileError(
                        f"parametro invalido en funcion {name}: {raw_param.strip()}"
                    )
                param_name, param_type = param_match.groups()
                if not is_supported_type(param_type):
                    raise CompileError(
                        f"tipo de parametro no soportado: {param_type}"
                    )
                if param_name in param_names:
                    raise CompileError(
                        f"parametro duplicado en funcion {name}: {param_name}"
                    )
                param_names.add(param_name)
                params.append((param_name, param_type))
        if len(params) > len(ARG_REGISTERS):
            raise CompileError(f"funcion {name}: maximo 6 parametros")
        open_index = match.end() - 1
        close_index = find_closing_brace(source, open_index)
        body = source[open_index + 1 : close_index]
        functions.append(
            {
                "name": name,
                "params": params,
                "return_type": return_type,
                "body": body,
                "exported": bool(exported),
            }
        )
        names.add(name)
        spans.append((match.start(), close_index + 1))
        position = close_index + 1
    remaining = list(source)
    for start, end in spans:
        remaining[start:end] = " " * (end - start)
    return functions, "".join(remaining)


def parse_parameters(name, params_text):
    params = []
    param_names = set()
    if not params_text.strip():
        return params
    for raw_param in params_text.split(","):
        param_match = PARAM_RE.match(raw_param)
        if not param_match:
            raise CompileError(
                f"parametro invalido en funcion {name}: {raw_param.strip()}"
            )
        param_name, param_type = param_match.groups()
        if not is_supported_type(param_type):
            raise CompileError(f"tipo de parametro no soportado: {param_type}")
        if param_name in param_names:
            raise CompileError(
                f"parametro duplicado en funcion {name}: {param_name}"
            )
        param_names.add(param_name)
        params.append((param_name, param_type))
    if len(params) > len(ARG_REGISTERS):
        raise CompileError(f"funcion {name}: maximo 6 parametros")
    return params


def extract_externs(source):
    externs = []
    spans = []
    position = 0
    while True:
        match = EXTERN_FUNCTION_RE.search(source, position)
        if not match:
            break
        name, params_text, return_type = match.groups()
        params = parse_parameters(name, params_text)
        signature = (
            tuple(param_type for _param_name, param_type in params),
            return_type,
        )
        allowed = KERNEL_EXTERN_ALLOWLIST.get(name)
        if allowed is None:
            raise CompileError(f"funcion externa no autorizada: {name}")
        if signature != allowed:
            raise CompileError(
                f"firma externa no autorizada para {name}: {signature}"
            )
        externs.append(
            {
                "name": name,
                "params": params,
                "return_type": return_type,
                "external": True,
            }
        )
        end = match.end()
        while end < len(source) and source[end] in (";", " ", "\t", "\n", "\r"):
            end += 1
        spans.append((match.start(), end))
        position = end
    remaining = list(source)
    for start, end in spans:
        remaining[start:end] = " " * (end - start)
    return externs, "".join(remaining)


def parse_errno(value):
    if value.lstrip("-").isdigit():
        return int(value)
    name = value[1:] if value.startswith("-") else value
    if name not in ERRNOS:
        raise CompileError(f"errno no soportado: {value}")
    return ERRNOS[name]


def pointer_type(type_name):
    return POINTER_TYPE_RE.match(type_name)


def is_supported_type(type_name):
    if is_fn_type(type_name):
        return True
    inner_type, _count = parse_array_type(type_name)
    if inner_type is not None:
        return is_supported_type(inner_type)
    if type_name in INTEGER_TYPES:
        return True
    if is_struct_type(type_name):
        return True
    match = pointer_type(type_name)
    if match:
        inner = match.group(1)
        return inner in INTEGER_TYPES or is_struct_type(inner)
    return False


def is_pointer_type(type_name):
    return pointer_type(type_name) is not None


def is_nullable_pointer(type_name):
    match = pointer_type(type_name)
    return bool(match and match.group(2))


def validate_memory_access(
    type_name, resource_name, offset_text, resources, variables
):
    if type_name not in TYPE_WIDTHS:
        raise CompileError(f"tipo de acceso a memoria no soportado: {type_name}")
    resource = resources.get(resource_name)
    if resource is None:
        raise CompileError(f"recurso no declarado: {resource_name}")
    state, capacity = resource
    if state != "live":
        raise CompileError(f"recurso ya liberado: {resource_name}")
    width = TYPE_WIDTHS[type_name]
    offset = parse_operand(offset_text, variables)
    if offset[0] == "var":
        if variables[offset[1]] != "usize":
            raise CompileError(
                f"offset dinamico {offset[1]} debe ser usize, "
                f"no {variables[offset[1]]}"
            )
        return offset
    offset_value = offset[1]
    if offset_value % width:
        raise CompileError(
            f"acceso {type_name} desalineado en offset {offset_value}"
        )
    if offset_value + width > capacity:
        raise CompileError(
            f"acceso fuera de rango: "
            f"{resource_name}[{offset_value}:{offset_value + width}] "
            f"excede {capacity} bytes"
        )
    return offset


def parse_operand(value, variables, functions=None):
    value = value.strip()
    if value.lstrip("-").isdigit():
        return ("imm", int(value))
    if value in ENUM_VALUES:
        return ("imm", ENUM_VALUES[value][0])
    if value in ERRNOS:
        return ("imm", ERRNOS[value])
    if value in STATIC_DATA:
        return ("static_ref", value)
    if functions and value in functions and not functions[value].get("external"):
        return ("fn_ref", value)
    if value not in variables:
        raise CompileError(f"variable no declarada: {value}")
    return ("var", value)


def parse_expression(value, variables):
    match = EXPR_RE.match(value)
    if not match:
        raise CompileError(f"expresion no soportada: {value.strip()}")
    left, operator, right = match.groups()
    expression = [parse_operand(left, variables)]
    if operator:
        expression.extend((operator, parse_operand(right, variables)))
    return tuple(expression)


def validate_immediate(value, type_name):
    if is_fn_type(type_name):
        return
    if is_pointer_type(type_name):
        if value == 0 and is_nullable_pointer(type_name):
            return
        if value == 0:
            raise CompileError(
                f"null no es valido para puntero no anulable {type_name}"
            )
        raise CompileError(
            f"una direccion entera no se convierte implicitamente a {type_name}"
        )
    minimum, maximum = INTEGER_TYPES[type_name]
    if value < minimum or value > maximum:
        raise CompileError(
            f"valor {value} fuera de rango para {type_name}"
        )


def validate_expression_type(expression, variable_types, expected_type):
    if is_pointer_type(expected_type) and len(expression) != 1:
        raise CompileError("aritmetica de punteros no permitida")
    if is_fn_type(expected_type):
        if len(expression) != 1:
            raise CompileError("expresion invalida para tipo fn")
        return expected_type
    inner_type, _count = parse_array_type(expected_type)
    if inner_type is not None and is_struct_type(inner_type):
        if len(expression) == 1 and expression[0][0] == "imm":
            if expression[0][1] == 0:
                return expected_type
            raise CompileError(
                f"solo 0 es valido para inicializar array de struct {expected_type}"
            )
        raise CompileError(
            f"array de struct {expected_type} solo admite inicializacion con 0"
        )
    if is_struct_type(expected_type):
        if len(expression) == 1 and expression[0][0] == "imm":
            if expression[0][1] == 0:
                return expected_type
            raise CompileError(
                f"solo 0 es valido para inicializar struct {expected_type}"
            )
        raise CompileError(
            f"struct {expected_type} solo admite inicializacion con 0"
        )
    if inner_type is not None:
        expected_type = inner_type
    for operand in expression[::2]:
        kind, value = operand
        if kind in ("fn_ref", "static_ref"):
            continue
        if kind == "imm":
            validate_immediate(value, expected_type)
        elif variable_types[value] != expected_type:
            actual = variable_types[value]
            # Allow non-nullable → nullable pointer assignment
            if is_nullable_pointer(expected_type) and actual == expected_type.rstrip("?"):
                continue
            # Allow nullable → non-nullable pointer (value may be null-checked first)
            if is_nullable_pointer(actual) and actual.rstrip("?") == expected_type:
                continue
            # Allow integer widening
            if actual in INTEGER_TYPES and expected_type in INTEGER_TYPES:
                actual_w = TYPE_WIDTHS.get(actual, 0)
                expected_w = TYPE_WIDTHS.get(expected_type, 0)
                if actual_w <= expected_w:
                    continue
            raise CompileError(
                f"tipo incompatible: {value} es {variable_types[value]}, "
                f"se esperaba {expected_type}"
            )
    return expected_type


def resolve_field_path(base_name, field_names, variables):
    base_type = variables[base_name]
    if not is_struct_type(base_type):
        raise CompileError(f"{base_name} no es un struct (es {base_type})")
    total_offset = 0
    current_type = base_type
    resolved_names = [base_name]
    for fname in field_names:
        layout = STRUCT_LAYOUTS[current_type]
        field_info = layout["fields"].get(fname)
        if field_info is None:
            raise CompileError(
                f"struct {current_type} no tiene campo {fname}"
            )
        field_offset, field_type = field_info
        total_offset += field_offset
        current_type = field_type
        resolved_names.append(fname)
    return total_offset, current_type


def parse_value_expression(value, variables, functions, expected_type):
    chained = CHAINED_DOT_RE.match(value)
    if chained:
        base_name = chained.group(1)
        if "." in value:
            field_names = FIELD_PATH_RE.findall(value)
            field_names = field_names[1:]
            total_offset, field_type = resolve_field_path(
                base_name, field_names, variables
            )
            if field_type != expected_type:
                path = ".".join([base_name] + field_names)
                raise CompileError(
                    f"campo {path} es {field_type}, "
                    f"se esperaba {expected_type}"
                )
            return (
                "field_access",
                base_name,
                field_names,
                field_type,
                total_offset,
            )
    dot_match = DOT_ACCESS_RE.match(value)
    if dot_match:
        base_name, field_name = dot_match.groups()
        total_offset, field_type = resolve_field_path(
            base_name, [field_name], variables
        )
        if field_type != expected_type:
            raise CompileError(
                f"campo {base_name}.{field_name} es {field_type}, "
                f"se esperaba {expected_type}"
            )
        return ("field_access", base_name, [field_name], field_type, total_offset)
    arr_match = ARRAY_ACCESS_RE.match(value)
    if arr_match:
        base_name, index_text = arr_match.groups()
        if base_name not in variables:
            raise CompileError(f"variable no declarada: {base_name}")
        var_type = variables[base_name]
        inner_type, count = parse_array_type(var_type)
        if inner_type is None:
            raise CompileError(f"{base_name} no es un array (es {var_type})")
        index = parse_operand(index_text, variables)
        if inner_type != expected_type:
            raise CompileError(
                f"elemento de {base_name} es {inner_type}, "
                f"se esperaba {expected_type}"
            )
        elem_width = type_size_and_align(inner_type)[0]
        return ("array_access", base_name, index, inner_type, count, elem_width)
    ptr_match = PTR_OP_RE.match(value)
    if ptr_match:
        op, ptr_type, ptr_name, arg_text = ptr_match.groups()
        if ptr_name not in variables and ptr_name not in STATIC_DATA:
            raise CompileError(f"variable no declarada: {ptr_name}")
        if ptr_name in variables:
            var_type = variables[ptr_name]
            if not is_pointer_type(var_type) and not is_nullable_pointer(var_type):
                raise CompileError(f"{ptr_name} no es un puntero (es {var_type})")
        if op != "ptr_offset" and ptr_type != expected_type:
            raise CompileError(
                f"{op}<{ptr_type}> retorna {ptr_type}, se esperaba {expected_type}"
            )
        arg = parse_operand(arg_text, variables) if arg_text else None
        if arg and arg[0] == "imm":
            validate_immediate(arg[1], "usize")
        return ("ptr_op", op, ptr_name, ptr_type, arg)
    load_match = LOAD_RE.match(value)
    if load_match:
        load_type, resource_name, offset_text = load_match.groups()
        if load_type != expected_type:
            raise CompileError(
                f"cargar<{load_type}> no se puede asignar a {expected_type}"
            )
        return ("load", resource_name, offset_text, load_type)
    atom_match = ATOMIC_EXPR_RE.match(value)
    if atom_match:
        op, atom_type, ptr_name, arg1_text, arg2_text = atom_match.groups()
        if atom_type != expected_type:
            raise CompileError(
                f"{op}<{atom_type}> retorna {atom_type}, se esperaba {expected_type}"
            )
        if ptr_name not in variables:
            raise CompileError(f"variable no declarada: {ptr_name}")
        if variables[ptr_name] != f"ptr<{atom_type}>":
            raise CompileError(
                f"{ptr_name} es {variables[ptr_name]}, se esperaba ptr<{atom_type}>"
            )
        arg1 = parse_operand(arg1_text, variables) if arg1_text else None
        arg2 = parse_operand(arg2_text, variables) if arg2_text else None
        if arg1 and arg1[0] == "imm":
            validate_immediate(arg1[1], atom_type)
        if arg2 and arg2[0] == "imm":
            validate_immediate(arg2[1], atom_type)
        return ("atomic", op, ptr_name, atom_type, arg1, arg2)
    call_match = CALL_RE.match(value)
    if not call_match:
        if is_fn_type(expected_type):
            fn_name = value.strip()
            func = functions.get(fn_name)
            if func and not func.get("external"):
                return ("fn_ref", fn_name)
            if func:
                raise CompileError(
                    f"no se puede obtener referencia a funcion externa: {fn_name}"
                )
        expression = parse_expression(value, variables)
        validate_expression_type(expression, variables, expected_type)
        return expression
    function_name, args_text = call_match.groups()
    function = functions.get(function_name)
    if function is None:
        if function_name in variables and is_fn_type(variables[function_name]):
            fn_params, fn_ret = fn_type_info(variables[function_name])
            if fn_ret != expected_type:
                raise CompileError(
                    f"retorno de {function_name} es {fn_ret}, "
                    f"se esperaba {expected_type}"
                )
            raw_args = [] if not args_text.strip() else smart_split(args_text)
            if len(raw_args) != len(fn_params):
                raise CompileError(
                    f"funcion {function_name}: se esperaban "
                    f"{len(fn_params)} argumentos, se recibieron {len(raw_args)}"
                )
            args = []
            for raw_arg, param_type in zip(raw_args, fn_params):
                operand = parse_operand(raw_arg.strip(), variables)
                if operand[0] == "imm":
                    validate_immediate(operand[1], param_type)
                elif variables.get(operand[1]) != param_type:
                    raise CompileError(
                        f"argumento {operand[1]} es {variables.get(operand[1])}, "
                        f"se esperaba {param_type}"
                    )
                args.append(operand)
            return ("indirect_call", function_name, tuple(args), fn_ret, fn_params)
        raise CompileError(f"funcion no declarada: {function_name}")
    if function["return_type"] != expected_type:
        raise CompileError(
            f"retorno de {function_name} es {function['return_type']}, "
            f"se esperaba {expected_type}"
        )
    raw_args = [] if not args_text.strip() else args_text.split(",")
    if len(raw_args) != len(function["params"]):
        raise CompileError(
            f"funcion {function_name}: se esperaban "
            f"{len(function['params'])} argumentos, se recibieron {len(raw_args)}"
        )
    args = []
    for raw_arg, (_param_name, param_type) in zip(
        raw_args, function["params"]
    ):
        operand = parse_operand(raw_arg.strip(), variables, functions)
        if operand[0] == "imm":
            validate_immediate(operand[1], param_type)
        elif operand[0] == "fn_ref":
            pass
        elif variables[operand[1]] != param_type:
            raise CompileError(
                f"argumento {operand[1]} es {variables[operand[1]]}, "
                f"se esperaba {param_type}"
            )
        args.append(operand)
    return (
        "call",
        function_name,
        tuple(args),
        function["return_type"],
        function.get("external", False),
        function.get("exported", False),
    )


def parse_condition(value, variables):
    match = COND_RE.match(value)
    if not match:
        raise CompileError(f"condicion no soportada: {value.strip()}")
    left, comparator, right = match.groups()
    left_operand = parse_operand(left, variables)
    right_operand = parse_operand(right, variables)
    left_type = (
        variables[left_operand[1]] if left_operand[0] == "var" else None
    )
    right_type = (
        variables[right_operand[1]] if right_operand[0] == "var" else None
    )
    condition_type = left_type or right_type or "i64"
    if left_type and right_type and left_type != right_type:
        raise CompileError(
            f"comparacion entre tipos incompatibles: {left_type} y {right_type}"
        )
    if is_pointer_type(condition_type):
        if comparator not in ("==", "!="):
            raise CompileError(
                "punteros solo admiten comparaciones == y !="
            )
        for operand in (left_operand, right_operand):
            if operand[0] == "imm":
                validate_immediate(operand[1], condition_type)
    else:
        for operand in (left_operand, right_operand):
            if operand[0] == "imm":
                validate_immediate(operand[1], condition_type)
    return (left_operand, comparator, right_operand)


def parse_statements(
    body,
    block_kind,
    variables=None,
    resources=None,
    nested=False,
    loop_counter=None,
    functions=None,
    return_type=None,
):
    variables = {} if variables is None else dict(variables)
    resources = {} if resources is None else dict(resources)
    functions = {} if functions is None else functions
    loop_counter = [0] if loop_counter is None else loop_counter
    patterns = (
        ("klog", KLOG_RE),
        ("resource", RESOURCE_RE),
        ("use", USE_RE),
        ("free", FREE_RE),
        ("store", STORE_RE),
        ("ptr_op", PTR_OP_RE),
        ("array_assign", ARRAY_ASSIGN_RE),
        ("barrier", BARRIER_CALL_RE),
        ("return", RETURN_RE),
        ("typed_var", TYPED_VAR_RE),
        ("var", VAR_RE),
        ("assign", ASSIGN_RE),
        ("field_assign", FIELD_ASSIGN_RE),
    )
    statements = []
    position = 0

    while position < len(body):
        whitespace = re.match(r"[\s;]*", body[position:])
        position += whitespace.end()
        if position >= len(body):
            break
        while_match = WHILE_HEAD_RE.match(body, position)
        if while_match:
            condition = parse_condition(while_match.group(1), variables)
            open_index = while_match.end() - 1
            close_index = find_closing_brace(body, open_index)
            loop_body = body[open_index + 1 : close_index]
            loop_id = loop_counter[0]
            loop_counter[0] += 1
            loop_statements = parse_statements(
                loop_body,
                block_kind,
                variables,
                resources,
                nested=True,
                loop_counter=loop_counter,
                functions=functions,
                return_type=return_type,
            )
            statements.append(("while", loop_id, condition, loop_statements))
            position = close_index + 1
            continue
        if_match = IF_HEAD_RE.match(body, position)
        if if_match:
            condition = parse_condition(if_match.group(1), variables)
            open_index = if_match.end() - 1
            close_index = find_closing_brace(body, open_index)
            then_body = body[open_index + 1 : close_index]
            next_position = close_index + 1
            else_statements = []
            else_match = re.match(r"\s*else\s*\{", body[next_position:])
            if else_match:
                else_open = next_position + else_match.end() - 1
                else_close = find_closing_brace(body, else_open)
                else_body = body[else_open + 1 : else_close]
                else_statements = parse_statements(
                    else_body,
                    block_kind,
                    variables,
                    resources,
                    nested=True,
                    loop_counter=loop_counter,
                    functions=functions,
                    return_type=return_type,
                )
                next_position = else_close + 1
            then_statements = parse_statements(
                then_body,
                block_kind,
                variables,
                resources,
                nested=True,
                loop_counter=loop_counter,
                functions=functions,
                return_type=return_type,
            )
            statements.append(("if", condition, then_statements, else_statements))
            position = next_position
            continue
        matched = False
        for statement_kind, pattern in patterns:
            match = pattern.match(body, position)
            if not match:
                continue
            matched = True
            position = match.end()
            values = match.groups()
            if statement_kind == "klog":
                statements.append(("klog", decode_string(values[0])))
            elif statement_kind == "resource":
                if block_kind != "load":
                    raise CompileError("recurso solo se permite en on load")
                if nested:
                    raise CompileError("recurso dentro de if aun no soportado")
                resource_name, size_text, errno_text = values
                if resource_name in resources or resource_name in variables:
                    raise CompileError(f"recurso duplicado: {resource_name}")
                size = int(size_text)
                if size < 1 or size > 1024 * 1024:
                    raise CompileError(f"tamano kalloc fuera de rango: {size}")
                resources[resource_name] = ("live", size)
                variables[resource_name] = "ptr<u8>"
                statements.append(
                    ("resource", resource_name, size, parse_errno(errno_text))
                )
            elif statement_kind in ("use", "free"):
                if nested:
                    raise CompileError(
                        f"{statement_kind} dentro de if aun no soportado"
                    )
                resource_name = values[0]
                resource = resources.get(resource_name)
                if resource is None:
                    raise CompileError(f"recurso no declarado: {resource_name}")
                if resource[0] != "live":
                    raise CompileError(f"recurso ya liberado: {resource_name}")
                statements.append((statement_kind, resource_name))
                if statement_kind == "free":
                    resources[resource_name] = ("freed", resource[1])
                    variables.pop(resource_name, None)
            elif statement_kind == "store":
                type_name, resource_name, offset_text, value_text = values
                offset = validate_memory_access(
                    type_name,
                    resource_name,
                    offset_text,
                    resources,
                    variables,
                )
                value = parse_operand(value_text, variables)
                if value[0] == "imm":
                    validate_immediate(value[1], type_name)
                elif variables[value[1]] != type_name:
                    raise CompileError(
                        f"guardar<{type_name}> recibio "
                        f"{variables[value[1]]}"
                    )
                statements.append(
                    (
                        "store",
                        resource_name,
                        offset,
                        type_name,
                        value,
                        resources[resource_name][1],
                    )
                )
            elif statement_kind in ("typed_var", "var"):
                if statement_kind == "typed_var":
                    _declaration, variable_name, type_name, expression_text = values
                    if not is_supported_type(type_name):
                        raise CompileError(f"tipo no soportado: {type_name}")
                else:
                    _declaration, variable_name, expression_text = values
                    type_name = "i64"
                if nested:
                    raise CompileError("declaracion var dentro de if aun no soportada")
                if variable_name in variables:
                    raise CompileError(f"variable duplicada: {variable_name}")
                expression = parse_value_expression(
                    expression_text, variables, functions, type_name
                )
                if expression[0] == "load":
                    offset = validate_memory_access(
                        expression[3],
                        expression[1],
                        expression[2],
                        resources,
                        variables,
                    )
                    expression = (
                        expression[0],
                        expression[1],
                        offset,
                        expression[3],
                        resources[expression[1]][1],
                    )
                variables[variable_name] = type_name
                statements.append(("var", variable_name, expression, type_name))
            elif statement_kind == "assign":
                variable_name, expression_text = values
                if variable_name not in variables:
                    raise CompileError(f"variable no declarada: {variable_name}")
                if variable_name in resources:
                    raise CompileError(
                        f"no se puede reasignar el recurso propietario: {variable_name}"
                    )
                statements.append(
                    (
                        "assign",
                        variable_name,
                        parse_value_expression(
                            expression_text,
                            variables,
                            functions,
                            variables[variable_name],
                        ),
                        variables[variable_name],
                    )
                )
                expression = statements[-1][2]
                if expression[0] == "load":
                    offset = validate_memory_access(
                        expression[3],
                        expression[1],
                        expression[2],
                        resources,
                        variables,
                    )
                    replacement = (
                        expression[0],
                        expression[1],
                        offset,
                        expression[3],
                        resources[expression[1]][1],
                    )
                    statement = list(statements[-1])
                    statement[2] = replacement
                    statements[-1] = tuple(statement)
            elif statement_kind == "array_assign":
                base_name, index_text, expression_text = values
                if base_name not in variables:
                    raise CompileError(f"variable no declarada: {base_name}")
                var_type = variables[base_name]
                inner_type, count = parse_array_type(var_type)
                if inner_type is None:
                    raise CompileError(f"{base_name} no es un array (es {var_type})")
                index = parse_operand(index_text, variables)
                if index[0] == "imm":
                    if index[1] < 0 or index[1] >= count:
                        raise CompileError(
                            f"indice {index[1]} fuera de rango para {base_name}[{count}]"
                        )
                elif variables.get(index[1]) != "usize":
                    raise CompileError(
                        f"indice de array debe ser usize, no {variables.get(index[1])}"
                    )
                elem_width = type_size_and_align(inner_type)[0]
                expression = parse_value_expression(
                    expression_text, variables, functions, inner_type
                )
                statements.append(
                    (
                        "store_array",
                        base_name,
                        index,
                        inner_type,
                        count,
                        elem_width,
                        expression,
                    )
                )
            elif statement_kind == "barrier":
                statements.append(("barrier", values[0]))
            elif statement_kind == "ptr_op":
                op, ptr_type, ptr_name, arg_text = values[:4]
                if ptr_name not in variables and ptr_name not in STATIC_DATA:
                    raise CompileError(f"variable no declarada: {ptr_name}")
                if ptr_name in variables and not is_pointer_type(variables[ptr_name]) and not is_nullable_pointer(variables[ptr_name]):
                    raise CompileError(f"{ptr_name} no es un puntero")
                if op != "ptr_store":
                    raise CompileError(f"{op} solo valido en expresion, no como sentencia")
                arg = parse_operand(arg_text, variables) if arg_text else None
                if arg and arg[0] == "imm":
                    validate_immediate(arg[1], ptr_type)
                statements.append(("ptr_store_stmt", ptr_name, ptr_type, arg))
            elif statement_kind == "field_assign":
                base_name, dot_chain, expression_text = values
                if base_name not in variables:
                    raise CompileError(f"variable no declarada: {base_name}")
                field_names = FIELD_PATH_RE.findall(dot_chain) if dot_chain.strip() else []
                if not field_names:
                    raise CompileError(
                        f"asignacion de campo requiere campo: {base_name}"
                    )
                total_offset, field_type = resolve_field_path(
                    base_name, field_names, variables
                )
                expression = parse_value_expression(
                    expression_text, variables, functions, field_type
                )
                statements.append(
                    (
                        "store_field",
                        base_name,
                        field_names,
                        total_offset,
                        field_type,
                        expression,
                    )
                )
            else:
                if block_kind == "function":
                    expression = parse_value_expression(
                        values[0],
                        variables,
                        functions,
                        return_type,
                    )
                    statements.append(("return_expr", expression, return_type))
                elif nested:
                    raise CompileError("return dentro de if aun no soportado")
                else:
                    statements.append(("return", parse_errno(values[0].strip())))
                if body[position:].strip():
                    raise CompileError("sentencias despues de return")
            break
        if not matched:
            excerpt = body[position : position + 40].splitlines()[0]
            raise CompileError(
                f"sentencia no soportada en on {block_kind}: {excerpt!r}"
            )
    return statements


def collect_resources(statements):
    resources = []
    for statement in statements:
        if statement[0] == "resource":
            resources.append(statement[1])
        elif statement[0] == "if":
            resources.extend(collect_resources(statement[2]))
            resources.extend(collect_resources(statement[3]))
        elif statement[0] == "while":
            resources.extend(collect_resources(statement[3]))
    return resources


def collect_variables(statements):
    variables = []
    for statement in statements:
        if statement[0] == "var":
            variables.append(statement[1])
        elif statement[0] == "if":
            variables.extend(collect_variables(statement[2]))
            variables.extend(collect_variables(statement[3]))
        elif statement[0] == "while":
            variables.extend(collect_variables(statement[3]))
    return variables


def collect_messages(statements):
    messages = []
    for statement in statements:
        if statement[0] == "klog":
            messages.append(statement[1])
        elif statement[0] == "if":
            messages.extend(collect_messages(statement[2]))
            messages.extend(collect_messages(statement[3]))
        elif statement[0] == "while":
            messages.extend(collect_messages(statement[3]))
    return messages


def collect_loop_ids(statements):
    loop_ids = []
    for statement in statements:
        if statement[0] == "while":
            loop_ids.append(statement[1])
            loop_ids.extend(collect_loop_ids(statement[3]))
        elif statement[0] == "if":
            loop_ids.extend(collect_loop_ids(statement[2]))
            loop_ids.extend(collect_loop_ids(statement[3]))
    return loop_ids


def has_division(statements):
    for statement in statements:
        if statement[0] in ("var", "assign", "store_field"):
            expression = statement[2] if statement[0] != "store_field" else statement[5]
            if len(expression) == 3 and expression[1] in ("/", "%"):
                return True
        elif statement[0] == "return_expr":
            expression = statement[1]
            if len(expression) == 3 and expression[1] in ("/", "%"):
                return True
        elif statement[0] == "if":
            if has_division(statement[2]) or has_division(statement[3]):
                return True
        elif statement[0] == "while" and has_division(statement[3]):
            return True
    return False


def has_dynamic_memory_access(statements):
    for statement in statements:
        if statement[0] == "store" and statement[2][0] == "var":
            return True
        if statement[0] in ("var", "assign"):
            expression = statement[2]
            if (
                expression[0] == "load"
                and expression[2][0] == "var"
            ):
                return True
        if statement[0] == "if":
            if has_dynamic_memory_access(
                statement[2]
            ) or has_dynamic_memory_access(statement[3]):
                return True
        if statement[0] == "while" and has_dynamic_memory_access(statement[3]):
            return True
    return False


def emit_cleanup(lines, active, slots):
    for resource_name in reversed(active):
        offset = slots[resource_name]
        skip_label = f".Lskip_free_{resource_name}_{len(lines)}"
        lines.extend(
            [
                f"\tmovq {offset}(%rbp), %rdi",
                "\ttestq %rdi, %rdi",
                f"\tje {skip_label}",
                "\tcall kfree",
                f"{skip_label}:",
            ]
        )


def emit_return(lines, active, slots, value, stack_size):
    emit_cleanup(lines, active, slots)
    lines.extend(
        [
            f"\tmovl ${value}, %eax",
            f"\taddq ${stack_size}, %rsp" if stack_size else "",
            "\tpopq %rbp",
            "\tRET",
        ]
    )


def emit_load_operand(lines, operand, slots, register):
    operand_kind, value = operand
    if operand_kind == "imm":
        lines.append(f"\tmovq ${value}, %{register}")
    elif operand_kind == "fn_ref":
        lines.append(f"\tleaq {value}(%rip), %{register}")
    elif operand_kind == "static_ref":
        lines.append(f"\tleaq {value}(%rip), %{register}")
    else:
        lines.append(f"\tmovq {slots[value]}(%rbp), %{register}")


def emit_checked_address(
    lines,
    resource_name,
    offset,
    type_name,
    capacity,
    slots,
    memory_error_label,
):
    lines.append(f"\tmovq {slots[resource_name]}(%rbp), %rcx")
    if offset[0] == "imm":
        return f"{offset[1]}(%rcx)"
    emit_load_operand(lines, offset, slots, "rdx")
    maximum = capacity - TYPE_WIDTHS[type_name]
    lines.extend(
        [
            f"\tcmpq ${maximum}, %rdx",
            f"\tja {memory_error_label}",
        ]
    )
    alignment_mask = TYPE_WIDTHS[type_name] - 1
    if alignment_mask:
        lines.extend(
            [
                f"\ttestq ${alignment_mask}, %rdx",
                f"\tjnz {memory_error_label}",
            ]
        )
    return "(%rcx,%rdx)"


def emit_memory_load(
    lines,
    resource_name,
    offset,
    type_name,
    capacity,
    slots,
    memory_error_label,
):
    address = emit_checked_address(
        lines,
        resource_name,
        offset,
        type_name,
        capacity,
        slots,
        memory_error_label,
    )
    instruction = {
        "u8": "movzbq",
        "bool": "movzbq",
        "i8": "movsbq",
        "u16": "movzwq",
        "i16": "movswq",
        "u32": "movl",
        "i32": "movslq",
        "u64": "movq",
        "i64": "movq",
        "usize": "movq",
        "isize": "movq",
    }[type_name]
    destination = "%eax" if type_name == "u32" else "%rax"
    lines.append(f"\t{instruction} {address}, {destination}")


def emit_memory_store(
    lines,
    resource_name,
    offset,
    type_name,
    value,
    capacity,
    slots,
    memory_error_label,
):
    emit_load_operand(lines, value, slots, "rax")
    address = emit_checked_address(
        lines,
        resource_name,
        offset,
        type_name,
        capacity,
        slots,
        memory_error_label,
    )
    instruction, source = {
        "u8": ("movb", "%al"),
        "i8": ("movb", "%al"),
        "bool": ("movb", "%al"),
        "u16": ("movw", "%ax"),
        "i16": ("movw", "%ax"),
        "u32": ("movl", "%eax"),
        "i32": ("movl", "%eax"),
        "u64": ("movq", "%rax"),
        "i64": ("movq", "%rax"),
        "usize": ("movq", "%rax"),
        "isize": ("movq", "%rax"),
    }[type_name]
    lines.append(f"\t{instruction} {source}, {address}")


def emit_expression(
    lines,
    expression,
    slots,
    arithmetic_error_label,
    memory_error_label=None,
    value_type="i64",
):
    if expression[0] == "load":
        _kind, resource_name, offset, type_name, capacity = expression
        emit_memory_load(
            lines,
            resource_name,
            offset,
            type_name,
            capacity,
            slots,
            memory_error_label,
        )
        return
    if expression[0] == "field_access":
        _kind, base_name, _field_names, field_type, field_offset = expression
        base_slot = slots[base_name]
        instruction = {
            "u8": "movzbq",
            "bool": "movzbq",
            "i8": "movsbq",
            "u16": "movzwq",
            "i16": "movswq",
            "u32": "movl",
            "i32": "movslq",
            "u64": "movq",
            "i64": "movq",
            "usize": "movq",
            "isize": "movq",
        }.get(field_type)
        if instruction is None:
            raise CompileError(
                f"tipo de campo no soportado: {field_type}"
            )
        if field_type in ("u32",):
            lines.append(
                f"\t{instruction} {base_slot + field_offset}(%rbp), %eax"
            )
        else:
            lines.append(
                f"\t{instruction} {base_slot + field_offset}(%rbp), %rax"
            )
        return
    if expression[0] == "array_access":
        _kind, base_name, index, elem_type, _count, elem_width = expression
        base_slot = slots[base_name]
        if index[0] == "imm":
            offset = base_slot + index[1] * elem_width
            instruction = {
                "u8": "movzbq",
                "bool": "movzbq",
                "i8": "movsbq",
                "u16": "movzwq",
                "i16": "movswq",
                "u32": "movl",
                "i32": "movslq",
                "u64": "movq",
                "i64": "movq",
                "usize": "movq",
                "isize": "movq",
            }.get(elem_type, "movq")
            if elem_type in ("u32",):
                lines.append(f"\t{instruction} {offset}(%rbp), %eax")
            else:
                lines.append(f"\t{instruction} {offset}(%rbp), %rax")
        else:
            emit_load_operand(lines, index, slots, "rcx")
            if elem_width not in (1, 2, 4, 8):
                raise CompileError(f"ancho de elemento no soportado: {elem_width}")
            if elem_width > 1:
                lines.append(f"\timulq ${elem_width}, %rcx, %rcx")
            lines.append(f"\tmovq %rbp, %rax")
            lines.append("\taddq %rcx, %rax")
            lines.append(f"\taddq ${base_slot}, %rax")
            lines.extend([
                f"\tmovq %rbp, %rcx",
                f"\taddq ${base_slot + elem_width * _count}, %rcx",
                "\tcmpq %rcx, %rax",
                f"\tjae {memory_error_label}",
                "\tcmpq %rbp, %rax",
                f"\tjb {memory_error_label}",
            ])
            instruction = {
                "u8": "movzbq",
                "bool": "movzbq",
                "i8": "movsbq",
                "u16": "movzwq",
                "i16": "movswq",
                "u32": "movl",
                "i32": "movslq",
                "u64": "movq",
                "i64": "movq",
                "usize": "movq",
                "isize": "movq",
            }.get(elem_type, "movq")
            if elem_type in ("u32",):
                lines.append(f"\t{instruction} (%rax), %eax")
            else:
                lines.append(f"\t{instruction} (%rax), %rax")
        return
    if expression[0] == "call":
        _kind, function_name, arguments, _return_type, external, exported = expression
        for operand, register in zip(arguments, ARG_REGISTERS):
            emit_load_operand(lines, operand, slots, register)
        if external or exported:
            symbol = function_name
        else:
            symbol = f"spasm_fn_{function_name}"
        lines.append(f"\tcall {symbol}")
        return
    if expression[0] == "ptr_op":
        _kind, op, ptr_name, ptr_type, arg = expression
        if ptr_name in STATIC_DATA:
            lines.append(f"\tleaq {ptr_name}(%rip), %rax")
        else:
            lines.append(f"\tmovq {slots[ptr_name]}(%rbp), %rax")
        if op == "ptr_load":
            width = type_size_and_align(ptr_type)[0]
            instr = {1: "movzbq", 2: "movzwq", 4: "movl", 8: "movq"}.get(width, "movq")
            if width == 4:
                lines.append(f"\t{instr} (%rax), %eax")
            else:
                lines.append(f"\t{instr} (%rax), %rax")
        elif op == "ptr_store":
            emit_load_operand(lines, arg, slots, "rcx")
            width = type_size_and_align(ptr_type)[0]
            instr = {1: "movb", 2: "movw", 4: "movl", 8: "movq"}.get(width, "movq")
            reg = {1: "%cl", 2: "%cx", 4: "%ecx", 8: "%rcx"}[width]
            lines.append(f"\t{instr} {reg}, (%rax)")
            lines.append("\tmovq %rcx, %rax")
        elif op == "ptr_offset":
            emit_load_operand(lines, arg, slots, "rcx")
            lines.append("\taddq %rcx, %rax")
        return
    if expression[0] == "atomic":
        _kind, op, ptr_name, atom_type, arg1, arg2 = expression
        width = type_size_and_align(atom_type)[0]
        instr = {1: "b", 2: "w", 4: "l", 8: "q"}.get(width, "q")
        lines.append(f"\tmovq {slots[ptr_name]}(%rbp), %rax")
        if op == "atomic_load":
            lines.append(f"\tmov{instr} (%rax), %eax" if width <= 4 else f"\tmovq (%rax), %rax")
        elif op == "atomic_xchg":
            emit_load_operand(lines, arg1, slots, "rcx")
            lines.append(f"\txchg{instr} %ecx, (%rax)" if width <= 4 else f"\txchgq %rcx, (%rax)")
            lines.append(f"\tmov{instr} %ecx, %eax" if width <= 4 else "\tmovq %rcx, %rax")
        elif op == "atomic_cmpxchg":
            emit_load_operand(lines, arg1, slots, "rdx")
            emit_load_operand(lines, arg2, slots, "rcx")
            lines.append(f"\tlock cmpxchg{instr} %ecx, (%rax)" if width <= 4 else f"\tlock cmpxchgq %rcx, (%rax)")
        elif op == "atomic_add":
            emit_load_operand(lines, arg1, slots, "rcx")
            if width <= 4:
                lines.append(f"\tlock add{instr} %ecx, (%rax)")
                lines.append(f"\tmov{instr} (%rax), %eax")
            else:
                lines.append(f"\tlock addq %rcx, (%rax)")
                lines.append("\tmovq (%rax), %rax")
        elif op == "atomic_sub":
            emit_load_operand(lines, arg1, slots, "rcx")
            if width <= 4:
                lines.append(f"\tlock sub{instr} %ecx, (%rax)")
                lines.append(f"\tmov{instr} (%rax), %eax")
            else:
                lines.append(f"\tlock subq %rcx, (%rax)")
                lines.append("\tmovq (%rax), %rax")
        return
    if expression[0] == "indirect_call":
        _kind, var_name, arguments, _return_type, _fn_params = expression
        for operand, register in zip(arguments, ARG_REGISTERS):
            emit_load_operand(lines, operand, slots, register)
        lines.append(f"\tmovq {slots[var_name]}(%rbp), %rax")
        lines.append("\tcall *%rax")
        return
    if expression[0] == "fn_ref":
        lines.append(f"\tleaq {expression[1]}(%rip), %rax")
        return
    emit_load_operand(lines, expression[0], slots, "rax")
    if len(expression) == 3:
        operator, right = expression[1:]
        emit_load_operand(lines, right, slots, "rcx")
        if operator == "+":
            lines.append("\taddq %rcx, %rax")
        elif operator == "-":
            lines.append("\tsubq %rcx, %rax")
        elif operator == "*":
            lines.append("\timulq %rcx, %rax")
        elif operator == "&":
            lines.append("\tandq %rcx, %rax")
        elif operator == "|":
            lines.append("\torq %rcx, %rax")
        elif operator == "^":
            lines.append("\txorq %rcx, %rax")
        elif operator == "<<":
            lines.append("\tshlq %cl, %rax")
        elif operator == ">>":
            if value_type in ("u8", "u16", "u32", "u64", "usize"):
                lines.append("\tshrq %cl, %rax")
            else:
                lines.append("\tsarq %cl, %rax")
        else:
            lines.extend(
                [
                    "\ttestq %rcx, %rcx",
                    f"\tje {arithmetic_error_label}",
                ]
            )
            if value_type in ("u8", "u16", "u32", "u64", "usize"):
                lines.extend(["\txorl %edx, %edx", "\tdivq %rcx"])
            else:
                lines.extend(["\tcqto", "\tidivq %rcx"])
            if operator == "%":
                lines.append("\tmovq %rdx, %rax")


def inverse_jump(comparator):
    return {
        "==": "jne",
        "!=": "je",
        "<": "jge",
        "<=": "jg",
        ">": "jle",
        ">=": "jl",
    }[comparator]


def emit_native_function(lines, function, builtin=False):
    emit_function(
        lines,
        function["name"]
        if function.get("exported")
        else f"spasm_fn_{function['name']}",
        function["statements"],
        ".text" if builtin else ".spasm",
        params=function["params"],
        global_symbol=function.get("exported", False),
    )


def collect_slot_types(resources, params, statements):
    slot_types = {}
    for resource_name in resources:
        slot_types[resource_name] = "ptr<u8>"
    for param_name, param_type in params:
        slot_types[param_name] = param_type
    variable_types = collect_variables_with_types(statements)
    for var_name, var_type in variable_types.items():
        slot_types[var_name] = var_type
    loop_ids = collect_loop_ids(statements)
    for loop_id in loop_ids:
        slot_types[f"__loop_budget_{loop_id}"] = "i64"
    return slot_types


def collect_variables_with_types(statements):
    result = {}
    for statement in statements:
        if statement[0] == "var":
            result[statement[1]] = statement[3]
        elif statement[0] == "if":
            result.update(collect_variables_with_types(statement[2]))
            result.update(collect_variables_with_types(statement[3]))
        elif statement[0] == "while":
            result.update(collect_variables_with_types(statement[3]))
    return result


def compute_slots(resources, params, statements):
    slot_types = collect_slot_types(resources, params, statements)
    slots = {}
    offset = 0
    sorted_names = sorted(
        slot_types.keys(),
        key=lambda n: (
            0 if n.startswith("__loop_budget_") else
            1 if n in resources else
            2
        ),
    )
    for name in sorted_names:
        type_name = slot_types[name]
        width, align = type_size_and_align(type_name)
        padding = (align - (offset % align)) % align
        offset += padding
        offset += width
        slots[name] = -(offset)
    return slots, offset


def statement_list_terminates(statements):
    """Return True when the final statement cannot fall through."""
    if not statements:
        return False
    statement = statements[-1]
    if statement[0] in ("return", "return_expr"):
        return True
    if statement[0] == "if":
        then_statements = statement[2]
        else_statements = statement[3]
        return (
            bool(else_statements)
            and statement_list_terminates(then_statements)
            and statement_list_terminates(else_statements)
        )
    return False


def emit_function(
    lines, name, statements, prefix, params=(), global_symbol=True
):
    resources = collect_resources(statements)
    loop_ids = collect_loop_ids(statements)
    slots, raw_stack = compute_slots(resources, params, statements)
    stack_size = ((raw_stack + 15) // 16) * 16
    section = ".text" if prefix == ".text" else f"{prefix}.text"
    lines.extend(
        [
            f'.section {section},"ax"',
            ".p2align 4, 0x90",
            f".{'globl' if global_symbol else 'local'} {name}",
            f".type {name}, @function",
            f"{name}:",
            "\tENDBR",
            "\tpushq %rbp",
            "\tmovq %rsp, %rbp",
        ]
    )
    if stack_size:
        lines.append(f"\tsubq ${stack_size}, %rsp")
    slot_types = collect_slot_types(
        resources, params, statements
    )
    for slot_name, slot_offset in slots.items():
        slot_type = slot_types.get(slot_name, "i64")
        if is_struct_type(slot_type):
            layout = STRUCT_LAYOUTS[slot_type]
            pos = slot_offset
            remaining = layout["size"]
            while remaining >= 8:
                lines.append(f"\tmovq $0, {pos}(%rbp)")
                pos += 8
                remaining -= 8
            if remaining >= 4:
                lines.append(f"\tmovl $0, {pos}(%rbp)")
                pos += 4
            if remaining >= 2:
                lines.append(f"\tmovw $0, {pos}(%rbp)")
            if remaining >= 1:
                lines.append(f"\tmovb $0, {pos}(%rbp)")
        else:
            width = type_size_and_align(slot_type)[0]
            if width >= 8:
                lines.append(f"\tmovq $0, {slot_offset}(%rbp)")
            elif width >= 4:
                lines.append(f"\tmovl $0, {slot_offset}(%rbp)")
            elif width >= 2:
                lines.append(f"\tmovw $0, {slot_offset}(%rbp)")
            else:
                lines.append(f"\tmovb $0, {slot_offset}(%rbp)")
    for (param_name, param_type), register, reg32 in zip(params, ARG_REGISTERS, ARG_REGISTERS_32):
        width = type_size_and_align(param_type)[0]
        if width >= 8 or is_pointer_type(param_type) or is_struct_type(param_type):
            lines.append(f"\tmovq %{register}, {slots[param_name]}(%rbp)")
        else:
            if param_type.startswith("i"):
                lines.append(f"\tmovslq %{reg32}, %rax")
            else:
                lines.append(f"\tmovl %{reg32}, %eax")
            if width >= 4:
                lines.append(f"\tmovl %eax, {slots[param_name]}(%rbp)")
            elif width >= 2:
                lines.append(f"\tmovw %ax, {slots[param_name]}(%rbp)")
            else:
                lines.append(f"\tmovb %al, {slots[param_name]}(%rbp)")

    active = []
    message_index = [0]
    returned = False
    arithmetic_error_label = f".L{prefix[1:]}_arithmetic_error"
    loop_error_label = f".L{prefix[1:]}_loop_budget_error"
    memory_error_label = f".L{prefix[1:]}_memory_range_error"

    def emit_statement_list(statement_list):
        nonlocal returned
        for statement in statement_list:
            emit_statement(statement)

    def emit_statement(statement):
        nonlocal returned
        statement_kind = statement[0]
        if statement_kind == "klog":
            lines.extend(
                [
                    f"\tleaq .L{prefix}_message_{message_index[0]}(%rip), %rdi",
                    "\txorl %eax, %eax",
                    "\tcall _printk",
                ]
            )
            message_index[0] += 1
        elif statement_kind == "resource":
            resource_name, size, errno_value = statement[1:]
            offset = slots[resource_name]
            fail_label = f".Lalloc_fail_{resource_name}"
            continue_label = f".Lalloc_ok_{resource_name}"
            lines.extend(
                [
                    f"\tmovl ${size}, %edi",
                    "\tmovl $0xcc0, %esi",
                    "\tcall __kmalloc_noprof",
                    "\ttestq %rax, %rax",
                    f"\tjne {continue_label}",
                    f"{fail_label}:",
                ]
            )
            emit_return(lines, active, slots, errno_value, stack_size)
            lines.extend(
                [
                    f"{continue_label}:",
                    f"\tmovq %rax, {offset}(%rbp)",
                ]
            )
            active.append(resource_name)
        elif statement_kind == "use":
            resource_name = statement[1]
            lines.extend(
                [
                    f"\tmovq {slots[resource_name]}(%rbp), %rax",
                    "\tmovb $0xa5, (%rax)",
                ]
            )
        elif statement_kind == "free":
            resource_name = statement[1]
            lines.extend(
                [
                    f"\tmovq {slots[resource_name]}(%rbp), %rdi",
                    "\tcall kfree",
                    f"\tmovq $0, {slots[resource_name]}(%rbp)",
                ]
            )
            active.remove(resource_name)
        elif statement_kind == "store":
            resource_name, offset, type_name, value, capacity = statement[1:]
            emit_memory_store(
                lines,
                resource_name,
                offset,
                type_name,
                value,
                capacity,
                slots,
                memory_error_label,
            )
        elif statement_kind in ("var", "assign"):
            variable_name, expression, value_type = statement[1:4]
            if is_struct_type(value_type) and len(expression) == 1 and expression[0] == ("imm", 0):
                pass
            else:
                emit_expression(
                    lines,
                    expression,
                    slots,
                    arithmetic_error_label,
                    memory_error_label,
                    value_type,
                )
                width = type_size_and_align(value_type)[0]
                if width >= 8:
                    lines.append(f"\tmovq %rax, {slots[variable_name]}(%rbp)")
                elif width >= 4:
                    lines.append(f"\tmovl %eax, {slots[variable_name]}(%rbp)")
                elif width >= 2:
                    lines.append(f"\tmovw %ax, {slots[variable_name]}(%rbp)")
                else:
                    lines.append(f"\tmovb %al, {slots[variable_name]}(%rbp)")
        elif statement_kind == "store_field":
            base_name, _field_names, field_offset, field_type, expression = statement[1:]
            emit_expression(
                lines,
                expression,
                slots,
                arithmetic_error_label,
                memory_error_label,
                field_type,
            )
            base_slot = slots[base_name]
            store_instr, source_reg = {
                "u8": ("movb", "%al"),
                "i8": ("movb", "%al"),
                "bool": ("movb", "%al"),
                "u16": ("movw", "%ax"),
                "i16": ("movw", "%ax"),
                "u32": ("movl", "%eax"),
                "i32": ("movl", "%eax"),
                "u64": ("movq", "%rax"),
                "i64": ("movq", "%rax"),
                "usize": ("movq", "%rax"),
                "isize": ("movq", "%rax"),
            }.get(field_type, ("movq", "%rax"))
            lines.append(
                f"\t{store_instr} {source_reg}, "
                f"{base_slot + field_offset}(%rbp)"
            )
        elif statement_kind == "store_array":
            base_name, index, elem_type, count, elem_width, expression = statement[1:]
            emit_expression(
                lines,
                expression,
                slots,
                arithmetic_error_label,
                memory_error_label,
                elem_type,
            )
            base_slot = slots[base_name]
            if index[0] == "imm":
                offset = base_slot + index[1] * elem_width
                store_instr, source_reg = {
                    "u8": ("movb", "%al"),
                    "i8": ("movb", "%al"),
                    "bool": ("movb", "%al"),
                    "u16": ("movw", "%ax"),
                    "i16": ("movw", "%ax"),
                    "u32": ("movl", "%eax"),
                    "i32": ("movl", "%eax"),
                    "u64": ("movq", "%rax"),
                    "i64": ("movq", "%rax"),
                    "usize": ("movq", "%rax"),
                    "isize": ("movq", "%rax"),
                }.get(elem_type, ("movq", "%rax"))
                lines.append(
                    f"\t{store_instr} {source_reg}, {offset}(%rbp)"
                )
            else:
                emit_load_operand(lines, index, slots, "rcx")
                if elem_width > 1:
                    lines.append(f"\timulq ${elem_width}, %rcx, %rcx")
                lines.extend([
                    f"\tmovq %rbp, %rdx",
                    "\taddq %rcx, %rdx",
                    f"\taddq ${base_slot}, %rdx",
                    f"\tmovq %rbp, %rcx",
                    f"\taddq ${base_slot + elem_width * count}, %rcx",
                    "\tcmpq %rcx, %rdx",
                    f"\tjae {memory_error_label}",
                    "\tcmpq %rbp, %rdx",
                    f"\tjb {memory_error_label}",
                ])
                store_instr, source_reg = {
                    "u8": ("movb", "%al"),
                    "i8": ("movb", "%al"),
                    "bool": ("movb", "%al"),
                    "u16": ("movw", "%ax"),
                    "i16": ("movw", "%ax"),
                    "u32": ("movl", "%eax"),
                    "i32": ("movl", "%eax"),
                    "u64": ("movq", "%rax"),
                    "i64": ("movq", "%rax"),
                    "usize": ("movq", "%rax"),
                    "isize": ("movq", "%rax"),
                }.get(elem_type, ("movq", "%rax"))
                lines.append(
                    f"\t{store_instr} {source_reg}, (%rdx)"
                )
        elif statement_kind == "barrier":
            barrier_kind = statement[1]
            barrier_insn = {
                "smp_mb": "mfence",
                "smp_rmb": "lfence",
                "smp_wmb": "sfence",
                "barrier": "",
            }.get(barrier_kind)
            if barrier_insn:
                lines.append(f"\t{barrier_insn}")
            else:
                lines.append("\t# compiler barrier")
        elif statement_kind == "ptr_store_stmt":
            ptr_name, ptr_type, arg = statement[1:]
            if ptr_name in STATIC_DATA:
                lines.append(f"\tleaq {ptr_name}(%rip), %rax")
            else:
                lines.append(f"\tmovq {slots[ptr_name]}(%rbp), %rax")
            emit_load_operand(lines, arg, slots, "rcx")
            width = type_size_and_align(ptr_type)[0]
            instr = {1: "movb", 2: "movw", 4: "movl", 8: "movq"}.get(width, "movq")
            reg = {1: "%cl", 2: "%cx", 4: "%ecx", 8: "%rcx"}[width]
            lines.append(f"\t{instr} {reg}, (%rax)")
        elif statement_kind == "if":
            condition, then_statements, else_statements = statement[1:]
            left, comparator, right = condition
            label_number = len(lines)
            else_label = f".Lif_else_{prefix[1:]}_{label_number}"
            end_label = f".Lif_end_{prefix[1:]}_{label_number}"
            emit_load_operand(lines, left, slots, "rax")
            emit_load_operand(lines, right, slots, "rcx")
            lines.extend(
                [
                    "\tcmpq %rcx, %rax",
                    f"\t{inverse_jump(comparator)} {else_label}",
                ]
            )
            emit_statement_list(then_statements)
            if not statement_list_terminates(then_statements):
                lines.append(f"\tjmp {end_label}")
            lines.append(f"{else_label}:")
            emit_statement_list(else_statements)
            lines.append(f"{end_label}:")
        elif statement_kind == "while":
            loop_id, condition, loop_statements = statement[1:]
            budget_slot = slots[f"__loop_budget_{loop_id}"]
            head_label = f".Lwhile_head_{prefix[1:]}_{loop_id}"
            end_label = f".Lwhile_end_{prefix[1:]}_{loop_id}"
            left, comparator, right = condition
            lines.extend(
                [
                    f"\tmovq $100000, {budget_slot}(%rbp)",
                    f"{head_label}:",
                ]
            )
            emit_load_operand(lines, left, slots, "rax")
            emit_load_operand(lines, right, slots, "rcx")
            lines.extend(
                [
                    "\tcmpq %rcx, %rax",
                    f"\t{inverse_jump(comparator)} {end_label}",
                    f"\tsubq $1, {budget_slot}(%rbp)",
                    f"\tjz {loop_error_label}",
                ]
            )
            emit_statement_list(loop_statements)
            lines.extend([f"\tjmp {head_label}", f"{end_label}:"])
        elif statement_kind == "return_expr":
            expression, value_type = statement[1:3]
            emit_expression(
                lines,
                expression,
                slots,
                arithmetic_error_label,
                memory_error_label,
                value_type,
            )
            emit_cleanup(lines, active, slots)
            if stack_size:
                lines.append(f"\taddq ${stack_size}, %rsp")
            lines.extend(["\tpopq %rbp", "\tRET"])
            returned = True
        else:
            emit_return(lines, active, slots, statement[1], stack_size)
            returned = True

    emit_statement_list(statements)
    if not returned:
        emit_return(lines, active, slots, 0, stack_size)
    if has_division(statements):
        lines.append(f"{arithmetic_error_label}:")
        emit_return(lines, resources, slots, -33, stack_size)
    if loop_ids:
        lines.append(f"{loop_error_label}:")
        emit_return(lines, resources, slots, -40, stack_size)
    if has_dynamic_memory_access(statements):
        lines.append(f"{memory_error_label}:")
        emit_return(lines, resources, slots, -34, stack_size)
    lines.extend([f".size {name}, .-{name}", ""])


def emit_assembly(metadata, blocks, functions, kind="module"):
    lines = [
        "/* Generated from SpASM; native Linux kernel x86_64 backend. */",
        "#include <asm/nospec-branch.h>",
        ".code64",
        "",
    ]
    for function in functions:
        emit_native_function(lines, function, builtin=kind == "builtin")
    if STATIC_DATA:
        lines.extend(['.section .rodata,"a"', ""])
        for name, (elem_type, count, values) in STATIC_DATA.items():
            width = type_size_and_align(elem_type)[0]
            directive = {1: ".byte", 2: ".value", 4: ".long", 8: ".quad"}.get(width, ".byte")
            lines.append(f".globl {name}")
            lines.append(f".type {name}, @object")
            lines.append(f".size {name}, {width * count}")
            lines.append(f"{name}:")
            for v in values[:count]:
                lines.append(f"\t{directive} {v}")
            remaining = count - len(values)
            if remaining > 0:
                lines.append(f"\t.zero {remaining * width}")
            lines.append("")
    if kind == "builtin":
        lines.extend(
            [
                '.section .note.GNU-stack,"",@progbits',
                "",
            ]
        )
        return "\n".join(lines)
    emit_function(lines, "spasm_module_init", blocks["load"], ".init")
    lines.extend(
        [
            ".globl init_module",
            ".set init_module, spasm_module_init",
            '.section .init.data,"aw"',
            ".Lspasm_init_addressable:",
            "\t.quad init_module",
            "",
        ]
    )
    emit_function(lines, "spasm_module_exit", blocks["unload"], ".exit")
    lines.extend(
        [
            ".globl cleanup_module",
            ".set cleanup_module, spasm_module_exit",
            '.section .exit.data,"aw"',
            ".Lspasm_exit_addressable:",
            "\t.quad cleanup_module",
            "",
        ]
    )
    lines.extend(['.section .rodata.str1.1,"aMS",@progbits,1'])
    for prefix, statements in ((".init", blocks["load"]), (".exit", blocks["unload"])):
        messages = collect_messages(statements)
        for index, message in enumerate(messages):
            lines.extend(
                [
                    f".L{prefix}_message_{index}:",
                    f'\t.asciz "\\0016spasm: {asm_string(message)}\\n"',
                ]
            )
    lines.extend(["", '.section .modinfo,"a"'])
    for key in ("license", "author", "description"):
        if metadata.get(key):
            lines.append(f'\t.asciz "{key}={asm_string(metadata[key])}"')
    lines.extend(
        [
            f'\t.asciz "name={asm_string(metadata["module"])}"',
            "",
            '.section .note.GNU-stack,"",@progbits',
            "",
        ]
    )
    return "\n".join(lines)


def emit_makefile(module_name):
    return (
        f"obj-m := {module_name}.o\n"
        f"{module_name}-y := {module_name}_native.o\n"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Compila SpASM-kmod nativo a ensamblador x86_64 para Kbuild."
    )
    parser.add_argument("source", type=pathlib.Path)
    parser.add_argument("--out-dir", required=True, type=pathlib.Path)
    parser.add_argument(
        "--kind", choices=("module", "builtin"), default="module"
    )
    args = parser.parse_args()

    try:
        source = args.source.read_text(encoding="utf-8")
        metadata, blocks, functions = parse_source(source, kind=args.kind)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        module_name = (
            metadata["module"] if args.kind == "module" else args.source.stem
        )
        asm_path = args.out_dir / f"{module_name}_native.S"
        asm_path.write_text(
            emit_assembly(metadata, blocks, functions, kind=args.kind),
            encoding="utf-8",
        )
        if args.kind == "module":
            makefile_path = args.out_dir / "Makefile"
            makefile_path.write_text(
                emit_makefile(module_name), encoding="utf-8"
            )
        print(asm_path)
    except (OSError, CompileError) as exc:
        print(f"spasm-kmod-native: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
