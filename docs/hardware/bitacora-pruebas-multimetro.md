# Bitácora de pruebas con multímetro: Faro A y Faro B (versión simplificada)

**Proyecto:** FaroNet, Proyecto 1 de Redes de Computadoras (TEC)
**Integrantes:** Jimmy Castillo Guzmán, Juan Carlos Gómez
**Multímetro usado:** [modelo, por ejemplo VC830L]
**Referencia:** esquemático `docs/hardware/circuito-faro.html` (ahí están marcados los puntos TP1 a TP6)

Esta versión del Faro solo lleva LED IR (D1), fototransistor (Q2), un 2N2222A (Q1), cinco resistencias (R1 a R5), dos LEDs (D2, D3) y el botón (SW1). Todo va a 3.3 V y no hay 5 V en la placa.

Todas las mediciones de voltaje se toman con la punta negra en GND (TP2). Llenen las columnas "Faro A" y "Faro B" con lo que midan, y marquen "OK" solo si el valor cae en el rango esperado. Si algo falla, anótenlo en la sección 9 con la corrección que hicieron.

**Orden obligatorio:** no conecten la placa a la Raspberry hasta pasar las secciones 1 a 4.

| TP | Dónde |
|---|---|
| TP1 | Riel 3V3 (arriba de R1 y colector de Q2) |
| TP2 | GND |
| TP3 | Base de Q1 |
| TP4 | Colector de Q1 (cátodo de D1) |
| TP5 | RXD: emisor de Q2, arriba de R3 |
| TP6 | GPIO17: pata del botón que va a J1-7 |

| J1 | Señal | Pin físico RPi |
|---|---|---|
| 1 | 3V3 | 1 |
| 2 | GND | 6 |
| 3 | TXD | 8 (GPIO14) |
| 4 | RXD | 10 (GPIO15) |
| 5 | LED_TX | 16 (GPIO23) |
| 6 | LED_RX | 18 (GPIO24) |
| 7 | PANICO | 11 (GPIO17) |

---

## 1. Inspección visual (sin energía)

| # | Revisión | Faro A | Faro B |
|---|---|---|---|
| 1.1 | Juntas cónicas y brillantes; ninguna fría (opaca o granulada) ni en bola | | |
| 1.2 | Sin puentes de estaño entre pads vecinos (revisar con lupa o la cámara del celular) | | |
| 1.3 | D1 con el ánodo hacia R1 | | |
| 1.4 | Q2 con el colector hacia 3V3 y el emisor hacia R3 | | |
| 1.5 | D1 y Q2 al borde de la placa, de frente, separados ≥ 2 cm con una barrera opaca | | |
| 1.6 | Tubito negro alrededor de Q2 | | |
| 1.7 | LEDs D2 y D3 con la pata larga hacia R4 y R5 | | |
| 1.8 | Q1 orientado según el datasheet (C-B-E) | | |
| 1.9 | SW1 conectado por dos patas en diagonal | | |
| 1.10 | Header J1 de 7 pines firme y recto; cables ordenados | | |

Fecha: __________ Responsable: __________

---

## 2. Continuidad (sin energía, modo continuidad/pitido)

Cada fila debe pitar. Midan de pad a pad, no de pata a pata, para comprobar también la soldadura.

| # | Desde | Hasta | Red | Faro A | Faro B |
|---|---|---|---|---|---|
| 2.1 | J1 pin 1 | R1 (lado de arriba) | 3V3 | | |
| 2.2 | J1 pin 1 | Colector de Q2 | 3V3 | | |
| 2.3 | J1 pin 2 | Emisor de Q1 | GND | | |
| 2.4 | J1 pin 2 | R3 (lado de abajo) | GND | | |
| 2.5 | J1 pin 2 | Cátodo de D2, cátodo de D3, una pata de SW1 | GND | | |
| 2.6 | J1 pin 3 | R2 (un lado) | TXD | | |
| 2.7 | R2 (otro lado) | Base de Q1 | BASE | | |
| 2.8 | R1 (lado de abajo) | Ánodo de D1 | — | | |
| 2.9 | Cátodo de D1 | Colector de Q1 | — | | |
| 2.10 | J1 pin 4 | Emisor de Q2 y R3 (lado de arriba) | RXD | | |
| 2.11 | J1 pin 5 | R4 → ánodo de D2 | LED_TX | | |
| 2.12 | J1 pin 6 | R5 → ánodo de D3 | LED_RX | | |
| 2.13 | J1 pin 7 | Otra pata de SW1 (la diagonal) | PANICO | | |

---

## 3. Ausencia de cortos (sin energía, sin Raspberry)

Modo resistencia. Lo importante es que **ninguna** de estas filas pite ni marque cerca de 0 Ω.

| # | Entre | Esperado | Faro A | Faro B | OK |
|---|---|---|---|---|---|
| 3.1 | 3V3 y GND (J1-1 y J1-2) | OL o varios kΩ o más. Nunca menos de 1 kΩ | | | |
| 3.2 | TXD y GND (J1-3 y J1-2) | No pita (se ve R2 más la base de Q1) | | | |
| 3.3 | RXD y GND (J1-4 y J1-2) | ≈ R3 (10 kΩ) con Q2 tapado. Nunca ≈ 0 Ω | | | |
| 3.4 | TXD y RXD (J1-3 y J1-4) | No pita (puede marcar varios kΩ: pasa por R2, Q1 y R3) | | | |
| 3.5 | Pines vecinos de J1 (1-2, 2-3, 3-4, 4-5, 5-6, 6-7) | Ninguno en corto | | | |
| 3.6 | Botón suelto: J1-7 y GND | OL | | | |
| 3.7 | Botón presionado: J1-7 y GND | ≈ 0 Ω (pita) | | | |

Fecha: __________ Responsable: __________

---

## 4. Verificación de componentes (sin energía, modo diodo)

| # | Componente | Puntas | Esperado | Faro A | Faro B |
|---|---|---|---|---|---|
| 4.1 | D1 LED IR | Roja en ánodo, negra en cátodo | ≈ 1.0–1.2 V. Al revés: OL | | |
| 4.2 | D2 LED verde | Roja en ánodo, negra en cátodo | ≈ 1.8–2.6 V (puede encender un poco) | | |
| 4.3 | D3 LED rojo | Roja en ánodo, negra en cátodo | ≈ 1.6–1.9 V | | |
| 4.4 | Q1 base-emisor | Roja en base, negra en emisor | ≈ 0.6–0.7 V | | |
| 4.5 | Q1 base-colector | Roja en base, negra en colector | ≈ 0.6–0.7 V | | |
| 4.6 | Q1 colector-emisor | Ambos sentidos | OL | | |
| 4.7 | R1 (modo Ω) | | ≈ 100 Ω | | |
| 4.8 | R2 (modo Ω) | | ≈ 1 kΩ | | |
| 4.9 | R3 (modo Ω, Q2 tapado) | | ≈ 10 kΩ (o el valor que pusieron) | | |
| 4.10 | R4, R5 (modo Ω) | | ≈ 330 Ω | | |

---

## 5. Primer encendido (Raspberry conectada)

1. Apaguen la Raspberry.
2. Conecten los 7 cables dupont según la tabla de arriba.
3. Revisen dos veces que J1-1 va al pin 1 (3.3V) y no al 2 ni al 4 (5V). Con 5 V, RXD puede pasar de 3.3 V y dañar el GPIO15.
4. Enciendan la Raspberry y midan.

| # | Punto | Condición | Esperado | Faro A | Faro B | OK |
|---|---|---|---|---|---|---|
| 5.1 | TP1 (3V3) | — | 3.2–3.4 V | | | |
| 5.2 | TP6 (GPIO17) | Botón suelto, con pull-up activado (ver abajo) | ≈ 3.3 V | | | |
| 5.3 | TP6 | Botón presionado | 0 V | | | |
| 5.4 | LED verde D2 | `pinctrl set 23 op dh` | Enciende | | | |
| 5.5 | LED rojo D3 | `pinctrl set 24 op dh` | Enciende | | | |

Comandos en la terminal de la Raspberry (Raspberry Pi OS Bookworm; en versiones anteriores cambien `pinctrl` por `raspi-gpio`):

1. `pinctrl set 17 ip pu`
2. `pinctrl get 17` (debe decir `hi` suelto y `lo` presionado)
3. `pinctrl set 23 op dh` (enciende el LED verde)
4. `pinctrl set 23 op dl` (lo apaga)
5. `pinctrl set 24 op dh` (enciende el LED rojo)
6. `pinctrl set 24 op dl` (lo apaga)

---

## 6. Emisor (Raspberry conectada)

Con la UART activada, GPIO14 queda en 1 cuando no transmite, así que el LED IR queda encendido. Para forzar estados durante la prueba:

1. `pinctrl set 14 op dh` (TX en 1: LED IR encendido)
2. `pinctrl set 14 op dl` (TX en 0: LED IR apagado)
3. `pinctrl set 14 a0` (devuelve GPIO14 a la UART al terminar)

| # | Punto | Condición | Esperado | Faro A | Faro B | OK |
|---|---|---|---|---|---|---|
| 6.1 | TP3 (base de Q1) | TX en 1 | ≈ 0.7 V | | | |
| 6.2 | TP3 | TX en 0 | 0 V | | | |
| 6.3 | TP4 (colector de Q1) | TX en 1 | ≈ 0.1–0.2 V | | | |
| 6.4 | TP4 | TX en 0 | ≈ 2–3.3 V | | | |
| 6.5 | Caída en R1 (puntas en sus dos patas) | TX en 1 | ≈ 1.8 V (equivale a ≈ 18 mA) | | | |
| 6.6 | Caída en D1 (puntas en sus dos patas) | TX en 1 | ≈ 1.2–1.4 V | | | |
| 6.7 | D1 visto con la cámara del celular | TX en 1 | Se ve una luz morada | | | |

---

## 7. Receptor (Raspberry conectada)

Con la versión simplificada no hay comparador: RXD (TP5) va directo al GPIO15. La Pi lee 0 por debajo de 0.9 V y 1 por encima de 1.6 V; para tener margen buscamos ≤ 0.5 V a oscuras y ≥ 2 V con luz.

| # | Punto | Condición | Esperado | Faro A | Faro B | OK |
|---|---|---|---|---|---|---|
| 7.1 | TP5 (RXD) | Q2 tapado con el dedo | ≤ 0.5 V | | | |
| 7.2 | TP5 | Luz ambiente normal, otro Faro apagado | ≤ 0.5 V | | | |
| 7.3 | TP5 | Propio LED encendido (TX en 1), otro Faro apagado | ≤ 0.5 V (si sube, le llega luz de su propio D1) | | | |
| 7.4 | TP5 | Otro Faro encendido de frente a la distancia de trabajo | ≥ 2 V | | | |
| 7.5 | TP5 | En ningún caso | ≤ 3.4 V | | | |

### Ajuste de R3

Si 7.1 a 7.4 no dan lo esperado, cambien R3 y repitan la sección 7.

| Síntoma | Corrección |
|---|---|
| 7.4 nunca llega a 2 V | Subir R3 a 22 kΩ o 47 kΩ, o acercar los Faros |
| 7.2 pasa de 0.5 V | Bajar R3 a 4.7 kΩ y poner el tubito negro en Q2 |
| 7.3 pasa de 0.5 V | Separar más D1 de Q2 y poner una barrera opaca entre ellos |
| No sube nunca, ni con luz | Revisar la polaridad de Q2 (colector a 3V3) y que D1 del otro Faro se vea morado en la cámara |

| Faro | R3 final | TP5 oscuro | TP5 con luz | Distancia de trabajo |
|---|---|---|---|---|
| A | | | | |
| B | | | | |

---

## 8. Prueba del enlace sin software de FaroNet

Sirve para confirmar el hardware antes de usar `DispositivoLuzAdaptador`. Primero desactiven la consola serie (`sudo raspi-config nonint do_serial_cons 1`) y reinicien.

En el Faro B (recibe):

1. `stty -F /dev/ttyAMA0 9600 raw -echo`
2. `cat /dev/ttyAMA0`

En el Faro A (envía):

1. `stty -F /dev/ttyAMA0 9600 raw -echo`
2. `echo "hola faro" > /dev/ttyAMA0`

Sin comparador, los bordes del fototransistor son lentos. Empiecen a 9600 baudios y bajen a 4800 o 2400 si llegan caracteres raros. La velocidad que funcione es la que se usa después con `--baudios` en los dos Faros. (Los LEDs D2 y D3 los maneja el software de FaroNet, así que en esta prueba no se encienden.)

| # | Distancia | Velocidad | ¿Llegó "hola faro" completo? | Observaciones |
|---|---|---|---|---|
| 8.1 | 10 cm | 9600 | | |
| 8.2 | 25 cm | 9600 | | |
| 8.3 | 50 cm | 9600 | | |
| 8.4 | 1 m | 9600 | | |
| 8.5 | 50 cm | 19200 | | |
| 8.6 | 50 cm | 4800 | | |

Las mediciones formales de tasa efectiva y BER van en el Apéndice B del RFC (`python3 -m faro.medir`).

---

## 9. Problemas encontrados y correcciones

| Fecha | Faro | Problema | Causa | Corrección | Prueba que lo confirma |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |

---

## 10. Evidencia

- Foto de la cara de componentes del Faro A: `docs/hardware/fotos/faro-a-frente.jpg`
- Foto de la cara de soldaduras del Faro A: `docs/hardware/fotos/faro-a-atras.jpg`
- Foto de la cara de componentes del Faro B: `docs/hardware/fotos/faro-b-frente.jpg`
- Foto de la cara de soldaduras del Faro B: `docs/hardware/fotos/faro-b-atras.jpg`
- Fotos del multímetro en las mediciones 3.1, 5.1, 7.2 y 7.4 (recomendado)
