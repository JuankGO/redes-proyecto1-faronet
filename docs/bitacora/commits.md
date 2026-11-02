# Reporte de commits de Git

Corte: historial previo al commit de esta entrega, incluyendo la rama que
contenía las pruebas UART retiradas. Los títulos y autores se conservan como
aparecen en Git. El hash del commit documental se consulta en GitHub; no se
intenta incluir un commit dentro de su propio contenido.

## Resumen por autor del historial

| Autor registrado | Commits |
| --- | --- |
| Jimmy Castillo Guzman | 1 |
| Jimmy Castillo Guzmán | 3 |
| JimmyCR1 | 1 |
| JuankGO | 14 |

Los nombres JimmyCR1 y las variantes de Jimmy Castillo corresponden a firmas
distintas del historial; no se convierten automáticamente en horas. Se incluyen
merges y commits de código, por lo que los conteos no miden esfuerzo.

## Detalle

| Commit | Fecha | Autor | Descripción |
| --- | --- | --- | --- |
| 891e5eb | 2026-10-30 | Jimmy Castillo Guzmán | test(faro): scripts de prueba cruda de emisor y receptor por UART |
| c7a3b9b | 2026-10-30 | JuankGO | Merge pull request #4 from JuankGO/faro-simplificado |
| f4538c1 | 2026-10-30 | Jimmy Castillo Guzmán | feat(faro): modo loopback en faro.medir para probar un solo Faro |
| 77cf357 | 2026-10-30 | JuankGO | Merge pull request #3 from JuankGO/main |
| 8a30954 | 2026-10-30 | JuankGO | Merge pull request #2 from JuankGO/faro-simplificado |
| ba70abd | 2026-10-30 | Jimmy Castillo Guzmán | docs(faro): documentar el Faro simplificado sin comparador |
| 1c7e8a9 | 2026-10-26 | Jimmy Castillo Guzman | Merge pull request #1 from JuankGO/ACACHETE |
| f054099 | 2026-10-26 | JimmyCR1 | build(Nuevo): Juank no sabe nada, yo si |
| f9e5990 | 2026-10-17 | JuankGO | Worker de Cloudflare desplegado con D1 y Durable Objects |
| ffdf247 | 2026-10-16 | JuankGO | Integración Mesh + Chat completada |
| ce04044 | 2026-10-15 | JuankGO | Prueba de integracion de la mesh |
| 8ecfa5c | 2026-10-14 | JuankGO | Directorio firmado con TTL y tabla de vecinos |
| 972d72a | 2026-10-12 | JuankGO | Parte 7 completa: identidad, panico y cebolla |
| 55c0558 | 2026-10-12 | JuankGO | Parte 7A: identidad criptografica del nodo (Ed25519 + Curve25519) |
| 386170c | 2026-10-12 | JuankGO | Modelo de amenazas v1 |
| 064cd70 | 2026-10-12 | JuankGO | Demo del medio simulado entre dos Faros |
| fe44373 | 2026-10-12 | JuankGO | Capa 1: trama Faro v1 con CRC, Manchester y DispositivoLuzAdaptador |
| 10139f8 | 2026-10-12 | JuankGO | Estructura inicial del repositorio |
| b77a1c2 | 2026-09-30 | JuankGO | Initial commit |

## Reproducir el reporte

```bash
git log --all --date=short --format="%h %ad %an %s"
git shortlog -s -n --all
git log --all -- tools/emisor.py tools/receptor.py
```

La última orden permite revisar el alta y la retirada de los dos scripts.
Su eliminación no reescribe el historial. Las pruebas oficiales se conservan
como módulos del paquete faro.
