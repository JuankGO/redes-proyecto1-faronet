# Bitácora de pruebas y resultados

Fecha de cierre documental: 1 de noviembre de 2026.
Los datos se identifican como observados, reportados por el grupo o calculados.
No se guardan identidades, direcciones ni bitácoras de tráfico de usuarios.

## 1. Pruebas automatizadas ejecutadas

| Prueba | Comando | Resultado observado | Alcance |
| --- | --- | --- | --- |
| Python | python -m pytest tests -q | 140 aprobadas, 12,81 s en la revisión | Códec, adaptador, red, cifrado, chat, pánico y gateway |
| Worker local | npx vitest run | 23 aprobadas, una suite | Firmas, replay, WebSocket, Atom, TTL, buzón y validaciones |
| TypeScript | npx tsc --noEmit | Código de salida 0 | Tipado y compilación estática |

Entorno: PC Windows, Python 3.12, dependencias del proyecto y runtime local
de Cloudflare. Cinco pruebas del puerto pigpio usan GPIO simulado. Las 140
pruebas son casos de software, no un contador de tramas ópticas recibidas.
Estos resultados corresponden a la revisión ya ejecutada; incorporar fotos
no implica una nueva ejecución sobre las Raspberry.

## 2. Desarrollo físico y evidencia aportada

| Etapa | Resultado | Origen |
| --- | --- | --- |
| Prototipo MB102 | Emisor transparente y PT333 negro configurados próximos; resistencias, transistor, indicadores y botón visibles | Fotografías del desarrollo |
| Loopback de la protoboard | 100% de tramas recibidas a 1000 baudios; límite reportado próximo a 1050 | Reporte del grupo, sin conservar un barrido de BER por distancia |
| Conmutación manual de TX17 | TX=0 produce RX27=1; TX=1 produce RX27=0 | Captura original de terminal |
| Construcción final | Dos Faros en placa perforada, con botón, componentes y headers; vista conjunta y detalle frontal/posterior individual | Fotografías del cierre |
| Enlace entre placas soldadas | El último diagnóstico guardado no recuperó tramas válidas | Ensayo SSH descrito abajo |

La protoboard sí tuvo funcionamiento óptico reportado. La lectura 1/0 adjunta
demuestra la respuesta estática en el ensayo fotografiado; la recepción de
tramas a 1000 baudios se atribuye al reporte del grupo. Son dos evidencias
distintas y se conservan con su origen.

Fotos e identificación: [inventario de evidencias](../hardware/fotos/README.md).

## 3. Diagnóstico observado por SSH

Se controlaron ambas Raspberry mediante SSH sin cambiar el programa instalado.

| Comprobación | Resultado observado |
| --- | --- |
| TX en A y B | Secuencia UART de 14 bytes a 300 baudios, unos 0,48 s |
| B sin pull interno | Datos repetitivos e inestables, sin seguimiento claro del emisor |
| A durante la secuencia de B | 0 bytes y 0 transiciones |
| Ambos sentidos con pull-up interno | 0 bytes y 0 transiciones útiles |
| Alineación repetida A hacia B | RX de B permaneció en 1 con pull-up; sin él fluctuó |

Conclusión de ese ensayo: sin recepción válida entre placas soldadas.
La causa no quedó aislada entre alineación, conexiones y acondicionamiento.
Este resultado corresponde a esa sesión y no borra el funcionamiento previo
de la protoboard ni la respuesta lógica de la captura.

## 4. Rendimiento: cálculos de referencia

Las cifras siguientes son **proyecciones teóricas, no mediciones por distancia**.
Supuestos: 3,3 V, R4 de 10 k, emisores y detectores correctamente enfrentados,
iluminación suficiente, sin errores, sin reintentos y sin competencia del canal.
No se asigna una probabilidad de fallo óptico que no pueda calcularse del montaje.

El código usa 114 bytes de payload por DATA máxima. Con Manchester, preámbulo,
SFD, UART 8N1 y el byte auxiliar de pigpio:

- DATA: 128 bytes lógicos -> **267 bytes UART**.
- ACK: 14 bytes lógicos -> **39 bytes UART**.
- Separación de ráfagas: **20 tiempos de byte** por recepción.
- Ciclo ideal DATA/ACK: (267 + 39 + 2 x 20) x 10 / baudios.
- Tasa de payload ideal con ACK: 114 / tiempo del ciclo.

| Baudios | Tiempo DATA | Ciclo ideal DATA/ACK | Tasa ideal sin ACK | Tasa ideal con ACK |
| --- | --- | --- | --- | --- |
| 300 | 8,90 s | 11,53 s | 12,81 B/s | 9,88 B/s |
| 1000 | 2,67 s | 3,46 s | 42,70 B/s | 32,95 B/s |

La columna sin ACK es el cociente de payload entre tiempo de transmisión,
sin pausa ni procesamiento. La columna con ACK agrega dos silencios de veinte
bytes. Las tasas físicas pueden ser menores por procesamiento, errores y espera.

### Comparación ideal de tres distancias

| Distancia de referencia | Sentido | Baudios | BER del modelo ideal | Payload ideal con ACK |
| --- | --- | --- | --- | --- |
| 1 cm | A a B y B a A | 300 | 0, supuesto sin errores | 9,88 B/s |
| 2 cm | A a B y B a A | 300 | 0, supuesto sin errores | 9,88 B/s |
| 5 cm | A a B y B a A | 300 | 0, supuesto sin errores | 9,88 B/s |

Los tres valores coinciden porque el modelo calcula tiempos de protocolo y
supone recepción correcta a cada distancia. No modela potencia, ruido ni ángulo
del detector; por eso no permite afirmar que la BER física sea cero o que el
alcance de 5 cm esté demostrado. Este cuadro completa la referencia numérica,
pero no acredita la medición experimental a tres distancias del enunciado.

Fuente del ensayo de 0/5: [captura histórica del diagnóstico](../hardware/fotos/prueba-loopback-diagnostico.jpg).

BER de la herramienta = bits distintos / bits comparados; una trama perdida
cuenta como todos sus bits erróneos. Una prueba capturada de 0/5 tramas y
5120/5120 bits contabilizados como erróneos da **BER=1,00** para ese ensayo;
no significa que cada bit óptico individual haya sido observado y cambiado.
La tasa útil confirmada en un ensayo sin ninguna entrega es **0 B/s**.

Para reproducir el experimento, el manual usa 100 tramas de BER y 20 con ACK
por distancia y sentido, luz ambiental normal y pausa de 1 s a 300 baudios.
Las distancias 1, 2 y 5 cm son las del escenario de referencia, no separaciones
reconstruidas de una fotografía.

## 5. Estado de los casos de integración

| Caso | Estado documentado al cierre |
| --- | --- |
| Emisor y receptor de la protoboard | Respuesta 1/0 fotografiada y loopback completo reportado a 1000 baudios |
| Texto y ACK entre placas finales | Sin entrega confirmada en el diagnóstico guardado |
| Dos comunidades exclusivamente por Faro | Prueba de software disponible; demostración física no acreditada por el registro |
| Ruta con tres relays | Probada por software; no se atribuye una ejecución por luz |
| Privado y tema compartido | Pruebas de cifrado y aplicación aprobadas en software |
| Pánico | Borrado y renovación probados por software; botón visible en ambas placas |
| Publicación al Worker | Implementada, con 23 pruebas locales aprobadas; no utilizada por el grupo |
| Buzón de blobs | Tamaño fijo, TTL y borrado al leer probados localmente |

## 6. Incidencias y tratamiento

| Incidencia | Tratamiento o conclusión |
| --- | --- |
| Archivo no encontrado | Usar módulos desde la raíz del repositorio |
| GPIO ya en uso | Un solo lector por Raspberry; liberar puerto antes de abrir |
| Receptor activo en bajo | Inversión RX habilitada en el puerto pigpio |
| Scripts anteriores GPIO14/15 | emisor.py y receptor.py retirados |
| Difusión informa enviado sin confirmar | Comprobar el texto en el receptor o usar dirección unicast para ACK |
| Lectura sensible al pull interno | Revisar acondicionamiento; la sesión no aisló una causa única |
| Ráfagas sin separación | Pausa de un segundo a 300 baudios en las pruebas BER |
| Horas reconstruidas al cierre | Veinte horas-persona identificadas como estimación, diez por integrante |
