# Machine Care Kernel v1

## Estado real

Los builtins `care_*` del runtime SpASM observan correctamente la máquina, pero
su estado y sus tickets pertenecen a cada proceso. No constituyen todavía una
política global del kernel.

El primer componente compartido es `spasm_care_level_v1`: un motor de decisión
SpASM puro, determinista y sin acceso directo al hardware. Recibe:

- uso de CPU, de 0 a 100;
- temperatura de CPU en grados Celsius;
- memoria libre en MiB.

Devuelve uno de los niveles ABI estables:

| Valor | Nivel |
|---:|---|
| 0 | GREEN |
| 1 | YELLOW |
| 2 | ORANGE |
| 3 | RED |
| 4 | EMERGENCY |

Separar adquisición y decisión permite probar la política exhaustivamente. Un
agente global de espacio de usuario y, posteriormente, un consumidor dentro del
kernel podrán invocar exactamente la misma implementación SpASM.

## Agente global observacional

`tools/spasm-care-agent/spasm-care-agent` es el primer consumidor global. El
puente obtiene señales de `/proc` y `sysfs`, invoca
`spasm_care_level_v1` desde una biblioteca nativa generada por el compilador
SpASM y publica `/run/spasm-care/status.json` mediante reemplazo atómico.

El campo `policy_language` permite comprobar que la decisión proviene de SpASM.
El modo inicial es deliberadamente `observe`: informa, pero no cambia
prioridades, frecuencia, scheduler ni cgroups. Su unidad systemd bloquea la
escritura sobre el kernel, módulos y control groups.

Ejemplo de contrato:

```json
{
  "schema": "spasm-care-status-v1",
  "policy": "spasm_care_level_v1",
  "policy_language": "SpASM",
  "mode": "observe",
  "level": 0,
  "level_name": "GREEN"
}
```

## Límites v1

- `>= 95 °C` o `< 64 MiB`: EMERGENCY.
- `>= 85 °C`, `< 128 MiB`, o CPU `>= 85 %` junto con `>= 75 °C`: RED.
- `>= 75 °C` o `< 256 MiB`: ORANGE.
- CPU `>= 85 %`: YELLOW.
- En otro caso: GREEN.

## Próximos contratos

1. Centralizar tickets y presupuestos entre procesos.
2. Aplicar límites reversibles mediante cgroup v2.
3. Exponer telemetría de solo lectura al kernel y al usuario.
4. Evaluar integración con scheduler/cpufreq únicamente después de validar el
   agente global sin regresiones.
