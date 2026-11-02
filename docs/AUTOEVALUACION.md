# Autoevaluación y limitaciones

## Estado de entrega

Se prepararon fuentes LaTeX, manual, RFC, esquema, BOM, bitácoras y PDFs. Las pruebas
locales aprueban 140 casos de Python y 23 del Worker y TypeScript no reporta
errores. No se considera validado el enlace entre placas ni la publicación
desde la mesh al Worker. El grupo indicó que el Worker se hizo, pero no se utilizó.

Se incorporaron cinco fotos: ambas placas juntas, detalle frontal y posterior
individual, protoboard y captura RX=1/0 según TX. El grupo reporta recepción del
100% a 1000 baudios en el prototipo. Las tablas analógicas y de rendimiento se
completan como referencias calculadas, con supuestos explícitos; no son medidas
de multímetro ni un barrido experimental de BER por distancia. Las horas conservan
la reconstrucción aproximada de veinte horas-persona indicada por el grupo.

## Rúbrica del proyecto, escala 0 a 10

Las notas siguientes son una **propuesta de autoevaluación documental** basada
en la evidencia disponible. Ambos estudiantes deben revisarlas antes de entregar.
No son calificaciones del profesor ni presuponen que todas las pruebas físicas
pasaron. El peso corresponde a la rúbrica interna de la página 8 del enunciado.

| Rubro | Peso | Propuesta 0-10 | Justificación |
| --- | --- | --- | --- |
| Hardware soldado, esquema, BOM y pruebas | 25% | 4 | Dos Faros fotografiados, esquema y BOM; sin entrega entre placas en el diagnóstico |
| Capa 1 y DispositivoLuzAdaptador | 10% | 6 | Códec y adaptador probados; loopback de prototipo reportado, sin recepción final acreditada |
| Capas 2 y 3, mesh y directorio | 15% | 8 | Rutas, firma y comunidades probadas por software; demostración por luz no acreditada |
| Privacidad | 10% | 7 | Cebolla, padding y pánico probados por software; botón visible y límites descritos |
| Aplicación anónima | 5% | 8 | Chat y comandos probados por software; no validado todo el recorrido físico |
| Aplicación pública en edge | 25% | 6 | Implementada y probada localmente; no utilizada en la integración |
| RFC | 5% | 9 | ASCII, protocolos, campos, versiones, privacidad y seguridad |
| Documentación | 5% | 8 | Apartados, fotos, captura y cálculos completos, con origen de cada dato identificado |
| TOTAL PONDERADO PROPUESTO | 100% | **62,5/100** | Suma de nota/10 por peso |

La página 2 menciona 30% de valor de la asignación y la página 8 dice «Proyecto
20%». No se resuelve esa diferencia inventando un peso: debe confirmarse con el
profesor. La tabla anterior solo normaliza la rúbrica interna a cien puntos.
No se asignan extras de kick-off ni velocidad. Una reconstrucción de kick-off
no prueba que se entregó cuando correspondía.

## Aprendizaje, escala 1 a 5

Escala del enunciado: 1 muy malo, 2 malo, 3 regular, 4 bueno y 5 muy bueno.
Estas son propuestas para reflexión; cada integrante debe aceptar o corregir
su propia valoración. No son resultados de una encuesta realizada.

| Rubro | Jimmy, propuesta | Juan Carlos, propuesta |
| --- | --- | --- |
| Soldadura y hardware | 4 | 3 |
| Capa física | 4 | 4 |
| Enrutamiento mesh | 3 | 4 |
| Privacidad y anonimato | 4 | 4 |
| Serverless en el edge | 3 | 4 |
| Redacción de RFC | 4 | 4 |

## Problemas y limitaciones

- La conmutación manual del detector no asegura tramas a una velocidad determinada.
- La iluminación, alineación, reflejos y conexiones del pull-up afectan el margen de RX.
- Una entrada que cambia solo con la resistencia interna puede estar flotante; hay que medir antes de concluir.
- El lector puede quedar ocupado tras una interrupción; se requiere un solo dueño del GPIO.
- El silencio de veinte bytes obliga a separar ráfagas de BER a velocidades bajas.
- La red requiere siete nodos para la política de cinco candidatos y tres relays.
- A 300 baudios la fragmentación y los anuncios de control son lentos; su integración física no está validada.
- El Worker no se utilizó en la demostración, aunque tiene código, configuración y URL informada.
- HELLO/RUTA no están firmados; existe exposición a Sybil y manipulación de rutas.
- El directorio revela direcciones de transporte y la cebolla no elimina correlación global de tiempos.
- El pánico no garantiza borrado forense en microSD ni de todas las copias de memoria.
- El origen de un privado no se autentica solo con la pista que muestra el chat.

El reporte de commits acompaña esta autoevaluación y conserva los autores del
historial. No se usa el número de commits para determinar la nota ni las horas.
