# Bitácora de pruebas y resultados

Fecha de corte: 1 de noviembre de 2026. Se separan ejecución observada,
información reportada por el grupo y procedimientos pendientes. No se guardan
direcciones IP, direcciones físicas ni identidades reales de usuarios del sistema.

## 1. Pruebas automatizadas ejecutadas

| Prueba | Comando | Resultado observado | Qué no demuestra |
| --- | --- | --- | --- |
| Python | `python -m pytest tests -q` | **140 aprobadas**, 12,81 s en la ejecución de revisión | Luz, soldadura o voltajes reales |
| Worker local | `npx vitest run` | **23 aprobadas**, una suite | Uso del despliegue público o integración real |
| TypeScript | `npx tsc --noEmit` | Código de salida 0, sin errores | Publicación ni disponibilidad de la URL |

Entorno de revisión: PC Windows, Python 3.12, dependencias del proyecto y runtime
local de Cloudflare para Vitest. Se añadieron cinco pruebas del puerto pigpio a
las 135 de Python que tenía la base. Los GPIO se simulan en esas cinco pruebas.

Una primera ejecución restringida no pudo usar correctamente sockets y carpetas
temporales. Se repitió con acceso al entorno local y pasaron las 140; no fue
necesario alterar aserciones ni marcar pruebas como omitidas para obtenerlo.

Las pruebas cubren CRC y tamaños, tramas externas, ACK, duplicados, directorio,
rutas, cebolla, chat, pánico y gateway. Las del Worker incluyen firmas, replay,
WebSocket, Atom, TTL, borrado al leer, validación de entradas y ausencia de
columnas de registro de IP/User-Agent. Las firmas de prueba son fixtures, no
llaves de producción.

## 2. Desarrollo físico reportado

| Etapa | Resultado reportado | Clasificación |
| --- | --- | --- |
| Prototipo | Indicadores, botón y enlace IR local probados | Reporte y capturas de desarrollo |
| Velocidad local | Tramas estables a 1000 baudios y fallos al superar aproximadamente 1050 | Reporte del grupo, sin tabla formal de BER |
| Haz tapado | Se reportó una prueba local correcta usando material opaco | Desarrollo; no reemplaza pruebas entre placas |
| Placa perforada | Se recibió foto de componentes de una placa soldada | Evidencia visual parcial |
| Paso a dos Faros | Intentos sin confirmación de recepción válida | Integración pendiente |

La velocidad UART es una configuración, no la tasa útil. El resultado local no
se extrapola a otra distancia, otra placa o luz ambiental distinta.

## 3. Diagnóstico observado por SSH

Se controlaron ambas Raspberry a través de SSH, sin modificar el código del
proyecto instalado. Se alternaron los emisores por GPIO17 y se leyó GPIO27.

| Comprobación | Resultado observado |
| --- | --- |
| TX en A y B | pigpio generó una secuencia UART de 14 bytes a 300 baudios en unos 0,48 s |
| Recepción B sin pull interno | Datos repetitivos e inestables que no siguieron claramente al emisor |
| Recepción A | Sin datos ni transiciones durante la secuencia de B |
| Repetición con pull-up interno | Cero bytes y cero transiciones útiles en ambos sentidos |
| Alineación repetida A hacia B | B permaneció en 1 al apagar y encender A con pull-up; sin él fluctuó |

Estos resultados no verifican que el LED emita correctamente solo porque exista
una onda GPIO. Tampoco identifican de forma concluyente una conexión rota.
Se requiere revisar el camino óptico y medir RX, pull-up, alimentación y GND.
El estado del enlace físico no se sustituye por la suposición «todo funciona».

## 4. Protocolo de medición formal, pendiente

El enunciado exige tasa efectiva y BER a tres distancias bajo luz ambiental
normal. No obliga a que una de ellas sea un metro salvo para el extra. Se
proponen **1 cm, 2 cm y 5 cm**, manteniendo alimentación y resistencias iguales.
Cambiar esas distancias si el montaje requiere otras, y registrar las usadas.

Usar 100 tramas para BER y 20 para tasa con ACK por distancia y sentido. Registrar
el tiempo real, baudios, tipo de iluminación, hora y cualquier pérdida. Los
comandos completos están en el manual. No se llena la tabla con valores teóricos.

| Distancia | Sentido | Tramas recibidas/enviadas | Bits distintos/totales | BER | Tasa útil B/s |
| --- | --- | --- | --- | --- | --- |
| 1 cm | A hacia B | Pendiente | Pendiente | Pendiente | Pendiente |
| 1 cm | B hacia A | Pendiente | Pendiente | Pendiente | Pendiente |
| 2 cm | A hacia B | Pendiente | Pendiente | Pendiente | Pendiente |
| 2 cm | B hacia A | Pendiente | Pendiente | Pendiente | Pendiente |
| 5 cm | A hacia B | Pendiente | Pendiente | Pendiente | Pendiente |
| 5 cm | B hacia A | Pendiente | Pendiente | Pendiente | Pendiente |

Condiciones por sesión: fecha y hora, luz ambiental, instrumento de distancia,
baudios, R4 final, número de tramas, alineación y responsable: **pendientes**.

BER = bits distintos / bits totales comparados. El programa reconstruye el
contenido esperado por semilla y SEQ y contabiliza las tramas perdidas como todos
sus bits erróneos. Es una estimación conservadora basada en tramas, no una medida
de cada bit físico 8N1 ni una separación estadística de pérdida y error de bit.
La tasa útil es payload confirmado dividido por segundos de la prueba, incluyendo
confirmaciones y reintentos.

Una trama máxima produce 267 bytes UART incluyendo relleno pigpio. A 300 baudios
su tiempo de transmisión teórico es 267 x 10 / 300 = **8,9 s**; no es una medición
de rendimiento. Una tasa teórica tampoco se copia en la columna de tasa útil.

## 5. Casos de aceptación de la integración

| Caso | Resultado esperado | Estado físico/integrado |
| --- | --- | --- |
| Texto A-B y B-A | Texto completo visible en receptor | Pendiente |
| ACK dirigido | Emisor informa entrega confirmada | Pendiente |
| Dos comunidades solo por Faro | Mensaje cruza luz; al bloquearla falla el camino | Pendiente |
| Tres relays | Ruta con candidatos suficientes y sin modo directo | Probado en software; pendiente por luz |
| Privado/tema | Solo destinatario o miembros descifran | Pruebas software; pendiente defensa |
| Pánico físico | Borrado lógico, renovación y señal visual | Pruebas software; pendiente botón sobre sistema integrado |
| Mensaje público al Worker | Sala y feed reciben solo público | **No utilizado por el grupo** |
| Buzón muerto | Blob fijo, primera lectura y borrado | Probado localmente en suite; uso integrado no realizado |

## 6. Incidencias y tratamiento

| Incidencia | Tratamiento aplicado o pendiente |
| --- | --- |
| Archivo no encontrado | Ejecutar módulos desde la raíz de su repositorio |
| GPIO ya en uso | Detener otro lector y liberar puerto antes de abrirlo |
| Polaridad distinta del receptor original | Invertir RX en el puerto pigpio |
| Scripts de prueba con GPIO14/15 | Retirar `tools/emisor.py` y `tools/receptor.py` |
| Mensaje «enviado» sin texto al otro lado | Comprobar recepción; difusión no confirma |
| Lectura depende del pull interno | Medir acondicionamiento y revisar conexión, sin inferir una causa única |
| Varias tramas sin separar | Usar pausa de un segundo a 300 baudios en BER |
| Bitácora incompleta al final | Reconstrucción señalada como estimada; registrar a futuro al trabajar |
