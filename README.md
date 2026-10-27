# FaroNet

Proyecto 1 de Redes de Computadoras (ITCR, II semestre 2026). Un enlace por luz infrarroja entre dos Raspberry Pi 2 (el Faro), una red mesh anónima con cebolla de 3 saltos, un chat y un Worker de Cloudflare que publica los mensajes públicos.

La especificación completa está en `docs/rfc/rfc-faronet.txt` y el modelo de amenazas en `docs/amenazas.md`.

## Estructura

| Carpeta | Qué tiene |
| --- | --- |
| `faro/` | Capa 1: trama, CRC, Manchester, UART, LEDs y botón (GPIO), medición de tasa y BER |
| `mesh/` | Capas 2 y 3: vecinos, directorio firmado, rutas, celdas de 1024 B, cebolla, enlace Faro |
| `app/` | Capa 7: mensajes de 256 B, temas con frase secreta, chat por terminal |
| `gateway/` | Puente mesh → Worker con peticiones firmadas Ed25519 |
| `worker/` | Cloudflare Worker: salas en vivo, feed Atom, buzón muerto, directorio público |
| `tests/` | Pruebas de Python (`pytest`) |
| `tools/` | Prueba manual del buzón |
| `docs/` | RFC, amenazas, circuito interactivo, bitácora de pruebas y de horas |

## Pines de la Raspberry Pi 2

| Señal | Pin físico | GPIO |
| --- | --- | --- |
| TX hacia el LED IR (por el 2N2222A) | 8 | GPIO14 |
| RX desde el comparador LM311 | 10 | GPIO15 |
| LED TX (verde) | 16 | GPIO23 |
| LED RX (rojo) | 18 | GPIO24 |
| Botón de pánico (a GND, pull-up interno) | 11 | GPIO17 |

Todo lo que llega a un GPIO va a 3.3 V, nunca a 5 V. El circuito está en `docs/hardware/circuito-faro.html` y las mediciones en `docs/hardware/bitacora-pruebas-multimetro.md`.

## 1. Preparar cada Raspberry (una vez)

Activar la UART de hardware y quitar la consola serie:

1. `sudo raspi-config nonint do_serial_hw 0`
2. `sudo raspi-config nonint do_serial_cons 1`
3. `sudo usermod -aG dialout,gpio $USER`
4. `sudo reboot`

Si `raspi-config` no tiene esas opciones (versiones viejas), se hace a mano en `sudo raspi-config` → Interface Options → Serial Port: consola "No", hardware "Sí". En la Pi 2 la UART queda en `/dev/ttyAMA0`.

Instalar dependencias (con apt, para no compilar PyNaCl en la Pi 2):

1. `sudo apt update`
2. `sudo apt install -y git python3-nacl python3-serial python3-gpiozero python3-pytest`
3. `git clone <URL-del-repo> faronet`
4. `cd faronet`

En una PC (Windows, Linux o Mac) basta con:

1. `python -m venv .venv`
2. `.venv\Scripts\activate` (Windows) o `source .venv/bin/activate` (Linux/Mac)
3. `pip install -r requirements.txt`

## 2. Probar todo sin hardware

1. `python -m pytest tests`
2. `python -m app.demo_chat`
3. `python -m mesh.demo_nodo`
4. `python -m mesh.demo_onion`

`tests/test_nodo_robusto.py` incluye dos comunidades UDP unidas por un Faro simulado.

## 3. Probar el Faro

Primero las mediciones con multímetro de la bitácora. Después, con los dos Faros apuntándose:

Prueba rápida de texto. La Pi B imprime su dirección física y la Pi A le manda un mensaje confirmado con ACK (`ffffffff` lo manda a difusión, sin ACK):

1. `python3 -m faro.demo_recibir --uart /dev/ttyAMA0`
2. `python3 -m faro.demo_enviar --uart /dev/ttyAMA0 --destino DIRECCION_DE_B --mensaje "hola faro"`

Tasa de error de bit (BER) a 0.5 m, 1 m y 2 m (en la Pi B y luego en la Pi A):

1. `python3 -m faro.medir recibir --uart /dev/ttyAMA0 --tramas 200 --distancia 1.0`
2. `python3 -m faro.medir enviar --uart /dev/ttyAMA0 --tramas 200`

Tasa efectiva con ACK (en la Pi B y luego en la Pi A):

1. `python3 -m faro.medir eco --uart /dev/ttyAMA0`
2. `python3 -m faro.medir tasa --uart /dev/ttyAMA0 --tramas 100 --distancia 1.0`

Los resultados van en el Apéndice B del RFC. Para probar otra velocidad se agrega `--baudios 19200` en los dos lados.

Sin hardware se usa `--udp PUERTO --vecino 127.0.0.1:OTRO` en lugar de `--uart`.

## 4. Desplegar el Worker

1. `cd worker`
2. `npm install`
3. `npx wrangler login`
4. `npx wrangler d1 migrations apply faronet-db --remote`
5. `npx wrangler deploy`

Si la base es nueva, antes del paso 4 se corre `npx wrangler d1 create faronet-db` y se pega el `database_id` en `wrangler.jsonc`.

La llave pública del gateway se carga como secreto. No va en el repositorio. La imprime el gateway al arrancar (paso 5):

1. `npx wrangler secret put GATEWAY_PUB`

Pruebas del Worker (corren en workerd local, sin cuenta):

1. `npx vitest run`
2. `npx tsc --noEmit`

Para desarrollo local: copiar `.dev.vars.example` a `.dev.vars`, poner la llave y correr `npx wrangler dev`. `python3 tools/prueba_buzon.py` prueba el buzón contra `localhost:8787`.

## 5. Levantar la red

La cebolla necesita al menos 5 candidatos a relay, así que la red debe tener 7 nodos o más. Una misma PC puede correr varios nodos, cada uno con su puerto y su carpeta.

Comunidad A. En la Pi A (192.168.1.10), que también es el Faro hacia la comunidad B:

1. `python3 -m mesh.nodo --puerto 6001 --ip-publica 192.168.1.10 --uart /dev/ttyAMA0 --carpeta ~/.faronet`

Gateway hacia el Worker, en la misma Pi A o en otra máquina de la comunidad A:

1. `python3 -m gateway.gateway --puerto 6100 --ip-publica 192.168.1.10 --semilla 192.168.1.10:6001 --carpeta ~/.faronet-gw --worker https://faronet-worker.TU-CUENTA.workers.dev`

Nodos extra en una PC de la comunidad A (192.168.1.20), uno por terminal:

1. `python -m mesh.nodo --puerto 6002 --ip-publica 192.168.1.20 --semilla 192.168.1.10:6001 --carpeta ~/.faronet-2`
2. `python -m mesh.nodo --puerto 6003 --ip-publica 192.168.1.20 --semilla 192.168.1.10:6001 --carpeta ~/.faronet-3`

Comunidad B. En la Pi B (otra red, por ejemplo 10.0.0.10), unida a la A solo por luz:

1. `python3 -m mesh.nodo --puerto 6001 --ip-publica 10.0.0.10 --uart /dev/ttyAMA0 --carpeta ~/.faronet`

El chat corre su propio nodo. En cualquier máquina:

1. `python -m app.chat --nodo 192.168.1.20:7001 --alias ana --semilla 192.168.1.10:6001 --carpeta ~/.faronet-ana`

Comandos del chat:

| Comando | Qué hace |
| --- | --- |
| `/nodos` | Lista los nodos conocidos (ID = primeros 8 hex) |
| `/priv ID texto` | Mensaje privado por 3 relays |
| `/unirse tema frase-secreta` | Entra a un tema privado (frase de 8 caracteres o más) |
| `/tema tema texto` | Mensaje a los miembros del tema |
| `/publico tema texto` | Sale al Worker por un gateway: `https://.../sala/tema` y `https://.../feed/tema.atom` |
| `/panico` | Borra llaves y estado, genera identidad y dirección nuevas |
| `/ayuda`, `/salir` | Ayuda y salir |

En la Raspberry, el botón de GPIO17 hace lo mismo que `/panico`.

## Qué falta

Solo la parte física:

1. Soldar los dos Faros.
2. Hacer las mediciones con multímetro.
3. Medir tasa y BER con `faro.medir` y llenar el Apéndice B del RFC.
4. Tomar las fotos.
5. Completar `docs/bitacora/horas.md`.
