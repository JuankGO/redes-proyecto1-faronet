# Bitácora de pruebas con multímetro: Faro A y Faro B

**Proyecto:** FaroNet, Proyecto 1 de Redes de Computadoras (TEC)
**Integrantes:** Jimmy Castillo Guzmán, Juan Carlos Gómez
**Multímetro usado:** [modelo, por ejemplo VC830L]
**Referencia:** esquemático `docs/hardware/circuito-faro.html` (los puntos TP1 a TP9 están marcados ahí)

Todas las mediciones de voltaje se toman con la punta negra en GND (TP3). Llenen las columnas "Faro A" y "Faro B" con lo que midan, y marquen "OK" solo si el valor cae dentro del rango esperado. Si algo falla, anótenlo en la sección 9 con la corrección que hicieron.

**Orden obligatorio:** no conecten la placa a la Raspberry ni pongan el LM311 en su socket hasta pasar las secciones 1 a 4.

---

## 1. Inspección visual (sin energía)

| # | Revisión | Faro A | Faro B |
|---|---|---|---|
| 1.1 | Juntas cónicas y brillantes; ninguna fría (opaca o granulada) ni en bola | | |
| 1.2 | Sin puentes de estaño entre pads vecinos (revisar con lupa o la cámara del celular) | | |
| 1.3 | Socket DIP-8 soldado con la muesca hacia el lado del pin 1 | | |
| 1.4 | LED IR (D1) con la pata larga hacia R1 | | |
| 1.5 | LEDs D2 y D3 con la pata larga hacia R5 y R6 | | |
| 1.6 | Q1 orientado según el datasheet (C-B-E) | | |
| 1.7 | Cables ordenados, sin cobre expuesto de más | | |
| 1.8 | Header J1 de 8 pines firme y recto | | |

Fecha: __________ Responsable: __________

---

## 2. Continuidad (sin energía, modo continuidad/pitido)

Cada fila debe pitar. Midan de pad a pad, no de pata a pata, para comprobar también la soldadura.

| # | Desde | Hasta | Red | Faro A | Faro B |
|---|---|---|---|---|---|
| 2.1 | J1 pin 1 | R1 (lado de arriba) | 5V | | |
| 2.2 | J1 pin 1 | Socket U1 pin 8 | 5V | | |
| 2.3 | J1 pin 1 | C1 (una pata) | 5V | | |
| 2.4 | J1 pin 2 | R3 (lado de arriba) | 3V3 | | |
| 2.5 | J1 pin 2 | R4 (lado de arriba) | 3V3 | | |
| 2.6 | J1 pin 2 | RV1 (un extremo) | 3V3 | | |
| 2.7 | J1 pin 3 | Emisor de Q1 | GND | | |
| 2.8 | J1 pin 3 | Emisor de Q2 | GND | | |
| 2.9 | J1 pin 3 | Socket U1 pin 1 y pin 4 | GND | | |
| 2.10 | J1 pin 3 | RV1 (otro extremo) y C1 (otra pata) | GND | | |
| 2.11 | J1 pin 3 | Cátodo de D2, cátodo de D3, una pata de SW1 | GND | | |
| 2.12 | J1 pin 4 | R2 (un lado) | TXD | | |
| 2.13 | R2 (otro lado) | Base de Q1 | BASE | | |
| 2.14 | R1 (lado de abajo) | Ánodo de D1 | — | | |
| 2.15 | Cátodo de D1 | Colector de Q1 | — | | |
| 2.16 | Colector de Q2 | R3 (lado de abajo) y socket U1 pin 3 | RX_A | | |
| 2.17 | Cursor de RV1 | Socket U1 pin 2 | VREF | | |
| 2.18 | Socket U1 pin 7 | R4 (lado de abajo) y J1 pin 5 | RXD | | |
| 2.19 | J1 pin 6 | R5 → ánodo de D2 | LED_TX | | |
| 2.20 | J1 pin 7 | R6 → ánodo de D3 | LED_RX | | |
| 2.21 | J1 pin 8 | Otra pata de SW1 | PANICO | | |

---

## 3. Ausencia de cortos (sin energía, sin LM311, sin Raspberry)

Modo resistencia. Lo importante es que **ninguna** de estas filas pite ni marque cerca de 0 Ω.

| # | Entre | Esperado | Faro A | Faro B | OK |
|---|---|---|---|---|---|
| 3.1 | 5V y GND (J1-1 y J1-3) | OL (abierto). Puede subir lentamente mientras carga C1 | | | |
| 3.2 | 3V3 y GND (J1-2 y J1-3) | ≈ 10 kΩ: es el trimpot RV1. Nunca menos de 1 kΩ | | | |
| 3.3 | 5V y 3V3 (J1-1 y J1-2) | OL | | | |
| 3.4 | TXD y RXD (J1-4 y J1-5) | OL | | | |
| 3.5 | Pines vecinos de J1 (1-2, 2-3, 3-4, 4-5, 5-6, 6-7, 7-8) | Ninguno en corto (salvo lo que dicen 3.1 a 3.4) | | | |
| 3.6 | Pines vecinos del socket U1 (1-2, 2-3, 3-4, 5-6, 6-7, 7-8) | Sin corto. 1-4 sí están unidos (ambos a GND) | | | |
| 3.7 | Botón suelto: J1-8 y GND | OL | | | |
| 3.8 | Botón presionado: J1-8 y GND | ≈ 0 Ω (pita) | | | |

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
| 4.7 | R1 (modo Ω, en la placa) | | ≈ 100 Ω | | |
| 4.8 | R2, R4 | | ≈ 1 kΩ | | |
| 4.9 | R3 | | ≈ 10 kΩ | | |
| 4.10 | R5, R6 | | ≈ 330 Ω | | |

---

## 5. Primer encendido (Raspberry conectada, todavía sin LM311)

1. Apaguen la Raspberry.
2. Conecten los 8 cables dupont según la tabla de `circuito-faro.html` (pestaña "Conexión a la Raspberry").
3. Revisen dos veces que J1-1 va al pin 2 (5V) y J1-2 al pin 1 (3.3V). Invertirlos puede dañar la placa.
4. Enciendan la Raspberry y midan.

| # | Punto | Condición | Esperado | Faro A | Faro B | OK |
|---|---|---|---|---|---|---|
| 5.1 | TP1 (5V) | — | 4.8–5.2 V | | | |
| 5.2 | TP2 (3V3) | — | 3.2–3.4 V | | | |
| 5.3 | Socket U1 pin 8 | — | igual que TP1 | | | |
| 5.4 | TP6 (colector de Q2) | Tapado con el dedo (oscuro) | ≈ 3.0–3.3 V | | | |
| 5.5 | TP6 | Apuntando con un control remoto de TV y presionando un botón | baja (oscila, el multímetro marca menos) | | | |
| 5.6 | TP7 (cursor de RV1) | Girar RV1 de un extremo al otro | de 0 V a 3.3 V | | | |
| 5.7 | TP9 (GPIO17) | Botón suelto, con pull-up activado (ver abajo) | ≈ 3.3 V | | | |
| 5.8 | TP9 | Botón presionado | 0 V | | | |

Para activar el pull-up del GPIO17 y probar los LEDs, en la terminal de la Raspberry (Raspberry Pi OS Bookworm; en versiones anteriores cambien `pinctrl` por `raspi-gpio`):

1. `pinctrl set 17 ip pu`
2. `pinctrl get 17` (debe decir `hi` suelto y `lo` presionado)
3. `pinctrl set 23 op dh` (enciende el LED verde)
4. `pinctrl set 23 op dl` (lo apaga)
5. `pinctrl set 24 op dh` (enciende el LED rojo)
6. `pinctrl set 24 op dl` (lo apaga)

---

## 6. Emisor (Raspberry conectada)

Con el UART activado, GPIO14 queda en 1 cuando no se transmite, así que el LED IR queda encendido. Para forzar estados durante la prueba:

1. `pinctrl set 14 op dh` (TX en 1: LED IR encendido)
2. `pinctrl set 14 op dl` (TX en 0: LED IR apagado)
3. `pinctrl set 14 a0` (devuelve GPIO14 al UART al terminar)

| # | Punto | Condición | Esperado | Faro A | Faro B | OK |
|---|---|---|---|---|---|---|
| 6.1 | TP4 (base de Q1) | TX en 1 | ≈ 0.7 V | | | |
| 6.2 | TP4 | TX en 0 | 0 V | | | |
| 6.3 | TP5 (colector de Q1) | TX en 1 | ≈ 0.1–0.2 V | | | |
| 6.4 | TP5 | TX en 0 | ≈ 3.5–5 V | | | |
| 6.5 | Caída en R1 | TX en 1 | ≈ 3.5 V (equivale a ≈ 35 mA) | | | |
| 6.6 | D1 visto con la cámara del celular | TX en 1 | se ve una luz morada | | | |

---

## 7. Receptor y comparador (LM311 colocado)

1. Apaguen la Raspberry.
2. Pongan el LM311 en el socket con la muesca hacia el pin 1.
3. Enciendan la Raspberry.

| # | Punto | Condición | Esperado | Faro A | Faro B | OK |
|---|---|---|---|---|---|---|
| 7.1 | Socket U1 pin 4 y pin 1 | — | 0 V | | | |
| 7.2 | TP8 (salida, GPIO15) | Q2 tapado (oscuro) | ≈ 0.1–0.3 V | | | |
| 7.3 | TP8 | LED IR del otro Faro encendido, a 1 m, apuntando | ≈ 3.3 V | | | |
| 7.4 | TP8 | Nunca debe pasar de 3.4 V | ≤ 3.4 V | | | |

Si 7.2 o 7.3 no dan lo esperado, hagan primero la calibración de abajo y repitan.

### Calibración del umbral (RV1)

| Paso | Medición | Faro A | Faro B |
|---|---|---|---|
| a | TP6 con luz ambiente normal y el otro LED apagado | | |
| b | TP6 con el otro LED encendido a la distancia de trabajo | | |
| c | Valor objetivo de TP7 = (a + b) / 2 | | |
| d | TP7 después de ajustar RV1 | | |

---

## 8. Prueba del enlace sin software de FaroNet

Sirve para confirmar el hardware antes de usar `DispositivoLuzAdaptador`. Primero desactiven la consola serie (`sudo raspi-config`, Interface Options, Serial Port: login shell No, hardware Sí) y reinicien.

En el Faro B (recibe):

1. `stty -F /dev/ttyAMA0 9600 raw -echo`
2. `cat /dev/ttyAMA0`

En el Faro A (envía):

1. `stty -F /dev/ttyAMA0 9600 raw -echo`
2. `echo "hola faro" > /dev/ttyAMA0`

| # | Distancia | Velocidad | ¿Llegó "hola faro" completo? | LED RX se encendió | Observaciones |
|---|---|---|---|---|---|
| 8.1 | 0.5 m | 9600 | | | |
| 8.2 | 1 m | 9600 | | | |
| 8.3 | 2 m | 9600 | | | |
| 8.4 | 1 m | 19200 | | | |
| 8.5 | 1 m | 38400 | | | |

Las mediciones formales de tasa efectiva y BER van en el Apéndice B del RFC.

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
- Fotos del multímetro en las mediciones 3.1, 3.2, 5.1 y 5.2 (recomendado)
