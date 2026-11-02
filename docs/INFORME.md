# FaroNet: documentación del proyecto

**Curso:** Redes de Computadoras, Ingeniería en Computación, TEC.
**Profesor:** Kevin Moraga. **Periodo:** II semestre de 2026.
**Integrantes:** Jimmy Castillo Guzmán y Juan Carlos Gómez.
**Repositorio:** https://github.com/JuankGO/redes-proyecto1-faronet
**Fecha de corte:** 1 de noviembre de 2026.

## Alcance y evidencia

Este documento describe la arquitectura y el uso previsto de FaroNet. Los
ejemplos de operación muestran el resultado esperado cuando las partes están
operativas. Los resultados medidos se distinguen de esos ejemplos. No se
atribuyen voltajes, distancias ni pruebas aprobadas que no se hayan registrado.

Se sigue el enunciado «Proyecto 1 - FaroNet», septiembre de 2026, páginas 3 a 8.
La entrega digital incluye fuentes Markdown, RFC ASCII y ambos documentos en
PDF. No se requiere imprimirlos. El informe desarrolla los nueve apartados
solicitados y los anexos incorporan las tablas y procedimientos completos.

## 1. Introducción

FaroNet reúne un enlace físico construido por el grupo con una red de mensajes
que busca reducir la exposición de contenido y metadatos. Además de enviar
texto, hay que reconocer tramas, detectar errores, encontrar nodos, encaminar
paquetes y definir qué información puede publicarse en Internet.

La solución se divide en un Faro infrarrojo, una mesh con cifrado por capas y
una aplicación de chat. Un gateway puede publicar únicamente mensajes públicos
en un Worker. Los mensajes privados permanecen dentro de FaroNet.

```text
Comunidad A                         Comunidad B
[Nodos UDP] -- [RPi + Faro A] ~IR~ [RPi + Faro B] -- [Nodos UDP]
     |                                                   |
     +----------- mesh con cifrado por capas -------------+
                                                         |
                                                      Gateway
                                                         |
                                                       HTTPS
                                                         |
                                            Worker + D1 + salas
```

Cada Raspberry ejecuta el nodo y controla su placa por GPIO. No se necesita
flashear un microcontrolador aparte. Ethernet o WiFi transportan UDP dentro de
cada comunidad. Para acreditar el puente exclusivo por luz, las comunidades no
deben tener una ruta IP alternativa que evite el Faro.

## 2. Ambiente de desarrollo

| Área | Herramientas y uso |
| --- | --- |
| Hardware | Dos Raspberry Pi 2 Model B, microSD y Raspberry Pi OS de 32 bits |
| Desarrollo | PC, editor de texto o VS Code, Git y GitHub |
| Capa física | Python y pigpio/pigpiod en GPIO17 y GPIO27 |
| Criptografía | PyNaCl/libsodium y WebCrypto Ed25519 |
| Red | Sockets UDP y HTTPS |
| Edge | TypeScript, Node.js, Wrangler, D1 y Durable Objects |
| Pruebas | pytest, Vitest, TypeScript y multímetro |
| Montaje | MB102, placa perforada, cautín, estaño, pinzas y alambre |
| Documentación | Markdown, RFC ASCII y ReportLab para PDF |

El control de versiones conserva cambios por autor, fecha y propósito. Cada
cambio se revisa con `git diff` y las pruebas correspondientes. Los secretos y
registros de usuarios no se incorporan al repositorio. El número de commits no
se usa para calcular horas.

La depuración se separa en lectura estática del detector, recepción de bytes,
tramas válidas con CRC y tráfico mesh. Una lectura 0/1 o un LED encendido no
demuestran una trama recibida. Las evidencias de laboratorio no se convierten
en registros persistentes de tráfico del sistema.

## 3. Diseño

### 3.1 Circuito y conexión al nodo

Cada Faro tiene un LED IR con resistencia de 330 ohmios, un NPN 2N2222A, un
fototransistor PT333, dos indicadores y un botón. GPIO17 controla la base del
NPN mediante 2,2 kiloohmios. Otra resistencia de 10 kiloohmios une base y GND.
El receptor conecta el colector a RX y a 3,3 V mediante 10 kiloohmios; su emisor
va a GND. Un condensador de 100 nF desacopla alimentación y tierra.

RX vale 1 sin luz y 0 con luz. `SeriePigpio` invierte la lectura y produce UART
8N1 por software. Se conservan GPIO17/27 del prototipo. La Raspberry mantiene
su fuente micro-USB normal y la placa toma 3,3 V de su pin 1. La propuesta de
usar 5 V en el emisor no se considera una modificación implementada.

Los headers permiten retirar la Raspberry sin desoldar. El montaje final debe
estar soldado: las fotos de protoboard documentan desarrollo, no sustituyen las
cuatro vistas de los Faros terminados que pide el enunciado.

### 3.2 Protocolo físico

La trama contiene 12 bytes de cabecera, hasta 114 de contenido y 2 de CRC, con
máximo de 128 bytes. Declara versión, tipo, destino, origen, secuencia y longitud.
CRC-16/CCITT-FALSE detecta errores accidentales; no cifra ni autentica frente a
un atacante.

Manchester se aplica al preámbulo, delimitador y trama. Una trama máxima produce
266 bytes UART, más un byte auxiliar de pigpio, sin modificar el límite de 128
bytes de la trama lógica. UART agrega los bits de inicio y parada.

El adaptador espera canal libre y usa retroceso aleatorio. La entrega dirigida
usa ACK y reintentos; la difusión no se confirma. Los duplicados se descartan.
La ocupación se estima con bytes recibidos y silencio, no con un detector
analógico de portadora; pueden existir colisiones.

### 3.3 Mesh, enrutamiento y privacidad

Los nodos anuncian vecinos, intercambian entradas firmadas del directorio y
propagan rutas por costo en saltos. Cada entrada identifica versión, clave,
dirección de transporte y vencimiento. Una firma verifica quién publicó la
entrada, no que cada persona controle una sola identidad.

Se usan celdas de 1024 bytes con relleno y cebolla de tres relays mediante
SealedBox. Cada relay abre una capa y obtiene el próximo salto. El código exige
cinco candidatos distintos del origen y el destino, así que la demostración
anónima requiere siete nodos. Pueden ser procesos separados en una PC, cada
uno con su puerto y carpeta de llaves.

El enlace Faro divide los mensajes en fragmentos de hasta 110 bytes más cuatro
bytes de índice y total. Una celda binaria de 1024 bytes ocupa diez fragmentos.
El sobre JSON que codifica la celda en hexadecimal puede necesitar más; no debe
confundirse su tamaño con el de la celda original.

### 3.4 Aplicación y edge

El mensaje de aplicación mide 256 bytes e incluye versión, visibilidad, tema,
hora, longitud, texto y relleno. El chat distingue privados, temas privados y
mensajes públicos. Argon2id deriva las claves de temas a partir de frases.

El gateway filtra mensajes públicos y firma peticiones HTTPS. El Worker verifica
Ed25519, hora y nonce; implementa salas mediante Durable Objects y WebSockets,
feeds Atom, directorio verificable y un buzón de blobs de 1024 bytes con borrado
al leer y TTL. Su código y configuración están presentes.

URL informada por el grupo:
https://faronet-worker.faronet-jimmy-juan.workers.dev

**El Worker no se utilizó en la demostración integrada.** Tener código, una URL
y pruebas locales no acredita el recorrido mesh-gateway-edge en producción.

### 3.5 Modelo de amenazas

| Adversario | Observa | Defensa y límite |
| --- | --- | --- |
| Relay malicioso | Vecinos, próximo salto y tiempos | Cebolla y padding; la colusión permite correlación |
| Observador óptico | Luz, duración y cabeceras | Cifrado superior y dirección rotable; la demo cruda no es privada |
| Operador del gateway | Públicos y tráfico al edge | Los privados no se exportan; conserva visibilidad de su conexión |
| Proveedor del edge | IP de conexión, tiempos y públicos | La aplicación no registra encabezados; el proveedor sí ve su infraestructura |
| Acceso a microSD o sistema | Llaves y memoria | Pánico y borrado lógico; no garantizan borrado forense en flash |

El directorio conserva direcciones operativas para enrutar. No es una bitácora
histórica, pero expone metadatos. No hay protección completa contra observación
global, Sybil, denegación de servicio o un sistema operativo comprometido.
HELLO y RUTA no están firmados en v1. La pista del emisor de un privado tampoco
autentica su identidad.

## 4. Estructuras de datos y funciones

| Módulo | Estructura o función | Uso |
| --- | --- | --- |
| `faro.frame` | `Trama`, `codificar`, `decodificar`, `crc16` | Formato y validación |
| `faro.linea` | `armar_senal`, `extraer_trama` | Manchester y sincronización |
| `faro.serie_pigpio` | `SeriePigpio` | UART GPIO17/27 invertida |
| `faro.dispositivo_luz_adaptador` | `DispositivoLuzAdaptador` | Canal, ACK y tramas externas |
| `faro.identidad`, `direccion`, `panico` | Llaves y dirección | Crear, rotar y borrar |
| `mesh.vecinos`, `rutas`, `directorio` | Tablas en memoria | Descubrir, encaminar y verificar |
| `mesh.onion`, `celda`, `saltos` | Cebolla y celda fija | Cifrado y selección de relays |
| `mesh.enlace_faro` | Cola y parciales | Fragmentación y reensamblado |
| `app.mensaje`, `cliente`, `comandos` | Mensajes y órdenes | Chat y público/privado |
| `gateway.gateway`, `firma` | Cola y firma | Exportar solo públicos |
| `worker/src/index.ts` | `Sala`, HTTP y cron | Salas, feeds, buzón y limpieza |

El anexo de funciones describe entradas, salidas, errores y límites. El código
conserva docstrings y comentarios; los módulos antiguos de prueba cruda se
retiran para no mantener un segundo mapa de pines.

## 5. Instrucciones de ejecución

El manual anexo contiene los comandos de instalación, pruebas ópticas,
mensajería, mesh y despliegue. El Faro ejecuta Python sobre Linux; no requiere
compilación ni flasheo independiente. Debe existir un único proceso dueño de
GPIO27 en cada Raspberry.

```bash
sudo systemctl enable --now pigpiod
python3 -m pytest tests -q
python3 -m faro.medir loopback --uart pigpio --baudios 300 --tramas 5
```

Las demos de texto del Faro diagnostican el enlace y no reemplazan el chat
cifrado. La demostración completa debe verificar primero hardware y después
mesh, privacidad y publicación.

## 6. Actividades realizadas por estudiante

El grupo estimó unas 20 horas-persona entre ambos durante tres fines de semana.
La bitácora reconstruida distribuye diez horas a cada estudiante en materiales,
montaje, soldadura, código, pruebas e integración. Fechas, reparto y duración
por actividad son aproximaciones para revisión, no un cronómetro histórico.

Se interpretaron los tres fines de semana como 17-18 y 24-25 de octubre y
31 de octubre-1 de noviembre de 2026. Si el grupo se refería a otros fines de
semana, debe corregir las fechas. El registro anterior de 1 h sin autor se
conserva aparte y no se suma a las 20 h para evitar duplicar tiempo.

El anexo contiene una línea por actividad, fecha y horas y suma por integrante.
El reporte Git presenta contribuciones reales; no se utiliza para inventar
horarios ni asistencia.

## 7. Autoevaluación y estado final

El proyecto tiene implementaciones de las capas solicitadas y pruebas de
software. La bitácora identifica cada ejecución y sus resultados. El grupo
reportó un loopback de protoboard estable a 1000 baudios, pero eso no equivale a
medir tasa útil y BER a tres distancias.

En el diagnóstico por SSH del 1 de noviembre no se confirmó el enlace entre
Faros. Se generaron pulsos de salida, pero no se recibió una secuencia útil.
Las entradas medidas requieren revisar acondicionamiento y alineación; la causa
única no está determinada. No se declara como aprobada una comunicación que
solo se describió de forma hipotética.

La autoevaluación anexa cubre la rúbrica 0 a 10 y la escala de aprendizaje 1 a 5.
Sus notas son una propuesta editable que deben validar ambos integrantes. El
Worker figura implementado y probado localmente cuando existe esa evidencia,
pero no utilizado en la integración final.

## 8. Lecciones aprendidas

- Separar lectura estática, bytes, CRC y tráfico de aplicación al depurar.
- Mantener los mismos GPIO y la misma polaridad en código, esquema y manual.
- Confirmar la recepción en el otro equipo; «enviado» no garantiza entrega.
- Reservar margen respecto de la mayor velocidad que pasa una prueba cercana.
- Registrar continuidad y voltajes antes de conectar una placa soldada.
- Aislar el detector del emisor propio y reducir reflejos e iluminación externa.
- Probar por separado criptografía, transporte, aplicación y despliegue.
- Anotar horas y mediciones durante el trabajo, no al final.
- Describir límites de anonimato y borrado en microSD sin prometer seguridad absoluta.
- Preparar la defensa de veinte minutos con comandos y evidencias disponibles.

## 9. Bibliografía

1. Moraga, K. «Proyecto 1: FaroNet», TEC, septiembre de 2026, pp. 3-9. Enunciado del curso.
2. RFC Editor. RFC 7322, *RFC Style Guide*. https://www.rfc-editor.org/rfc/rfc7322
3. RFC Editor. RFC 6973, *Privacy Considerations for Internet Protocols*. https://www.rfc-editor.org/rfc/rfc6973
4. RFC Editor. RFC 8032, *Edwards-Curve Digital Signature Algorithm*. https://www.rfc-editor.org/rfc/rfc8032
5. PyNaCl. https://pynacl.readthedocs.io/en/latest/
6. pigpio, interfaz Python. https://abyz.me.uk/rpi/pigpio/python.html
7. Raspberry Pi, documentación GPIO. https://www.raspberrypi.com/documentation/computers/raspberry-pi.html
8. Cloudflare, Wrangler. https://developers.cloudflare.com/workers/wrangler/commands/
9. Cloudflare, D1 y migraciones. https://developers.cloudflare.com/d1/wrangler-commands/
10. Cloudflare, Durable Objects. https://developers.cloudflare.com/durable-objects/best-practices/rules-of-durable-objects/
11. Historial y código del grupo. https://github.com/JuankGO/redes-proyecto1-faronet
12. Presupuesto histórico del grupo, 13 de octubre de 2026, conservado en `docs/hardware/FaroNet_Materiales.pdf`. La BOM actual distingue los valores del montaje nuevo.
