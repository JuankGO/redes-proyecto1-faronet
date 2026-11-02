# Manual de ejecución y demostración

Los comandos se ejecutan desde la raíz del repositorio, salvo donde se indica
`worker`. Usar terminales diferentes para procesos que deben permanecer activos.
Las direcciones IP de los ejemplos son de laboratorio; reemplazarlas por las de
la red propia. Ningún resultado esperado de esta guía se considera una medición.

## 1. Preparar cada Raspberry

Grabar Raspberry Pi OS Lite de 32 bits en la microSD con Raspberry Pi Imager,
configurar usuario y SSH y conectar Ethernet. La Pi 2 no incorpora WiFi; si se
usa WiFi hace falta un adaptador. No se flashea un firmware adicional: Python
controla los GPIO desde Linux.

```bash
sudo apt update
sudo apt install -y git pigpiod python3-pigpio python3-nacl python3-serial python3-gpiozero python3-pytest
sudo systemctl enable --now pigpiod
git clone https://github.com/JuankGO/redes-proyecto1-faronet.git faronet-juank
cd faronet-juank
pigs t
python3 -m pytest tests -q
```

`pigs t` devuelve un contador si pigpiod responde. El montaje usa TX GPIO17 y RX
GPIO27, no `/dev/serial0` ni `/dev/ttyAMA0`. No habilitar la consola serie para
estas pruebas. Conectar o modificar las placas solo con la alimentación retirada.

Si ya hay una copia parcheada con cambios locales, conservarla. Clonar esta
entrega en otra carpeta y usar esa carpeta en los comandos, en vez de forzar un
`git pull` o descartar modificaciones.

## 2. PC, SSH y pruebas sin hardware

```bash
python -m pip install -r requirements.txt
python -m pytest tests -q
python -m app.demo_chat
python -m mesh.demo_nodo
python -m mesh.demo_onion
python demo_mesh_chat.py
```

Las demos y el Faro simulado usan sockets locales. No prueban luz ni soldaduras.
Para controlar las Raspberry desde dos ventanas del PC:

```bash
ssh faro-a@faro-a.local
ssh faro-b@faro-b.local
```

Cada línea va en una ventana distinta. Si mDNS no resuelve, consultar `hostname -I`
en cada Raspberry y sustituir el nombre por su IP. SSH transporta los comandos;
un mensaje enviado mediante `--uart pigpio` debe cruzar por luz.

## 3. Verificar un Faro

Completar primero continuidad y ausencia de cortos de la bitácora de multímetro.
Para la prueba estática, no dejar otro programa usando los GPIO:

```bash
pigs modes 27 r
pigs modes 17 w
pigs w 17 0
pigs r 27
pigs w 17 1
pigs r 27
pigs w 17 0
```

Con el emisor y detector de esa placa enfrentados se espera 1 con IR apagado y 0
con IR encendido. Si la entrada solo cambia al activar `pud`, revisar la conexión
RX, el pull-up externo y los voltajes. Una entrada flotante no demuestra recepción.

Prueba de tramas en la misma placa:

```bash
python3 -m faro.medir loopback --uart pigpio --baudios 300 --tramas 5
```

Esperado: cinco tramas `OK`, cero bits distintos y BER cero. No forzar las patas
soldadas para enfrentarlas; planear la orientación o probar con el otro Faro.
Para detener un programa: Ctrl+C. Si queda un lector abierto después de un error,
detener primero todos los programas del Faro y ejecutar `pigs slrc 27`; si indica
que no estaba abierto, no hay lector que liberar.

## 4. Medir dos Faros

Alinear IR A con PT333 B e IR B con PT333 A. Evitar luz del emisor propio en cada
detector. Ambas Raspberry usan los mismos GPIO y baudios. No deben compartir
alimentación de placas ni estar unidas por señales TX/RX eléctricas.

Primero en B:

```bash
python3 -u -m faro.medir recibir --uart pigpio --baudios 300 --tramas 100 --espera 120 --distancia 0.01
```

Después en A:

```bash
python3 -u -m faro.medir enviar --uart pigpio --baudios 300 --tramas 100 --pausa 1
```

La pausa de un segundo supera los 20 tiempos de byte que usa el receptor para
separar ráfagas a 300 baudios. Sin esa pausa puede interpretar varias tramas como
una sola señal. No enviar más de 256 tramas por ejecución de BER: SEQ tiene un
byte y el receptor cuenta una sola vez cada secuencia.

Repetir a 0,02 m y 0,05 m y luego intercambiar A y B. Son tres distancias de
referencia para el procedimiento, no tres resultados ya obtenidos. A 300 baudios
100 tramas máximas y pausas tardan aproximadamente 17 minutos. Para ensayar antes,
usar diez tramas en ambos extremos. Mantener luz ambiental normal y registrar
hora, iluminación, separación, alineación y resistencia del receptor.

Para tasa útil con confirmación, primero en B:

```bash
python3 -u -m faro.medir eco --uart pigpio --baudios 300
```

Después en A:

```bash
python3 -u -m faro.medir tasa --uart pigpio --baudios 300 --tramas 20 --espera-ack 10 --distancia 0.01
```

Detener el eco al terminar. Repetir a las otras dos distancias y en el sentido
contrario. Registrar bytes confirmados, tiempo y reintentos, no solo baudios.
Un metro se requiere para competir por el extra de velocidad, no para las tres
distancias obligatorias. Si se busca el extra, agregar esa medición real.

## 5. Enviar texto de prueba

Primero en B:

```bash
python3 -u -m faro.demo_recibir --uart pigpio --baudios 300
```

En A:

```bash
python3 -u -m faro.demo_enviar --uart pigpio --baudios 300 --destino ffffffff --mensaje "Hola B, soy el Faro A"
```

«Enviado a difusión» solo confirma que A transmitió. B debe mostrar `Recibido de`
y el texto para acreditar entrega. Para ACK, sustituir `ffffffff` por la dirección
de ocho dígitos hexadecimales que imprime B. No usar la IP como destino físico.

Para responder, detener con Ctrl+C el receptor B, iniciar `demo_recibir` en A y
ejecutar `demo_enviar` en B. No ejecutar ambos programas a la vez en una misma Pi.
Estas demos envían texto de diagnóstico sin el cifrado de aplicación.

## 6. Chat, mesh y siete nodos

### Prueba funcional corta

Para probar el chat sin hardware, ejecutar sus demos. `--permitir-directo` permite
ensayar con pocos nodos, pero desactiva la exigencia de relays: no acredita el
anonimato solicitado y debe omitirse en la demostración final.

### Topología de referencia con enlace óptico exclusivo

Se proponen dos chats que poseen los Faros, cuatro relays UDP y un gateway: siete
procesos. Los relays y el gateway pueden correr en una PC de la comunidad A.
La comunidad B no debe tener conectividad IP de aplicación hacia A; su único
camino para la mesh es el Faro. SSH de administración no debe convertirse en
semilla, túnel o ruta de datos de la mesh.

En cada terminal definir las IP de laboratorio que correspondan:

```bash
IP_A=192.168.10.10
IP_B=192.168.20.10
IP_PC=192.168.10.20
```

En la Raspberry A:

```bash
python3 -m app.chat --nodo "$IP_A:7001" --alias faro-a --uart pigpio --baudios 300 --semilla "$IP_PC:7101" --carpeta ~/.faronet-a
```

En la Raspberry B, sin una semilla IP hacia la comunidad A:

```bash
python3 -m app.chat --nodo "$IP_B:7002" --alias faro-b --uart pigpio --baudios 300 --carpeta ~/.faronet-b
```

En cuatro terminales de la PC, definir IP_A e IP_PC y ejecutar una línea por terminal:

```bash
python3 -m mesh.nodo --puerto 7101 --ip-publica "$IP_PC" --semilla "$IP_A:7001" --carpeta ~/.faronet-r1
python3 -m mesh.nodo --puerto 7102 --ip-publica "$IP_PC" --semilla "$IP_A:7001" --carpeta ~/.faronet-r2
python3 -m mesh.nodo --puerto 7103 --ip-publica "$IP_PC" --semilla "$IP_A:7001" --carpeta ~/.faronet-r3
python3 -m mesh.nodo --puerto 7104 --ip-publica "$IP_PC" --semilla "$IP_A:7001" --carpeta ~/.faronet-r4
```

El séptimo proceso es el gateway de la sección siguiente. Cada proceso tiene su
propia carpeta, incluso si comparte máquina. Antes de enviar, esperar a que el
directorio conozca cinco candidatos además de los dos extremos. El enlace lento
puede retrasar los anuncios y el reensamblado; esta topología es una guía de
reproducción, no una integración óptica ya validada.

Dentro de cada chat:

```text
/nodos
/priv PREFIJO_DEL_ID_DESTINO Hola desde FaroNet
/unirse equipo frase-compartida-larga
/tema equipo Mensaje del tema privado
/publico noticias Mensaje publico de demostracion
/panico
/salir
```

Reemplazar el prefijo por el ID que muestre `/nodos`. Compartir la frase del tema
por un canal aparte. `/panico` borra estado y cambia identidad; comprobarlo con
datos de prueba, no con llaves que se necesiten conservar. El botón físico de
GPIO24 lo ejecuta mientras corre el nodo/chat/gateway con `--uart`.

## 7. Worker implementado, no utilizado en la integración

URL informada: https://faronet-worker.faronet-jimmy-juan.workers.dev

Los pasos siguientes permiten reproducir el despliegue; no implican que el grupo
haya realizado la demostración mesh-gateway-edge. El repositorio contiene código,
migraciones y configuración. Se debe usar el plan gratuito y verificar su vigencia
antes de desplegar. No se despliega automáticamente al generar documentos.

En una PC con Node.js y npm:

```bash
cd worker
npm ci
npx tsc --noEmit
npx vitest run
npx wrangler login
```

Para una cuenta nueva, crear D1 y sustituir `database_id` en `wrangler.jsonc` por
el que devuelva la cuenta; no reutilizar el de otra persona:

```bash
npx wrangler d1 create faronet-db
npx wrangler d1 migrations apply faronet-db --remote
```

Crear la identidad persistente del gateway desde la raíz del proyecto:

```bash
python3 -c "from pathlib import Path; from faro.identidad import cargar_o_crear; firma,_=cargar_o_crear(Path.home()/'.faronet-gw'); print(firma.verify_key.encode().hex())"
```

Copiar únicamente esa llave pública al secreto del Worker. Nunca copiar el archivo
de llave privada. Desde `worker`:

```bash
npx wrangler secret put GATEWAY_PUB
npx wrangler deploy
```

Si se configura el secreto antes de la primera publicación, Wrangler puede crear
el Worker durante ese paso. Usar la URL real que imprima el despliegue. Para
desarrollo local: copiar `.dev.vars.example` a `.dev.vars`, completar la llave
pública y ejecutar `npx wrangler dev`. Ese archivo está excluido de Git.

El séptimo proceso, en la misma PC y con la misma carpeta de identidad creada:

```bash
python3 -m gateway.gateway --puerto 7200 --ip-publica "$IP_PC" --semilla "$IP_A:7001" --carpeta ~/.faronet-gw --worker https://faronet-worker.faronet-jimmy-juan.workers.dev
```

Antes de publicar comprobar que GATEWAY_PUB corresponde a esa carpeta. Probar:

```text
https://faronet-worker.faronet-jimmy-juan.workers.dev/sala/noticias
https://faronet-worker.faronet-jimmy-juan.workers.dev/feed/noticias.atom
https://faronet-worker.faronet-jimmy-juan.workers.dev/directorio
```

Para el buzón local, desde la raíz:

```bash
python3 tools/prueba_buzon.py http://localhost:8787
```

Esperado: depósito 201, primera lectura 200 con descifrado, segunda lectura 404 y
rechazo 413 para tamaño incorrecto. El secreto compartido se genera en memoria.

## 8. Defensa de veinte minutos

| Minutos | Demostración y evidencia |
| --- | --- |
| 0-4 | Mostrar Faros soldados, ambas caras, headers, esquema y multímetro |
| 4-7 | Tramas ópticas y tabla ya medida de BER/tasa a tres distancias |
| 7-11 | Directorio, rutas, tres relays y mensaje privado; cortar luz y comprobar dependencia |
| 11-14 | Tema privado, padding, rotación y pánico con indicadores |
| 14-17 | Mostrar código y pruebas del Worker; aclarar que no se utilizó integrado |
| 17-20 | RFC, bitácoras, limitaciones y preguntas |

No intentar medir cien tramas a tres distancias dentro de la defensa: llevar
resultados previos. Mostrar el estado real del enlace aunque una prueba falle.
