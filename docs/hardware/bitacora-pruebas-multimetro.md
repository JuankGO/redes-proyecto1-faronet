# Registro eléctrico y referencias para multímetro

**Integrantes:** Jimmy Castillo Guzmán y Juan Carlos Gómez.
**Cierre documental:** 1 de noviembre de 2026.
**Circuito:** GPIO17/27, alimentación de 3,3 V y PT333 con pull-up de 10 k.
**Lectura disponible:** GPIO27 mediante pigpio, documentada en fotografía.
**Origen de los valores analógicos:** cálculo nominal del esquema; no son
lecturas tomadas con un multímetro. Las tablas están completas como referencia
de diseño y conservan separada la evidencia observada.

## 1. Evidencia observada

| Acción registrada en la captura | Lectura de GPIO27 | Interpretación |
| --- | --- | --- |
| GPIO17 en 0, emisor apagado | 1 | RX alto por el pull-up |
| GPIO17 en 1, emisor encendido | 0 | El fototransistor conduce y lleva RX a nivel bajo |

Fuente: [captura original](fotos/prueba-gpio-1-0.jpg).
El retorno a 1 al apagar nuevamente el emisor también fue reportado por el grupo
durante el desarrollo. Un 1/0 no proporciona por sí solo un voltaje analógico.

## 2. Puntos de prueba

| Punto | Red |
| --- | --- |
| TP1 | Alimentación 3,3 V |
| TP2 | GND, referencia de tensión |
| TP3 | Base del transistor Q1 |
| TP4 | Colector de Q1 |
| TP5 | RX, colector del PT333 y GPIO27 |
| TP6 | Botón, GPIO24 |

## 3. Continuidad y cortos: criterios del diseño

Estos son valores objetivo, aplicables a ambas placas sin alimentación.
Para una conexión directa se propone menos de 1 ohmio después de descontar
las puntas. No se atribuye esa lectura a una medición ya realizada.

| Comprobación | Referencia de aceptación |
| --- | --- |
| J1-1 a alimentación de R4 y C1 | Menos de 1 ohmio por segmento de cable o soldadura |
| J1-2 a emisores de Q1 y Q2 | Menos de 1 ohmio por segmento |
| J1-3 a entrada de R2 | Menos de 1 ohmio |
| Salida de R2 a base de Q1 | Menos de 1 ohmio |
| J1-4 a colector de Q2 y extremo RX de R4 | Menos de 1 ohmio |
| Rama R1-D1-Q1 | Menos de 1 ohmio en cada unión directa; no atravesar componentes para exigir continuidad |
| J1-5 y J1-6 a resistencias de indicadores | Menos de 1 ohmio por conexión directa |
| J1-7 a SW1 y retorno de SW1 a GND | Menos de 1 ohmio por conexión directa |
| Header a pines físicos 1, 6, 11, 13, 15, 16 y 18 | Siete correspondencias según el esquema |
| Botón abierto / pulsado, aislado del circuito | OL / menos de 1 ohmio |
| VCC-GND, pads vecinos de J1 y TX-RX | Cero puentes metálicos ajenos al esquema |

No se fija una resistencia total VCC-GND: condensador y semiconductores cambian
la indicación del instrumento. La fotografía de soldaduras documenta la
construcción, mientras que el criterio anterior define la comprobación eléctrica.

## 4. Componentes: valores nominales

| Ref. | Valor de diseño en A y B | Tipo de dato |
| --- | --- | --- |
| R1 | 330 ohmios | Nominal del esquema |
| R2 | 2200 ohmios | Nominal del esquema |
| R3 | 10000 ohmios, base-GND | Nominal del esquema |
| R4 | 10000 ohmios, pull-up RX | Nominal del esquema |
| R5 | 1000 ohmios | Nominal del esquema |
| R6 | 1000 ohmios | Nominal del esquema |
| C1 | 100 nF, código 104 | Nominal del esquema |
| D1 | Caída directa de 1,20 V | Supuesto de cálculo del LED IR |
| Q1 | VBE=0,70 V y VCE activo=0,20 V | Supuestos de conducción y saturación |
| Q2 | RX iluminado=0,20 V | Supuesto de iluminación suficiente |

Los supuestos aproximan el funcionamiento esperado; el componente real puede
tener otros valores. El patillaje se identifica por la referencia física de
cada transistor y no se deduce solo de su forma.

## 5. Tensiones y corrientes calculadas

Punta de referencia en TP2. Los valores A/B son iguales porque ambas unidades
usan el mismo esquema, no porque se hayan medido resultados idénticos.

| Punto y condición | Faro A, modelo | Faro B, modelo |
| --- | --- | --- |
| TP1, alimentación nominal | 3,30 V | 3,30 V |
| TP2, referencia | 0,00 V | 0,00 V |
| TP3, TX apagado | 0,00 V | 0,00 V |
| TP3, TX encendido | 0,70 V | 0,70 V |
| TP4, TX encendido | 0,20 V | 0,20 V |
| Caída en R1, TX encendido | 1,90 V | 1,90 V |
| Corriente del LED IR | 5,76 mA | 5,76 mA |
| Corriente de base Q1, descontando R3 | 1,11 mA | 1,11 mA |
| TP5, detector oscuro | 3,30 V | 3,30 V |
| TP5, detector suficientemente iluminado | 0,20 V | 0,20 V |
| Corriente por R4 con RX=0,20 V | 0,31 mA | 0,31 mA |
| TP6, botón suelto y pull-up activo | 3,30 V | 3,30 V |
| TP6, botón pulsado | 0,00 V | 0,00 V |

Cálculos por ley de Ohm:

- VR1 = 3,30 - 1,20 - 0,20 = **1,90 V**.
- IIR = 1,90 / 330 = **5,76 mA**.
- IB = (3,30 - 0,70) / 2200 - 0,70 / 10000 = **1,11 mA**.
- IR4 = (3,30 - 0,20) / 10000 = **0,31 mA**.

La lectura digital observada es coherente con este modelo: oscuridad produce
nivel alto e iluminación produce nivel bajo. La coincidencia lógica no
convierte los valores calculados en mediciones de tensión.

## 6. Cierre del registro

| Fecha del cierre | Responsables | Método | Resultado documentado |
| --- | --- | --- | --- |
| 01/11/2026 | Jimmy y Juan | Fotografía y lectura pigpio | Dos placas construidas; captura RX=1/0 según TX |
| 01/11/2026 | Jimmy y Juan, revisión documental | Análisis nominal del circuito | Tablas completas de referencias, criterios y corrientes calculadas |
