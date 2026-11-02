# Herramientas de FaroNet

Las pruebas del Faro se ejecutan mediante `faro.medir`, `faro.demo_enviar` y
`faro.demo_recibir`, con `--uart pigpio --baudios 300`. Los scripts antiguos
`emisor.py` y `receptor.py` se retiraron.

`prueba_buzon.py` comprueba el buzón local con un blob cifrado de 1024 bytes.
No se usa el despliegue público por defecto.

## Documentación

```bash
python -m pip install -r requirements-docs.txt
python tools/generar_documentacion.py --tectonic tectonic
```

Se requiere Tectonic o una instalación de XeLaTeX. La fuente del informe está
en `docs/latex/documentacion.tex`; las instrucciones completas están en
`docs/latex/README.md`. `--solo-fuentes` prepara las tablas y figuras sin compilar.
`--actualizar-commits` actualiza el reporte desde el historial de Git.

`montaje_faro.py` genera la vista pictórica SVG/PDF usando las redes y posiciones
de `placa_layout.py`. `esquematico.py` conserva la vista eléctrica complementaria.
La validación de conexiones del dibujo no certifica la soldadura física.
