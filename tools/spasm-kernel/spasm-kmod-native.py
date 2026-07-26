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
RETURN_RE = re.compile(r"return\s+(-?[0-9]+)")
RESOURCE_RE = re.compile(
    r"recurso\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
    r"kalloc<u8>\(\s*([0-9]+)\s*\)\s+else\s+return\s+(-?[A-Za-z0-9_]+)"
)
USE_RE = re.compile(r"usar\s+([A-Za-z_][A-Za-z0-9_]*)")
FREE_RE = re.compile(r"liberar\s+([A-Za-z_][A-Za-z0-9_]*)")
STORE_RE = re.compile(
    r"guardar<([A-Za-z_][A-Za-z0-9_]*)>\(\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([0-9]+)\s*,\s*"
    r"(-?[0-9]+|[A-Za-z_][A-Za-z0-9_]*)\s*\)\s*;?"
)
VAR_RE = re.compile(
    r"(var|let)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^;{}]+)\s*;"
)
TYPED_VAR_RE = re.compile(
    r"(var|let)\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*"
    r"([A-Za-z_][A-Za-z0-9_]*(?:<[A-Za-z_][A-Za-z0-9_]*>)?\??)"
    r"\s*=\s*([^;{}]+)\s*;"
)
ASSIGN_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^;{}]+)\s*;")
IF_HEAD_RE = re.compile(r"if\s*\(([^()]*)\)\s*\{")
WHILE_HEAD_RE = re.compile(r"while\s*\(([^()]*)\)\s*\{")
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
ERRNOS = {"ENOMEM": -12}
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
EXPR_RE = re.compile(
    r"^\s*(-?[0-9]+|[A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s*([+\-*/%])\s*(-?[0-9]+|[A-Za-z_][A-Za-z0-9_]*))?\s*$"
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
    r"\bfn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^()]*)\)\s*"
    r"->\s*([A-Za-z_][A-Za-z0-9_]*(?:<[A-Za-z_][A-Za-z0-9_]*>)?\??)"
    r"\s*\{"
)
PARAM_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*"
    r"([A-Za-z_][A-Za-z0-9_]*(?:<[A-Za-z_][A-Za-z0-9_]*>)?\??)\s*$"
)
POINTER_TYPE_RE = re.compile(
    r"^ptr<([A-Za-z_][A-Za-z0-9_]*)>(\?)?$"
)
LOAD_RE = re.compile(
    r"^\s*cargar<([A-Za-z_][A-Za-z0-9_]*)>\(\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([0-9]+)\s*\)\s*$"
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


def parse_source(source):
    metadata = {}
    block_texts, source_without_blocks = extract_on_blocks(source)
    functions, source_without_blocks = extract_functions(source_without_blocks)
    function_signatures = {
        function["name"]: function for function in functions
    }

    for line_number, line in enumerate(source_without_blocks.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith(("#", "//")):
            continue
        match = HEADER_RE.match(line)
        if not match:
            raise CompileError(f"linea {line_number}: declaracion no soportada")
        key, value = match.groups()
        if key in metadata:
            raise CompileError(f"linea {line_number}: {key} duplicado")
        metadata[key] = decode_string(value)

    for required in ("module", "license"):
        if not metadata.get(required):
            raise CompileError(f"falta declaracion {required}")
    if not NAME_RE.match(metadata["module"]):
        raise CompileError("nombre de modulo invalido")

    blocks = {}
    for kind, body in block_texts:
        if kind in blocks:
            raise CompileError(f"bloque on {kind} duplicado")
        blocks[kind] = parse_statements(
            body, kind, functions=function_signatures
        )

    if "load" not in blocks or "unload" not in blocks:
        raise CompileError("se requieren bloques on load y on unload")
    return metadata, blocks, functions


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
        name, params_text, return_type = match.groups()
        if name in names:
            raise CompileError(f"funcion duplicada: {name}")
        if not is_supported_type(return_type):
            raise CompileError(f"tipo de retorno no soportado: {return_type}")
        params = []
        param_names = set()
        if params_text.strip():
            for raw_param in params_text.split(","):
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
        return_match = re.fullmatch(
            r"\s*return\s+([^;{}]+)\s*;?\s*", body
        )
        if not return_match:
            raise CompileError(
                f"funcion {name}: v1 requiere exactamente un return"
            )
        variable_types = dict(params)
        expression = parse_expression(return_match.group(1), variable_types)
        validate_expression_type(expression, variable_types, return_type)
        functions.append(
            {
                "name": name,
                "params": params,
                "return_type": return_type,
                "expression": expression,
            }
        )
        names.add(name)
        spans.append((match.start(), close_index + 1))
        position = close_index + 1
    remaining = list(source)
    for start, end in spans:
        remaining[start:end] = " " * (end - start)
    return functions, "".join(remaining)


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
    if type_name in INTEGER_TYPES:
        return True
    match = pointer_type(type_name)
    return bool(match and match.group(1) in INTEGER_TYPES)


def is_pointer_type(type_name):
    return pointer_type(type_name) is not None


def is_nullable_pointer(type_name):
    match = pointer_type(type_name)
    return bool(match and match.group(2))


def validate_memory_access(type_name, resource_name, offset, resources):
    if type_name not in TYPE_WIDTHS:
        raise CompileError(f"tipo de acceso a memoria no soportado: {type_name}")
    resource = resources.get(resource_name)
    if resource is None:
        raise CompileError(f"recurso no declarado: {resource_name}")
    state, capacity = resource
    if state != "live":
        raise CompileError(f"recurso ya liberado: {resource_name}")
    width = TYPE_WIDTHS[type_name]
    if offset % width:
        raise CompileError(
            f"acceso {type_name} desalineado en offset {offset}"
        )
    if offset + width > capacity:
        raise CompileError(
            f"acceso fuera de rango: {resource_name}[{offset}:{offset + width}] "
            f"excede {capacity} bytes"
        )


def parse_operand(value, variables):
    value = value.strip()
    if value.lstrip("-").isdigit():
        return ("imm", int(value))
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
    for operand in expression[::2]:
        kind, value = operand
        if kind == "imm":
            validate_immediate(value, expected_type)
        elif variable_types[value] != expected_type:
            raise CompileError(
                f"tipo incompatible: {value} es {variable_types[value]}, "
                f"se esperaba {expected_type}"
            )
    return expected_type


def parse_value_expression(value, variables, functions, expected_type):
    load_match = LOAD_RE.match(value)
    if load_match:
        load_type, resource_name, offset_text = load_match.groups()
        if load_type != expected_type:
            raise CompileError(
                f"cargar<{load_type}> no se puede asignar a {expected_type}"
            )
        return ("load", resource_name, int(offset_text), load_type)
    call_match = CALL_RE.match(value)
    if not call_match:
        expression = parse_expression(value, variables)
        validate_expression_type(expression, variables, expected_type)
        return expression
    function_name, args_text = call_match.groups()
    function = functions.get(function_name)
    if function is None:
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
        operand = parse_operand(raw_arg.strip(), variables)
        if operand[0] == "imm":
            validate_immediate(operand[1], param_type)
        elif variables[operand[1]] != param_type:
            raise CompileError(
                f"argumento {operand[1]} es {variables[operand[1]]}, "
                f"se esperaba {param_type}"
            )
        args.append(operand)
    return ("call", function_name, tuple(args), function["return_type"])


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
        ("return", RETURN_RE),
        ("typed_var", TYPED_VAR_RE),
        ("var", VAR_RE),
        ("assign", ASSIGN_RE),
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
                validate_memory_access(
                    type_name, resource_name, int(offset_text), resources
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
                    ("store", resource_name, int(offset_text), type_name, value)
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
                    validate_memory_access(
                        expression[3], expression[1], expression[2], resources
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
                    validate_memory_access(
                        expression[3], expression[1], expression[2], resources
                    )
            else:
                if nested:
                    raise CompileError("return dentro de if aun no soportado")
                statements.append(("return", int(values[0])))
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
        if statement[0] in ("var", "assign"):
            expression = statement[2]
            if len(expression) == 3 and expression[1] in ("/", "%"):
                return True
        elif statement[0] == "if":
            if has_division(statement[2]) or has_division(statement[3]):
                return True
        elif statement[0] == "while" and has_division(statement[3]):
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
    else:
        lines.append(f"\tmovq {slots[value]}(%rbp), %{register}")


def emit_memory_load(lines, resource_name, offset, type_name, slots):
    lines.append(f"\tmovq {slots[resource_name]}(%rbp), %rcx")
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
    lines.append(f"\t{instruction} {offset}(%rcx), {destination}")


def emit_memory_store(lines, resource_name, offset, type_name, value, slots):
    emit_load_operand(lines, value, slots, "rax")
    lines.append(f"\tmovq {slots[resource_name]}(%rbp), %rcx")
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
    lines.append(f"\t{instruction} {source}, {offset}(%rcx)")


def emit_expression(lines, expression, slots, arithmetic_error_label):
    if expression[0] == "load":
        _kind, resource_name, offset, type_name = expression
        emit_memory_load(lines, resource_name, offset, type_name, slots)
        return
    if expression[0] == "call":
        _kind, function_name, arguments, _return_type = expression
        for operand, register in zip(arguments, ARG_REGISTERS):
            emit_load_operand(lines, operand, slots, register)
        lines.append(f"\tcall spasm_fn_{function_name}")
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
        else:
            lines.extend(
                [
                    "\ttestq %rcx, %rcx",
                    f"\tje {arithmetic_error_label}",
                    "\tcqto",
                    "\tidivq %rcx",
                ]
            )
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


def emit_native_function(lines, function):
    name = function["name"]
    params = function["params"]
    expression = function["expression"]
    slots = {
        param_name: -8 * (index + 1)
        for index, (param_name, _param_type) in enumerate(params)
    }
    stack_size = ((len(slots) * 8 + 15) // 16) * 16
    arithmetic_error_label = f".Lspasm_fn_{name}_arithmetic_error"
    lines.extend(
        [
            '.section .text.spasm,"ax"',
            f".type spasm_fn_{name}, @function",
            f"spasm_fn_{name}:",
            "\tpushq %rbp",
            "\tmovq %rsp, %rbp",
        ]
    )
    if stack_size:
        lines.append(f"\tsubq ${stack_size}, %rsp")
    for (param_name, _param_type), register in zip(params, ARG_REGISTERS):
        lines.append(f"\tmovq %{register}, {slots[param_name]}(%rbp)")
    emit_expression(lines, expression, slots, arithmetic_error_label)
    if stack_size:
        lines.append(f"\taddq ${stack_size}, %rsp")
    lines.extend(["\tpopq %rbp", "\tRET"])
    if len(expression) == 3 and expression[1] in ("/", "%"):
        lines.extend(
            [
                f"{arithmetic_error_label}:",
                "\tmovq $-33, %rax",
                f"\taddq ${stack_size}, %rsp" if stack_size else "",
                "\tpopq %rbp",
                "\tRET",
            ]
        )
    lines.extend([f".size spasm_fn_{name}, .-spasm_fn_{name}", ""])


def emit_function(lines, name, statements, prefix):
    resources = collect_resources(statements)
    variables = collect_variables(statements)
    loop_ids = collect_loop_ids(statements)
    loop_slots = [f"__loop_budget_{loop_id}" for loop_id in loop_ids]
    slot_names = resources + variables + loop_slots
    if len(slot_names) != len(set(slot_names)):
        raise CompileError("colision de nombres entre variables o recursos")
    slots = {
        slot_name: -8 * (index + 1) for index, slot_name in enumerate(slot_names)
    }
    stack_size = ((len(slot_names) * 8 + 15) // 16) * 16
    lines.extend(
        [
            f'.section {prefix}.text,"ax"',
            f".globl {name}",
            f".type {name}, @function",
            f"{name}:",
            "\tpushq %rbp",
            "\tmovq %rsp, %rbp",
        ]
    )
    if stack_size:
        lines.append(f"\tsubq ${stack_size}, %rsp")
    for offset in slots.values():
        lines.append(f"\tmovq $0, {offset}(%rbp)")

    active = []
    message_index = [0]
    returned = False
    arithmetic_error_label = f".L{prefix[1:]}_arithmetic_error"
    loop_error_label = f".L{prefix[1:]}_loop_budget_error"

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
            resource_name, offset, type_name, value = statement[1:]
            emit_memory_store(
                lines, resource_name, offset, type_name, value, slots
            )
        elif statement_kind in ("var", "assign"):
            variable_name, expression = statement[1:3]
            emit_expression(lines, expression, slots, arithmetic_error_label)
            lines.append(f"\tmovq %rax, {slots[variable_name]}(%rbp)")
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
            lines.extend([f"\tjmp {end_label}", f"{else_label}:"])
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
    lines.extend([f".size {name}, .-{name}", ""])


def emit_assembly(metadata, blocks, functions):
    lines = [
        "/* Generated from SpASM; native Linux kernel x86_64 backend. */",
        "#include <asm/nospec-branch.h>",
        ".code64",
        "",
    ]
    for function in functions:
        emit_native_function(lines, function)
    emit_function(lines, "init_module", blocks["load"], ".init")
    emit_function(lines, "cleanup_module", blocks["unload"], ".exit")
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
    args = parser.parse_args()

    try:
        source = args.source.read_text(encoding="utf-8")
        metadata, blocks, functions = parse_source(source)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        module_name = metadata["module"]
        asm_path = args.out_dir / f"{module_name}_native.S"
        makefile_path = args.out_dir / "Makefile"
        asm_path.write_text(
            emit_assembly(metadata, blocks, functions), encoding="utf-8"
        )
        makefile_path.write_text(emit_makefile(module_name), encoding="utf-8")
        print(asm_path)
    except (OSError, CompileError) as exc:
        print(f"spasm-kmod-native: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
