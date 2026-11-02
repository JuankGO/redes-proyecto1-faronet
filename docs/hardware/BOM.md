# Lista de materiales y presupuesto

Montaje actual: dos Faros para Raspberry Pi 2, GPIO17/27, PT333 y electrónica a
3,3 V. Cada Faro requiere **seis resistencias** y un condensador, además de los
semiconductores, indicadores, botón y conectores. Esta lista sustituye como guía
de montaje al PDF histórico `FaroNet_Materiales.pdf`, que corresponde a otros
valores de resistencias y a un receptor de polaridad distinta.

## Componentes por placa y para el par

Los precios son **estimaciones de presupuesto en colones**, no una factura ni
una cotización vigente. Permiten valorar piezas que vienen de un kit sin precio
unitario conocido. No incluyen transporte, impuestos adicionales ni Raspberry.
Se deben sustituir por el costo real si se dispone del comprobante.

| Ref. | Material | Por Faro | Para dos | Precio unitario CRC | Subtotal dos CRC |
| --- | --- | --- | --- | --- | --- |
| D1 | LED IR compatible con PT333, nominalmente 940 nm | 1 | 2 | 350 | 700 |
| Q2 | Fototransistor PT333 negro | 1 | 2 | 900 | 1800 |
| Q1 | NPN 2N2222A | 1 | 2 | 447 | 894 |
| R1 | Resistencia 330 ohmios, 1/4 W | 1 | 2 | 50 | 100 |
| R2 | Resistencia 2,2 kiloohmios, 1/4 W | 1 | 2 | 50 | 100 |
| R3, R4 | Resistencia 10 kiloohmios, 1/4 W | 2 | 4 | 50 | 200 |
| R5, R6 | Resistencia 1 kiloohmio, 1/4 W | 2 | 4 | 50 | 200 |
| C1 | Cerámico 100 nF, código 104 | 1 | 2 | 100 | 200 |
| D2, D3 | LED visible TX y RX, colores disponibles | 2 | 4 | 100 | 400 |
| SW1 | Pulsador normalmente abierto | 1 | 2 | 250 | 500 |
| J1 | Tira de header de siete contactos, paso 2,54 mm | 1 | 2 | 200 | 400 |
| Cableado | Cables desmontables compatibles con los headers | 7 | 14 | 50 | 700 |
| Placa | Perforada de islas, HS-03 o equivalente | 1 | 2 | 1000 | 2000 |
| Puentes | Porción de alambre aislado por placa | 1 | 2 | 200 | 400 |
| Consumible | Porción de estaño y flux por placa | 1 | 2 | 250 | 500 |
| TOTAL | Valor estimado de ambos circuitos | - | - | - | **9094** |

Valor estimado por Faro: **CRC 4547**. El precio de Q1 toma como referencia el
presupuesto anterior (USD 0,95 a CRC 470/USD, redondeado); los demás son
asignaciones orientativas. No se afirma que el PT333 ni la placa HS-03 se hayan
comprado a esos precios. El emisor debe identificarse por su referencia real;
un encapsulado transparente no demuestra por sí solo su longitud de onda.

## Equipos reutilizados y herramientas

| Recurso | Cantidad | Tratamiento del costo |
| --- | --- | --- |
| Raspberry Pi 2 Model B, 1 GB | 2 | Ya disponibles; valor de reposición no cotizado |
| MicroSD con Raspberry Pi OS | 2 | Ya disponibles; no se necesita una capacidad específica de 256 GB |
| Fuente micro-USB apropiada para cada Raspberry | 2 | Reutilizada si está disponible |
| MB102 y jumpers | 1 o más | Solo prototipado; no sustituyen placas soldadas |
| PC, teclado, pantalla y cables Ethernet | Según montaje | Equipo de desarrollo reutilizado |
| Cautín, base, pinzas y cortador | Un juego | Herramientas, no componentes de cada Faro |
| Multímetro | 1 | Necesario para las mediciones exigidas; modelo y evidencia pendientes |

Si se necesitan fuentes nuevas, el presupuesto histórico contemplaba alrededor
de CRC 5593 por las dos. El valor de circuitos más esas fuentes sería cercano a
CRC 14687. El kit de soldadura y multímetro tenía una referencia histórica de
CRC 18306. Son referencias del documento anterior, no precios actualizados.

## Justificación de las piezas

- R1 limita la corriente IR. Con 3,3 V y caídas típicas de LED/transistor se espera un orden de 5-6 mA, que se confirma midiendo la caída en R1.
- R2 limita la corriente de base y R3 mantiene apagado Q1 cuando no hay excitación.
- R4 lleva RX a 3,3 V en oscuridad; el PT333 lo lleva hacia GND con luz.
- R5 y R6 limitan corriente de los indicadores; su color no afecta los GPIO.
- C1 desacopla 3,3 V y GND y no tiene polaridad.
- J1 y los cables permiten retirar la Raspberry sin desoldarla.

No se utilizan LM311, LDR, receptor de control remoto de 38 kHz ni alimentación
de 5 V en esta versión. La fuente de la Raspberry sí entrega su alimentación
normal por micro-USB; eso es distinto de aplicar 5 V a un GPIO.

## Referencias de compra históricas

El documento anterior cita CRCibernética y una consulta del 13 de octubre de
2026. Se conservan para localizar categorías y contrastar una compra; los precios
y modelos concretos deben verificarse en el comprobante o con el proveedor.

- https://www.crcibernetica.com/infrared-emitters-and-detectors/
- https://www.crcibernetica.com/bjt-transistor-npn-2n2222a/
- https://www.crcibernetica.com/prototype-pcb-5x7cm-one-sided-board/
- https://www.crcibernetica.com/jumper-wire-kit-140pcs/
- https://www.crcibernetica.com/soldering-and-multimeter-kit/
