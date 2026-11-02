# Kick-off: reconstrucción del planteamiento inicial

**Nota de alcance:** este documento se reconstruye al preparar la entrega.
No demuestra que se presentó en la clase o fecha exigida. No se solicita por
ello el extra ni se oculta la falta de evidencia de entrega histórica.

## 1. Introducción y estrategia

Construir dos interfaces de comunicación por luz y usarlas para transportar una
red con privacidad. Dividir el trabajo en hardware, códec, mesh, cifrado,
aplicación y edge permite detectar errores antes de integrar todo.

```text
Faro soldado -> tramas con CRC -> mesh -> cebolla y chat
                                      -> gateway -> Worker publico
```

Los privados y temas privados quedan en FaroNet. Solo contenido marcado como
público puede salir al edge. El hardware se prototipa y luego se suelda con
conectores desmontables.

## 2. Ambiente y flujo de trabajo

Raspberry Pi 2 y Raspberry Pi OS; Python para nodos y GPIO; TypeScript con
Wrangler para Cloudflare. PC con Git, editor y terminal. Para el circuito:
protoboard, cautín, estaño, pinzas, placa perforada y multímetro. El debugging
avanza de voltajes y GPIO a tramas y, después, a pruebas de red.

El flujo es implementar una parte, ejecutar sus pruebas, revisar el cambio y
publicar un commit. Las llaves y contraseñas quedan fuera de Git. Los commits
identifican contribuciones, no sustituyen una bitácora de horas.

## 3. Control de versiones

Repositorio del grupo:
https://github.com/JuankGO/redes-proyecto1-faronet

La rama principal concentra la versión de entrega. Se conservaron las
contribuciones del historial. Los scripts crudos de UART se retiran para usar
una sola biblioteca y el mapa GPIO17/27 del montaje actual.

## 4. Diseño inicial y amenazas

El esquema actual está en el anexo de hardware: LED IR y NPN para transmitir,
PT333 con pull-up para recibir, dos indicadores y botón. El componente central
es una Raspberry que ejecuta la aplicación y el control de la placa por GPIO.

Adversarios considerados desde el diseño: un nodo malicioso, un observador
óptico, el operador del gateway y el proveedor del edge. Se proponen cifrado de
extremo a extremo con bibliotecas reconocidas, tres relays, tamaños fijos,
dirección rotable, pánico y TTL. Persisten riesgos de correlación temporal,
colusión, sistema operativo comprometido y recuperación de datos en microSD.

## Resultado posterior

El código de cada capa y las pruebas locales existen. El Worker se implementó
pero el grupo informó que no lo utilizó en la demostración integrada. Las
mediciones de hardware y la comunicación entre placas no se declaran aprobadas
sin evidencia. El informe final desarrolla estas decisiones y limitaciones.
