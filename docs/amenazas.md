# Modelo de amenazas de FaroNet

**Autor:** [Jimmy Castillo, Juan Carlos Gomez]
**Curso:** Redes de Computadoras — Proyecto 1
**Fecha:** [12/10/2026]
**Versión:** 1.1 (ajustada al código final)

## 1. Propósito

Este documento responde, antes de escribir una sola línea de criptografía,
quiénes podrían querer espiar FaroNet, qué podrían ver y qué hacemos para
limitarlos. Todo lo que aquí se decide condiciona el diseño de las Partes 7
a 11 del proyecto, y se traslada casi tal cual a la sección *Privacy
Considerations* del RFC.

La regla es simple: si no sabemos contra quién nos protegemos, no podemos
decir que el sistema es privado.

## 2. Activos a proteger

Un **activo** es algo que tiene valor y que un atacante querría obtener,
modificar o destruir. En FaroNet protegemos cuatro:

- **El contenido de los mensajes.** Lo que el usuario escribe en el chat.
  Es lo más valioso: si se filtra, la privacidad se perdió por completo.
- **Las identidades de los nodos.** Las claves públicas y privadas de cada
  Faro, y la relación entre una clave y una persona real.
- **La dirección física del Faro.** Los 4 bytes que identifican a cada
  dispositivo en la mesh. Si alguien la asocia a un usuario, puede seguirle
  el rastro.
- **El grafo de comunicaciones.** Quién habla con quién y cuándo. Aunque
  no se lea el contenido, saber que A y B se escriben ya es información
  sensible.

## 3. Adversarios considerados

Consideramos cuatro adversarios, ordenados de "menos poderoso" a "más
poderoso". Para cada uno respondemos tres preguntas: qué puede ver, qué
**no** puede ver, y qué hicimos para limitarlo.

### 3.1 Nodo malicioso de la mesh

Un nodo que participa en la red pero coopera con un atacante. Puede ser
el relay que recibe nuestra celda.

| | |
| --- | --- |
| **Qué puede ver** | Quién le pasó la celda, a quién debe pasársela, la hora y el tamaño del mensaje. |
| **Qué NO puede ver** | El contenido del mensaje. El origen y el destino final **a la vez**, salvo que los tres nodos del circuito sean suyos. |
| **Defensa** | Cebolla de 3 saltos: cada relay abre solo su capa y ve únicamente el siguiente salto. Cifrado con claves públicas. Celdas de tamaño fijo (1024 bytes) para que el tamaño no delate cuánto se dijo: cada relay vuelve a rellenar la celda con bytes aleatorios hasta 1024 antes de reenviarla. Solo se arma la cebolla si hay al menos 5 candidatos a relay (si no, `SaltosError`). Paquetes mal formados se descartan sin tumbar el nodo. |

### 3.2 Observador del medio físico

Alguien que ve la luz del Faro: con una cámara, un fotodiodo o desde un
punto cercano. Está fuera de la red, solo mira el canal.

| | |
| --- | --- |
| **Qué puede ver** | Que hay una transmisión, cuándo ocurre y cuánto dura. Las direcciones físicas de las tramas (van en la cabecera, sin cifrar). |
| **Qué NO puede ver** | El contenido de los mensajes, porque viajan cifrados en capas. |
| **Defensa** | Cifrado de la celda completa antes de partirla en tramas. Direcciones físicas **rotables** con `direccion.rotar()` (el nodo avisa con un BEACON): no son permanentes. Celdas de 1024 bytes partidas siempre en los mismos 10 fragmentos, así todos los mensajes producen la misma ráfaga sin importar cuánto texto llevan. |

### 3.3 Operador del gateway

La persona que administra la Raspberry que hace de puente entre la mesh y
el Worker de Cloudflare. Es el eslabón más peligroso porque ve ambos mundos.

| | |
| --- | --- |
| **Qué puede ver** | Los mensajes marcados como **públicos** que salen a internet (es el destino final de esa cebolla, así que los lee en claro). Que existe tráfico hacia el Worker, y aproximadamente cuánto. |
| **Qué NO puede ver** | Quién originó el mensaje (la cebolla se descifra solo al final). Los mensajes **privados**, que nunca cruzan el gateway. |
| **Defensa** | `gateway/gateway.py` solo reenvía mensajes con `VISIBILIDAD = público` y con el TEMA que corresponde al nombre; lo demás lo descarta y lo cuenta en `ignorados`. El emisor llega al gateway por 3 relays, así que el gateway no sabe quién escribió. El chat elige un gateway al azar entre los que se anuncian con `rol: gateway` en el directorio. |

### 3.4 Proveedor del edge (Cloudflare)

La empresa que ejecuta el Worker en sus servidores. Es un adversario
poderoso porque ve el tráfico a nivel de red.

| | |
| --- | --- |
| **Qué puede ver** | La IP del gateway, la hora de las peticiones, los tamaños, los mensajes **públicos** (porque son públicos) y el directorio público de nodos, que incluye la IP:puerto de cada nodo UDP. |
| **Qué NO puede ver** | El contenido del buzón muerto, siempre que quien deposita suba una celda ya cifrada (el Worker solo exige 1024 bytes y un ID de 64 hex; no puede comprobar que esté cifrada). Quién escribió cada mensaje: el Worker no guarda identidad ni IP. |
| **Defensa** | El Worker **no guarda** `CF-Connecting-IP` ni `User-Agent`: la IP solo se usa en memoria como llave del límite de peticiones y ninguna tabla de D1 tiene columnas de IP (hay una prueba que lo verifica). Los blobs del buzón tienen TTL y se borran en la misma operación en que se leen (`DELETE ... RETURNING`). El código no hace `console.log` de encabezados. La observabilidad del Worker está apagada. La autenticación del gateway usa firma Ed25519 sobre método, ruta, hora, nonce y SHA-256 del cuerpo, con ventana de ±60 s y nonces de un solo uso: nadie más puede publicar ni repetir una petición vieja. Las entradas del directorio se verifican con la firma de cada nodo antes de guardarse. Los mensajes públicos vencen a los 7 días y un cron borra todo lo vencido cada hora. |

## 4. Qué NO protegemos

Un buen modelo de amenazas también dice sus límites. Si ocultamos las
debilidades, el documento no sirve.

- **Análisis de tráfico global.** Un adversario que observe **toda** la red
  a la vez y compare horas de entrada y salida de las celdas podría
  correlacionar mensajes aunque no lea su contenido. No lo resolvemos por
  completo. Mitigamos con tamaños fijos y TTL cortos, pero no es suficiente.
- **Cloudflare ve las IPs.** Aunque nuestro Worker no las guarde, Cloudflare
  sí las ve en su propia infraestructura antes de que el código las reciba.
  El usuario debe asumir que el proveedor del edge conoce la IP del gateway.
- **Robo físico del Faro.** Si alguien se lleva una Raspberry, puede leer las
  llaves guardadas en disco. El botón de pánico (GPIO17 o `/panico`) sobrescribe
  con ceros y borra las llaves, crea una identidad y una dirección nuevas y
  vacía las tablas en memoria, pero solo ayuda si el dueño lo activa **antes**
  de perder el control del dispositivo. Además, en una microSD la
  sobrescritura no garantiza que el dato viejo desaparezca (la tarjeta reparte
  las escrituras entre celdas distintas). No hay cifrado a nivel de disco.
- **Compromiso del sistema operativo.** Si el atacante tiene acceso root a
  una de las Raspberry, puede leer las llaves en memoria y suplantar al
  nodo. Asumimos que el sistema operativo no está comprometido.
- **Ataques de denegación de servicio.** Un atacante puede saturar la mesh o
  el Worker. No lo prevenimos; a lo sumo limitamos peticiones por cliente
  en el Worker (429).
- **Correlación por horario de escritura.** Si dos usuarios se escriben
  siempre a la misma hora, un observador puede inferir la relación. No lo
  ocultamos.
- **El emisor de un privado no está autenticado.** El campo TEMA de un
  mensaje directo lleva una pista del emisor (`dm:` + su ID), pero no va
  firmada: cualquiera puede poner la pista de otro. Por eso el chat la muestra
  como "posible emisor, no verificado".
- **Frases de tema débiles.** La llave de un tema sale de su frase con
  Argon2id; una frase corta o común se puede adivinar sin conexión. El chat
  exige al menos 8 caracteres, pero la fuerza real depende del grupo.
- **El directorio público revela IPs de la mesh.** Quien lea `/directorio`
  ve la IP:puerto de los nodos UDP (no la de los nodos que solo usan el Faro).
- **Metadatos en el feed público.** Los mensajes públicos son, por
  definición, públicos: cualquiera puede leerlos y correlacionarlos con
  otros mensajes públicos del mismo tema.

## 5. Suposiciones

- Los usuarios **eligen** qué mensajes son públicos y qué mensajes son
  privados. Los privados nunca salen de FaroNet.
- Cada nodo es responsable de **rotar** su dirección física de vez en cuando,
  y de **borrar** sus llaves al final de su vida útil con el botón de pánico.
- El directorio de nodos se publica con **firmas verificables** en un sitio
  no confiable (el edge), pero su integridad se comprueba siempre.
- La red subyacente (UDP dentro de la mesh, HTTPS hacia Cloudflare) ofrece
  al menos integridad, aunque no confidencialidad. La confidencialidad la
  aporta nuestra capa cebolla.
- Ningún algoritmo criptográfico es inventado por nosotros: usamos PyNaCl
  (libsodium) y la API WebCrypto del Worker, que son bibliotecas
  reconocidas.

## 6. Conclusión

FaroNet protege el **contenido** de los mensajes, la **identidad** de los
nodos y el **grafo** de comunicaciones contra los cuatro adversarios
descritos, dentro de los límites de la sección 4. No es un sistema
anónimo perfecto: es un sistema **honesto** sobre lo que sí y lo que no
puede garantizar. Las decisiones de diseño de las Partes 7 a 11 se
justifican contra este modelo.