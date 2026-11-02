# Bitácora de pruebas con multímetro

**Integrantes:** Jimmy Castillo Guzmán y Juan Carlos Gómez.
**Circuito:** esquema GPIO17/27 a 3,3 V, PT333 con pull-up de 10 k.
**Instrumento, fecha y responsable:** pendientes de registrar en cada sesión.
**Estado:** procedimiento preparado; no se recibieron valores medidos con multímetro.

Las columnas pendientes no equivalen a pruebas aprobadas. Las lecturas `pigs r`
son digitales, no mediciones de voltaje ni de continuidad.

## Puntos de prueba

| Punto | Red |
| --- | --- |
| TP1 | Alimentación 3,3 V |
| TP2 | GND, referencia de las medidas de tensión |
| TP3 | Base del transistor driver Q1 |
| TP4 | Colector de Q1 |
| TP5 | RX, colector del PT333 y GPIO27 |
| TP6 | Botón, GPIO24 |

## 1. Inspección y continuidad, sin alimentación

Desconectar la Raspberry y cualquier fuente. Medir entre pads para comprobar
también la soldadura. No esperar un pitido a través de resistencias o diodos.

| Comprobación | Criterio | A | B |
| --- | --- | --- | --- |
| Soldaduras y alambres | Sin puentes accidentales ni uniones flojas | Pendiente | Pendiente |
| J1-1 a extremo superior de R4 | Continuidad directa de 3V3 | Pendiente | Pendiente |
| J1-2 a emisor Q1 y emisor Q2 | Continuidad directa de GND | Pendiente | Pendiente |
| J1-3 a entrada de R2 | Continuidad directa de TX | Pendiente | Pendiente |
| Salida R2 a base Q1 | Continuidad directa | Pendiente | Pendiente |
| J1-4 a colector Q2 y extremo RX de R4 | Continuidad directa de RX | Pendiente | Pendiente |
| R1 y D1, rama hacia colector Q1 | Continuidad en cada segmento sin atravesar el LED o R1 | Pendiente | Pendiente |
| J1-5 y J1-6 a sus resistencias | Continuidad de indicadores | Pendiente | Pendiente |
| J1-7 a SW1; otro contacto a GND | Continuidad según esquema | Pendiente | Pendiente |
| Header a pines físicos 1,6,11,13,15,16,18 | Cada cable llega a su función | Pendiente | Pendiente |

## 2. Ausencia de cortos, sin alimentación

| Medida | Criterio | A | B |
| --- | --- | --- | --- |
| VCC-GND | Sin corto estable; C1 puede causar una lectura transitoria | Pendiente | Pendiente |
| Pads vecinos de J1 | Sin puentes ajenos al esquema | Pendiente | Pendiente |
| RX-GND con detector oscuro | No debe existir puente directo permanente | Pendiente | Pendiente |
| TX-RX | Sin unión directa | Pendiente | Pendiente |
| Botón abierto y pulsado | Abierto y continuidad respectivamente | Pendiente | Pendiente |

Anotar la resistencia real y la estabilidad de la lectura; no declarar un valor
universal VCC-GND porque los semiconductores y el condensador afectan la medida.
Si hay corto, corregirlo antes de conectar la Raspberry.

## 3. Valores de componentes

Para medir una resistencia sin caminos paralelos, levantar una pata si hace
falta, siempre sin energía. Confirmar tolerancia con bandas o referencia.

| Ref. | Valor esperado | A medido | B medido |
| --- | --- | --- | --- |
| R1 | 330 ohmios | Pendiente | Pendiente |
| R2 | 2,2 kiloohmios | Pendiente | Pendiente |
| R3 | 10 kiloohmios, base-GND | Pendiente | Pendiente |
| R4 | 10 kiloohmios, pull-up RX | Pendiente | Pendiente |
| R5 | 1 kiloohmio | Pendiente | Pendiente |
| R6 | 1 kiloohmio | Pendiente | Pendiente |
| D1 | Conducción en un sentido, según su ficha | Pendiente | Pendiente |
| Q1 | Patillaje y uniones B-E/B-C de NPN confirmados | Pendiente | Pendiente |
| Q2 | Patillaje C/E confirmado | Pendiente | Pendiente |

## 4. Tensiones, con alimentación

Solo después de aprobar continuidad y cortos. Punta negra en TP2, salvo la
caída en R1, que se mide entre sus dos extremos. Los valores de la tabla son
objetivos de diseño aproximados, no lecturas ya obtenidas ni límites absolutos
del fabricante.

| Punto y condición | Objetivo | A medido | B medido |
| --- | --- | --- | --- |
| TP1 | Cercano a 3,3 V | Pendiente | Pendiente |
| TP3, TX apagado | Cercano a 0 V | Pendiente | Pendiente |
| TP3, TX encendido | Unión B-E conduciendo, normalmente 0,6-0,8 V | Pendiente | Pendiente |
| TP4, TX encendido | Bajo si Q1 satura, normalmente inferior a 0,3 V | Pendiente | Pendiente |
| Caída en R1, TX encendido | Registrar y calcular I=V/330 | Pendiente | Pendiente |
| TP5, detector tapado, otro IR apagado | Alto, próximo a 3,3 V | Pendiente | Pendiente |
| TP5, IR del otro Faro enfrentado y encendido | Bajo, objetivo inferior a 0,5 V | Pendiente | Pendiente |
| TP5 en cualquier condición | No superar 3,3 V nominales de la electrónica | Pendiente | Pendiente |
| TP6, botón suelto y pull-up activo | Cercano a 3,3 V | Pendiente | Pendiente |
| TP6, botón pulsado | Cercano a 0 V | Pendiente | Pendiente |

El IR encendido se fuerza con `pigs modes 17 w` y `pigs w 17 1`; se apaga con
`pigs w 17 0`. El receptor permanece como entrada (`pigs modes 27 r`). Detener
primero los programas del Faro. Los indicadores se prueban en GPIO22 y GPIO23.
Al acabar, apagar salidas de diagnóstico y no dejar programas compitiendo.

## 5. Cierre de sesión

| Fecha | Responsable | Instrumento | Hallazgo | Corrección | Reprueba y evidencia |
| --- | --- | --- | --- | --- | --- |
| Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |

Registrar fotografías de las puntas y el valor de multímetro para VCC-GND,
alimentación y RX con/sin luz. No publicar contraseñas, direcciones de usuarios
ni llaves en esas fotos. El índice de evidencias identifica las vistas faltantes.
