# Herramientas de apoyo

Las pruebas físicas oficiales se ejecutan como módulos:

```bash
python3 -m faro.medir loopback --uart pigpio --baudios 300 --tramas 5
python3 -m faro.demo_recibir --uart pigpio --baudios 300
python3 -m faro.demo_enviar --uart pigpio --baudios 300 --destino ffffffff --mensaje "hola"
```

No abrir recepción y envío como procesos distintos a la vez en la misma Pi.
`emisor.py` y `receptor.py` se retiraron porque usaban otro puerto y mapa GPIO.

`prueba_buzon.py` prueba el endpoint del buzón con un secreto efímero y un blob
cifrado de 1024 bytes. Su URL por defecto es localhost, no el despliegue público.

## Regenerar la entrega

Desde la raíz del repositorio:

```bash
python -m pip install -r requirements-docs.txt
python tools/generar_documentacion.py
```

En GNU/Linux se necesita una fuente DejaVu Sans, por ejemplo el paquete
`fonts-dejavu-core`. En Windows se usa Arial y Consolas. El programa no modifica
GPIO, no usa SSH y no despliega el Worker.

Produce `output/pdf/FaroNet-documentacion.pdf`, `output/pdf/FaroNet-RFC.pdf` y
actualiza el SVG del esquema desde `esquematico.py`. El informe se compone de
las fuentes listadas en `SOURCES`; el RFC se lee estrictamente como ASCII.

Después de cambiar horas, pruebas, fotos o estado del proyecto, volver a generar
y revisar los PDFs. Las tablas pendientes no se rellenan automáticamente y el
reporte de commits mantiene el corte indicado en su encabezado.
