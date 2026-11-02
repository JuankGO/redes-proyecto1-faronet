# Documentación LaTeX

La fuente de la entrega es `documentacion.tex`. Contiene los apartados exigidos
en las páginas 7 y 8 del enunciado: introducción, ambiente, diseño, estructuras y
funciones, ejecución, actividades por estudiante, autoevaluación, lecciones y
bibliografía. Materiales, fotos y pruebas del Faro se integran en diseño.

`rfc.tex` compila el RFC ASCII por separado. Ambos documentos usan `formato.tex`:
portada centrada basada en la referencia del grupo, sin encabezados ni pies
decorativos y con solo el número de página. La portada no se numera.

Datos de portada: IC-7602, Redes de Computadoras; Jimmy Castillo Guzmán y Juan
Carlos Gómez; profesor Kevin Moraga; 1 de noviembre de 2026; II semestre de 2026.
El logotipo se tomó de la portada de referencia aportada por el grupo.

## Compilar

Con Tectonic instalado, desde la raíz del repositorio:

```bash
python -m pip install -r requirements-docs.txt
python tools/generar_documentacion.py --tectonic tectonic
```

También se puede indicar la ruta al ejecutable con `--tectonic RUTA`.
Tectonic descarga los paquetes necesarios en la primera compilación:
https://tectonic-typesetting.github.io/en-US/

Si se usa XeLaTeX, las tablas y figuras ya están versionadas. Desde esta carpeta:

```bash
xelatex -interaction=nonstopmode documentacion.tex
xelatex -interaction=nonstopmode documentacion.tex
xelatex -interaction=nonstopmode rfc.tex
```

El script copia los resultados a `output/pdf/FaroNet-documentacion.pdf` y
`output/pdf/FaroNet-RFC.pdf`. Los registros de compilación quedan fuera de Git.
No se cambia código del Faro ni se usa el despliegue del Worker al compilar.

## Fuentes de las tablas y figuras

- Materiales: `docs/hardware/BOM.md`.
- Actividades y horas estimadas: `docs/bitacora/horas.md`.
- Commits: tabla preparada a partir del historial; actualizar con `--actualizar-commits`.
- RFC: `docs/rfc/rfc-faronet.txt`, que debe seguir siendo ASCII.
- Montaje: `tools/placa_layout.py` y `tools/montaje_faro.py`.

La vista pictórica del Faro permite reconocer componentes y cables; el esquema
eléctrico se conserva en `docs/hardware/esquematico-faro.svg`. La ilustración no
sustituye las fotografías de ambas caras de las placas que pide el enunciado.
Las referencias analógicas y de rendimiento se identifican como cálculos
aproximados. La captura GPIO aporta lecturas digitales reales; el funcionamiento
del loopback del prototipo a 1000 baudios se atribuye al reporte del grupo.
Las tablas eléctricas se generan desde el registro de referencias y las
fotografías originales están en la carpeta de fotos del hardware.
