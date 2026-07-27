# Nice Kernel

**Filosofía:** *Machine and User Care.*

Nice Kernel es el nombre de trabajo del proyecto. Su objetivo es construir un
sistema que cuide tanto la máquina —estabilidad, recursos, diagnóstico y
comportamiento predecible— como a la persona —control, claridad, seguridad y
una experiencia comprensible—.

SpASM es el lenguaje y la cadena de compilación propios usados por el proyecto.
En esta etapa el nombre SpASM no se presenta como marca registrada; cualquier
registro, licencia o identidad comercial se decidirá por separado antes de una
publicación formal.

Este repositorio es el proyecto canónico para portar Linux x86_64 a SpASM.
Todo cambio del proyecto debe realizarse aquí:

```text
/home/martin/Disco3/kernelLinux/linux-6.19.14
```

No se modifican los proyectos FFmpeg/SpASM durante el trabajo del kernel. El
compilador SpASM se consume como una dependencia externa y, salvo que se
indique otra ruta, se toma de:

```text
/home/martin/Documentos/SpASM/tools/spasmc.py
```

## Comando único

```sh
tools/spasm-kernel/project COMMAND
```

Comandos:

- `status`: muestra versión, rama, artefactos y compilador.
- `config`: genera la configuración base x86_64.
- `build`: compila el kernel y sus módulos.
- `module`: compila el primer módulo nativo `.spasm` a `.ko` mediante Kbuild.
- `initramfs`: construye el initramfs configurable.
- `test`: arranca el kernel con el initramfs en QEMU.
- `spasm-info`: muestra la interfaz del compilador propio.

Verificación reproducible del primer hito Ring 0:

```sh
tools/nice-kernel/verify-poc
```

La procedencia, versiones, hashes y criterio de aprobación están registrados
en `NICE-KERNEL-PROVENANCE.md`.

El backend nativo se consume mediante el contrato estable
`nice-kernel-x86_64`, documentado en
`docs/nice-kernel/spasm-target-v1.md`. Sus pruebas rápidas se ejecutan con:

```sh
tools/testing/selftests/nice-kernel/run_backend_tests
```

El comando `project module` registra el target con `SPASMC_TARGET_PATH` y llama
al dispatcher propio `/home/martin/Documentos/SpASM/tools/spasmc.py`. No existe
una ruta alternativa que genere C.

El directorio de construcción predeterminado es:

```text
/home/martin/Disco3/kernelLinux/build-x86_64-baseline
```

Puede cambiarse sin editar archivos:

```sh
KERNEL_BUILD=/otra/ruta tools/spasm-kernel/project build
```

También puede seleccionarse otro compilador:

```sh
SPASMC=/ruta/tools/spasmc.py tools/spasm-kernel/project spasm-info
```

## Parámetros de QEMU/initramfs

El comando `test` acepta estas variables:

```sh
SPASM_MODE=test
SPASM_MESSAGE=Nice_Kernel_Machine_and_User_Care
SPASM_HOSTNAME=nice-kernel
SPASM_DELAY=0
SPASM_DEBUG=0
```

Ejemplo de consola interactiva:

```sh
SPASM_MODE=shell SPASM_DEBUG=1 tools/spasm-kernel/project test
```

## Regla de trabajo

La línea base C y los futuros objetos SpASM se construyen con el mismo Kbuild.
Los artefactos generados permanecen fuera del árbol fuente. Cada migración debe
mantener el arranque QEMU y la prueba del initramfs antes de integrarse.

## Principios del proyecto

- **Cuidado de la máquina:** no degradar estabilidad, memoria, aislamiento ni
  capacidad de diagnóstico durante una migración.
- **Cuidado de la persona:** errores explícitos, configuración visible y
  comportamiento seguro de forma predeterminada.
- **Compatibilidad:** Linux y sus herramientas deben consumir los artefactos
  normalmente, aunque su implementación nativa provenga de SpASM.
- **Migración verificable:** reemplazar componentes por módulos pequeños,
  reversibles y probados en x86_64.
- **Identidad honesta:** distinguir el kernel Linux de base, Nice Kernel como
  proyecto y SpASM como lenguaje y compilador.

El primer backend nativo admite el subconjunto de módulos con metadatos,
`on load`, `on unload`, `klog` y `return`. Genera ensamblador x86_64 y un objeto
ELF relocatable; no genera ni compila código C.

También admite recursos de memoria con comprobación estática:

```text
recurso buffer = kalloc<u8>(256) else return -ENOMEM
usar buffer
liberar buffer
```

El backend:

- rechaza recursos duplicados, no declarados, usados después de liberar o
  liberados dos veces;
- limita cada reserva a 1 MiB;
- usa `GFP_KERNEL` para la línea base Linux 6.19.14;
- comprueba el resultado de `__kmalloc_noprof`;
- libera recursos vivos en orden inverso antes de cualquier retorno;
- genera llamadas relocatables a `__kmalloc_noprof` y `kfree`.

## Variables y control de flujo nativo

El backend acepta variables enteras locales con la sintaxis normal de SpASM:

```text
var estado = 40;
estado = estado + 2;

if (estado == 42) {
	klog("rama correcta")
} else {
	klog("rama incorrecta")
}

var iteracion = 0;
var potencia = 1;
while (iteracion < 5) {
	potencia = potencia * 2;
	iteracion = iteracion + 1;
}

var cociente = 84 / 2;
var resto = 85 % 2;
```

Soporte actual:

- declaraciones `var` y `let`;
- asignación de enteros;
- expresiones enteras con `+`, `-`, `*`, `/` y `%`;
- operandos inmediatos o variables;
- comparadores `==`, `!=`, `<`, `<=`, `>` y `>=`;
- bloques `if/else`, incluidos condicionales anidados;
- bucles `while`;
- variables almacenadas en la pila, sin estado global oculto.

El compilador rechaza variables no declaradas, duplicadas o utilizadas en una
expresión no soportada. La división o módulo por cero retorna `-EDOM`, y cada
bucle tiene un presupuesto de 100000 iteraciones: si se agota, retorna
`-ELOOP`. Ambos caminos de error liberan primero todos los recursos vivos.
Las declaraciones, recursos y retornos dentro de una rama todavía están fuera
de este primer subconjunto.

## Funciones y tipos enteros

El target `nice-kernel-x86_64` admite funciones internas puras con hasta seis
argumentos y retorno entero:

```text
fn sumar(a: i64, b: i64) -> i64 {
	return a + b;
}

var resultado: i64 = sumar(40, 2);
```

Tipos v1:

```text
u8 i8 u16 i16 u32 i32 u64 i64 usize isize bool
```

Las firmas, cantidad de argumentos, compatibilidad exacta de tipos y constantes
fuera de rango se rechazan durante la compilación. Los argumentos siguen la ABI
System V x86_64 en registros y el resultado se devuelve en `rax`. En esta fase
las funciones son puras, contienen exactamente un `return`, no llaman la API
Linux y realizan la aritmética en registros de 64 bits; el truncado y la
comprobación de overflow para tipos menores quedan para la siguiente revisión
del sistema de tipos.

## Punteros tipados

La primera base de punteros distingue nulabilidad y propiedad:

```text
fn conservar(p: ptr<u8>) -> ptr<u8> {
	return p;
}

recurso buffer = kalloc<u8>(256) else return -ENOMEM
var alias: ptr<u8> = conservar(buffer);
var opcional: ptr<u8>? = 0;
liberar buffer
```

- `ptr<T>` nunca acepta `0`;
- `ptr<T>?` puede contener `0`;
- no existen conversiones implícitas entre enteros y direcciones;
- `ptr<u8>` y `ptr<u16>` son tipos incompatibles;
- no se permite aritmética ni comparación de orden entre punteros;
- solamente el nombre declarado con `recurso` posee la reserva y puede
  liberarla o reasignar su estado;
- un alias no transfiere propiedad.

SP-005 todavía no habilita desreferencia general. El acceso actual permanece
limitado a operaciones controladas por el backend; tamaños, alineación y
préstamos deberán modelarse antes de exponer lectura o escritura arbitraria.

## Acceso comprobado a memoria

Las reservas con capacidad conocida admiten accesos tipados con offset
constante:

```text
recurso buffer = kalloc<u8>(256) else return -ENOMEM
guardar<u32>(buffer, 4, 424242);
var lectura: u32 = cargar<u32>(buffer, 4);
```

Antes de generar una instrucción de memoria, el compilador comprueba:

- que el recurso existe y continúa vivo;
- que el tipo es entero y tiene un ancho conocido;
- que el offset respeta la alineación natural del tipo;
- que `offset + sizeof(T)` no excede la capacidad;
- que el valor almacenado tiene exactamente el tipo solicitado.

El backend selecciona cargas con extensión de signo o cero según `i8/u8`,
`i16/u16` e `i32/u32`; los tipos de 64 bits se transfieren completos. Los
accesos mediante alias permanecen deshabilitados; el recurso propietario
conserva la capacidad necesaria para comprobar cada operación.

Los algoritmos también pueden utilizar un offset variable de tipo `usize`:

```text
var indice: usize = 8;
guardar<u16>(buffer, indice, 1234);
var lectura: u16 = cargar<u16>(buffer, indice);
```

Para un offset dinámico, el backend emite antes de cada acceso:

- comparación sin signo contra `capacidad - sizeof(T)`;
- comprobación de la máscara de alineación;
- salto a una ruta común de error si alguna condición falla.

La ruta de error retorna `-ERANGE` y libera en orden inverso todos los recursos
que continúen vivos. Un índice dinámico de cualquier tipo distinto de `usize`
es rechazado. Los accesos mediante alias todavía permanecen deshabilitados.
