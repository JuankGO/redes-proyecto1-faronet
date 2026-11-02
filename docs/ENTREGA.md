# Lista de entrega y trazabilidad del enunciado

Fuente: «Proyecto 1 - FaroNet», septiembre de 2026. La columna de evidencia
identifica implementación y documentos; no convierte un requisito en aprobado.
«Pendiente físico» significa que falta demostrarlo o adjuntar el registro.

## Requisitos funcionales

| Requisito y página | Evidencia o ubicación | Estado al corte |
| --- | --- | --- |
| Emisor, receptor y acondicionamiento, p.3 | Esquema y BOM, GPIO17/27 y PT333 | Documentados; validación física pendiente |
| Indicadores y botón físico, p.3 | `faro/gpio.py`, TX22/RX23 y botón24 | Código presente; prueba integrada pendiente |
| Placa soldada y headers desmontables, p.3 | Foto de componentes y esquema J1 | Evidencia parcial; no usar protoboard en revisión final |
| Esquemático y BOM en colones, p.3 | SVG, conexiones y BOM | Preparados; precios orientativos |
| Fotos de ambas caras, p.3 | Índice de fotografías | Faltan vistas finales de A y cobre de B |
| Continuidad, cortos y voltajes, p.3 | Bitácora de multímetro | Procedimiento listo, mediciones pendientes |
| Trama máxima 128 B, CRC y versión, p.4 | `faro/frame.py`, RFC 2 | Pruebas software |
| Biblioteca DispositivoLuzAdaptador, p.4 | `faro/dispositivo_luz_adaptador.py` | Implementada y probada por software |
| Acceso al medio, p.4 | Espera de silencio y backoff | Implementado; no elimina toda colisión |
| Dirección física persistente y rotable, p.4 | `faro/direccion.py`, `mesh/nodo.py` | Implementada y probada por software |
| BER y tasa a tres distancias, p.4 | Bitácora de pruebas y RFC, apéndice B | Pendiente medir |
| Ethernet/WiFi y Faro, p.4 | UDP y `mesh/enlace_faro.py` | Software probado; puente óptico pendiente |
| Comunidades unidas exclusivamente por Faro, p.4 | Test de dos comunidades y topología del manual | Simulado; falta prueba física sin ruta alternativa |
| Enrutamiento dinámico, p.4 | `mesh/rutas.py`, `mesh/nodo.py` | Pruebas software |
| Directorio con entradas firmadas, p.4 | `mesh/directorio.py` | Pruebas de firma, estructura y TTL |
| Modelo de amenazas, p.4 | `docs/amenazas.md`, informe y RFC 7 | Documentado |
| Anonimato del origen y tres saltos, pp.4-5 | `mesh/onion.py`, `saltos.py` | Software probado; límites explícitos |
| Cifrado con biblioteca reconocida, p.5 | PyNaCl y WebCrypto | Implementado; sin primitivas propias |
| Padding a tamaño fijo, p.5 | Celda1024 y mensaje256 | Pruebas software |
| Botón de pánico, p.5 | Borrado lógico, renovación y parpadeo | Pruebas software; validar hardware |
| Sin bitácoras de usuarios y TTL, p.5 | Tablas acotadas, limpieza y Worker | Implementado; directorio operativo expone direcciones |
| Chat privado y temas privados internos, p.5 | `app/` y filtro del gateway | Pruebas software |
| Relay autenticado HTTPS/WSS, p.5 | `gateway/`, Ed25519 y nonce | Implementado; no utilizado integrado |
| Salas DO/WebSockets y feed Atom, p.5 | `worker/src/index.ts` | Pruebas locales aprobadas |
| Buzón opaco cifrado, fijo, TTL y borrado, p.5 | Endpoint y `tools/prueba_buzon.py` | Pruebas locales aprobadas; cifra el cliente |
| Directorio público verificable, p.5 | `/directorio` y firmas | Pruebas locales |
| Rate limiting y no registro, p.5 | Binding LIMITE, D1 y observabilidad apagada | Código y pruebas; no se afirma invisibilidad al proveedor |
| Despliegue reproducible sin secretos, p.6 | Wrangler, migraciones y manual | Configuración presente; Worker no utilizado |
| RFC ASCII de Faro y FaroNet, p.6 | `docs/rfc/rfc-faronet.txt` | Fuente y PDF |
| Trama externa y longitudes declaradas, p.6 | `enviar_crudo`, LEN y cabeceras | Pruebas software |
| Parámetros por terminal, p.6 | argparse de nodos, chat y herramientas | Implementado |

## Documentación y administración

| Entregable, pp.7-8 | Ubicación | Estado |
| --- | --- | --- |
| Introducción, ambiente y diseño | Informe, secciones 1-3 | Preparado |
| Funciones y estructuras | Informe y API | Preparado |
| Comandos concretos | Manual | Preparado |
| Actividades, fechas, horas y totales por estudiante | Bitácora de horas | Reconstrucción estimada de 20 h-persona |
| Estado, limitaciones y commits | Autoevaluación y reporte de Git | Preparado |
| Rúbrica 0-10 y aprendizaje 1-5 | Autoevaluación | Propuesta para revisión del grupo |
| Lecciones y bibliografía | Informe, secciones 8-9 | Preparado |
| Código documentado | Docstrings y API | Presente |
| LaTeX/ASCII y PDFs | `docs/latex/`, `docs/rfc/` y `output/pdf/` | Generados desde fuentes |
| URL pública | Manual e informe | Informada, no usada en demostración |
| Kick-off | `KICKOFF.md` | Reconstruido; no acredita entrega histórica |

## Cierre antes de enviar al profesor

- Completar los valores reales de multímetro, no los objetivos de diseño.
- Confirmar ambos sentidos y medir tasa útil y BER a tres distancias reales.
- Adjuntar las cuatro vistas finales de las placas soldadas.
- Revisar y aceptar la distribución estimada de horas y las notas propuestas.
- Mantener explícito que el Worker no se utilizó en la integración.
- Volver a generar los PDFs después de completar evidencias.
- Comprobar que no se suben contraseñas, llaves, `.dev.vars` ni registros de usuarios.
- Llevar el Faro físico, funcionando y soldado; la defensa dura como máximo veinte minutos.

El enunciado asigna cero a hardware si no se presenta soldado, cero si no hay
documentación y cero si el código no compila. El grupo debe revisar el formato
de envío y las fechas de la plataforma; no están fijadas en este PDF.
