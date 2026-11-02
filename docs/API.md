# Estructuras de datos y funciones principales

Los nombres corresponden al código del repositorio. Enteros binarios de varios
bytes usan orden de red, big-endian. Los detalles normativos están en el RFC.

## Faro: formato y línea

`Trama` es una dataclass con `tipo`, `dst`, `src`, `seq`, `payload` y `version`.

| Campo | Tamaño | Regla |
| --- | --- | --- |
| VER | 1 byte | Versión 1; receptor rechaza versiones no soportadas |
| TIPO | 1 byte | DATA=1, ACK=2, BEACON=3 |
| DST y SRC | 4 bytes cada uno | FFFFFFFF es difusión; cero no es identidad asignable |
| SEQ | 1 byte | Secuencia módulo 256; ACK repite la secuencia |
| LEN | 1 byte | Longitud de PAYLOAD, de 0 a 114 |
| PAYLOAD | LEN bytes | Contenido de la capa superior |
| CRC | 2 bytes | CRC-16/CCITT-FALSE de cabecera y contenido |

| Función | Entrada y salida | Error o límite |
| --- | --- | --- |
| `frame.codificar(t)` | Trama a bytes | Valida tamaños de direcciones y contenido |
| `frame.decodificar(crudo)` | Bytes a Trama | `TramaError` por versión, largo o CRC |
| `frame.crc16(datos)` | Bytes a entero de 16 bits | Vector 123456789 produce 29B1 |
| `linea.armar_senal(trama)` | Bytes a lista de medios bits | Añade cuatro AA y SFD D5, luego Manchester |
| `linea.extraer_trama(medios)` | Medios bits a bytes de trama | `LineaError` si no hay pares válidos, sincronización o longitud |

Manchester representa 1 por 01 y 0 por 10. `bits_a_bytes` y `bytes_a_bits`
convierten sin cifrar. Una trama externa construida con Scapy u otra herramienta
debe respetar el mismo formato y CRC; se entrega a `enviar_crudo`.

## Puerto e interfaz DispositivoLuzAdaptador

`Medio` define `enviar`, `recibir`, `ocupado` y `cerrar`. `MedioSimUDP` transporta
medios bits por UDP y `MedioUART` usa un objeto compatible con pyserial.
`--uart pigpio` crea `SeriePigpio` con TX17, RX27 e inversión de recepción.

`SeriePigpio` mantiene un `bytearray` de entrada. Implementa `write`, `flush`,
`read`, `in_waiting`, `reset_input_buffer` y `close`. Sus ondas son generadas por
pigpiod; no dependen de un bucle de Python para cada bit. Agrega 55 hexadecimal
como relleno de transporte, fuera del tamaño de trama. `MedioUART` delimita
ráfagas por un silencio mínimo de veinte tiempos de byte.

| Método del adaptador | Comportamiento |
| --- | --- |
| `enviar(dst, payload, tipo)` | Emite una trama sin esperar ACK; devuelve SEQ |
| `enviar_confiable(dst, payload)` | Espera ACK y reintenta; devuelve bool |
| `enviar_crudo(trama_bytes)` | Valida una trama externa antes de transmitir |
| `recibir(timeout)` | Devuelve DATA/BEACON o None; confirma DATA dirigida y filtra duplicados |
| `cambiar_direccion(nueva)` | Cambia la dirección, vacía duplicados y anuncia BEACON |

El adaptador guarda secuencia, cola `deque` de pendientes, último SEQ por origen
y contadores de enviadas, recibidas, descartadas y reintentos. Estos contadores
son agregados, no una bitácora persistente de usuarios. Una sola hebra usa la
instancia. Los errores de tramas recibidas se descartan; errores de acceso al
puerto deben diagnosticarse antes de ejecutar la mesh.

## Identidad, indicadores y pánico

`identidad.cargar_o_crear(carpeta)` devuelve una SigningKey Ed25519 y una
PrivateKey de cifrado, mediante PyNaCl. Los archivos se escriben con permisos
privados en sistemas que los soportan. `direccion.cargar_o_crear` conserva una
dirección de cuatro bytes; `rotar` genera otra evitando cero y difusión.

`Indicadores` controla TX22 y RX23 y permite parpadeo de pánico. `BotonPanico`
usa GPIO24 con pull-up, antirrebote y bloqueo para evitar llamadas simultáneas.
`panico.panico` sobrescribe y elimina archivos sensibles conocidos. `Nodo.panico`
también vacía tablas y colas, renueva identidad y avisa al cliente. La
sobrescritura lógica no garantiza eliminación física en microSD ni de todas las
copias que el intérprete pudo mantener en memoria.

## Vecinos, rutas y directorio

`TablaVecinos` asocia ID a canal, dirección y última observación. Registra HELLO
de vecinos directos y vence entradas sin actividad. No convierte un anuncio
recibido por un tercero en una vecindad física directa.

`TablaRutas` guarda destino, siguiente salto, costo y vigencia. Aprende vecinos,
mezcla anuncios, evita valores mal formados y olvida rutas vencidas. El infinito
es 16. Es vector de distancias, no un protocolo de consenso ni una garantía de
camino óptimo frente a nodos hostiles.

`Directorio` reúne entradas con versión, ID Ed25519, clave pública de cifrado,
canal, dirección, creación, TTL y rol opcional. `crear_entrada`, `firmar`,
`verificar` y `validar` comprueban estructura, firma y vigencia. `a_bytes` produce
JSON canónico con claves ordenadas y representación ASCII compatible con el
Worker. Se expiran entradas y se consulta a gateways por su rol.

## Celdas, cebolla y fragmentación

`empaquetar_celda` antepone longitud de dos bytes y rellena aleatoriamente hasta
1024. `desempaquetar_celda` valida y recupera contenido. Las primitivas de cifrado
son de PyNaCl. `construir_cebolla` cifra para destino y relays; `abrir_como_relay`
obtiene el siguiente salto, mientras `abrir_como_destino` recupera el mensaje.

`elegir_saltos` usa SystemRandom, excluye origen, destino y duplicados y exige
cinco candidatos para elegir tres relays. Si no los hay lanza `SaltosError`.
`--permitir-directo` es una excepción de pruebas y no ofrece esa propiedad.

`EnlaceFaro` tiene una cola de hasta 256 mensajes y una tabla parcial por origen.
Cada fragmento lleva índice y total de dos bytes cada uno, más hasta 110 de
datos. `fragmentar`, `_recibir_fragmento` y `_purgar` parten, reúnen y vencen
mensajes. El máximo de mensaje es 64 KiB y el timeout parcial es diez segundos
sin actualizar. No incluye un identificador de mensaje independiente: no se
deben intercalar mensajes fragmentados del mismo origen.

`Nodo` coordina socket, tablas, enlace, mantenimiento y recepción con bloqueos y
colas. HELLO y rutas se anuncian periódicamente; dirección y entradas se rotan o
renuevan. Su configuración se recibe de argparse. Los mensajes recibidos viven
una hora y se mantiene un límite de memoria; no se escriben conversaciones a disco.

## Aplicación

`empaquetar_mensaje` crea exactamente 256 bytes: VER1, VIS1, TEMA8, HORA4,
LARGO2, texto y relleno. El máximo de texto es 240 bytes antes del envoltorio de
un tema público. `desempaquetar_mensaje` comprueba tamaño, visibilidad, longitud,
TTL de una hora y tolerancia de reloj. `hash_tema` usa BLAKE2b de ocho bytes.

`Cliente` mantiene alias local, temas y claves en memoria. Ofrece
`enviar_privado`, `enviar_tema`, `enviar_publico`, `recibir_pendientes` y
`olvidar_todo`. `clave_de_tema` deriva una clave con Argon2id de nombre y frase.
El alias y la pista de emisor no constituyen una firma de identidad.
`parsear_comando` valida la sintaxis de `/priv`, `/tema`, `/publico` y pánico.

## Gateway y Worker

`Gateway` consume mensajes, valida visibilidad y tema y encola públicos. Usa
reintentos para errores temporales del edge; privados y contenido inválido no
se publican. `encabezados_firmados` firma la cadena FARONET-GW-1, método, ruta,
timestamp, nonce y SHA-256 del cuerpo. No se implementan primitivas propias.

| Endpoint | Función y control |
| --- | --- |
| POST `/api/relay` | Publicar un mensaje público; firma del gateway |
| POST `/api/directorio` | Recibir entradas y verificar firmas |
| GET `/directorio` | Réplica de lectura con firmas y expiración |
| GET `/sala/tema` | Página del tema |
| GET `/sala/tema/ws` | WebSocket de lectura en Durable Object Sala |
| GET `/feed/tema.atom` | Feed Atom con XML escapado |
| PUT/GET `/buzon/id` | Blob fijo, ID opaco, TTL y eliminación al leer |

D1 conserva `mensajes`, `buzon`, `directorio` y `nonces`, con índices y campos de
expiración. La ventana de firma es de 60 s, nonce 120 s, blob 24 h y públicos
siete días. El cron elimina vencidos. El límite configurado es 60 peticiones por
minuto por clave de cliente; es un parámetro del proyecto, no una cuota del plan.
La aplicación no persiste CF-Connecting-IP ni User-Agent, pero el directorio
incluye direcciones de transporte dentro de las entradas publicadas.

Las pruebas verifican límites y rechazos sin probar anonimato absoluto. La
operación integrada del Worker no se utilizó en la demostración del grupo.
