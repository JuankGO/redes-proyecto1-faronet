# FaroNet

Proyecto 1 de IC-7602: Redes de Computadoras, TEC, II semestre de 2026.
Integrantes: Jimmy Castillo Guzmán y Juan Carlos Gómez.

Dos Raspberry Pi 2 controlan Faros infrarrojos. Sobre el enlace se implementan
una mesh, mensajes cifrados y un gateway hacia Cloudflare Workers. Las pruebas
de software y las mediciones físicas se reportan por separado.

## Entrega

- [Informe LaTeX](docs/latex/documentacion.tex) e [instrucciones de compilación](docs/latex/README.md).
- [Vista de montaje](docs/hardware/montaje-faro.svg), [esquema eléctrico](docs/hardware/esquematico-faro.svg) y [materiales en colones](docs/hardware/BOM.md).
- [Multímetro](docs/hardware/bitacora-pruebas-multimetro.md), [pruebas](docs/bitacora/pruebas.md), [horas](docs/bitacora/horas.md) y [commits](docs/bitacora/commits.md).
- La autoevaluación y el reporte de commits se incluyen dentro del informe, según el enunciado.
- [RFC ASCII](docs/rfc/rfc-faronet.txt) y [modelo de amenazas](docs/amenazas.md).
- [Documentación PDF](output/pdf/FaroNet-documentacion.pdf) y [RFC PDF](output/pdf/FaroNet-RFC.pdf).

## Montaje actual

| Señal | GPIO BCM | Pin físico |
| --- | --- | --- |
| Alimentación | 3,3 V | 1 |
| Tierra | GND | 6 |
| TX hacia el transistor del LED IR | 17 | 11 |
| RX desde el colector del PT333 | 27 | 13 |
| Indicador TX | 22 | 15 |
| Indicador RX | 23 | 16 |
| Botón a GND | 24 | 18 |

Con luz RX entrega 0 y sin luz 1. Se usa `--uart pigpio`, que invierte RX.
El circuito externo completo usa 3,3 V; no se incluye la variante de 5 V.
Ambos Faros tienen el mismo mapa. No hace falta activar `/dev/ttyAMA0`.

## Inicio en cada Raspberry

```bash
sudo apt update
sudo apt install -y git pigpiod python3-pigpio python3-nacl python3-serial python3-gpiozero python3-pytest
sudo systemctl enable --now pigpiod
git clone https://github.com/JuankGO/redes-proyecto1-faronet.git faronet-juank
cd faronet-juank
python3 -m pytest tests -q
python3 -m faro.medir loopback --uart pigpio --baudios 300 --tramas 5
```

Para el loopback, el IR debe mirar al detector de la misma placa. Si la carpeta
ya existe, revisar `git status` antes de actualizar; no sobrescribir cambios locales.
Para comunicar dos Faros y levantar la mesh seguir [el manual](docs/EJECUCION.md).
Los scripts antiguos `tools/emisor.py` y `tools/receptor.py` se retiran; se usan
los módulos `faro.demo_enviar`, `faro.demo_recibir` y `faro.medir`.

## Organización

| Carpeta | Contenido |
| --- | --- |
| `faro/` | Tramas, CRC, Manchester, GPIO y adaptador |
| `mesh/` | Vecinos, directorio, rutas, cebolla y fragmentación |
| `app/` | Mensajes y chat por terminal |
| `gateway/` | Publicación firmada hacia el Worker |
| `worker/` | Salas, WebSockets, Atom, buzón y directorio |
| `tests/` | Pruebas Python sin hardware |
| `docs/` | Fuentes, evidencias y PDFs |
| `tools/` | Prueba del buzón y generación de documentos |

En PC: `python -m pip install -r requirements.txt` y `python -m pytest tests -q`.
Para reconstruir los PDFs: `python -m pip install -r requirements-docs.txt`
y `python tools/generar_documentacion.py --tectonic tectonic`.

**Worker:** https://faronet-worker.faronet-jimmy-juan.workers.dev
URL informada por el grupo. El Worker se implementó, pero no se utilizó en la
demostración integrada; no se presenta esa integración como aprobada.
No subir contraseñas, llaves ni `.dev.vars`.
