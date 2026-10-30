# Plan: validar audio RK817

## Objetivo

Comprobar por separado salida de altavoz, audífonos, detección de jack,
controles del códec y rutas de alimentación declaradas por el DTS candidato.

## Evidencia disponible

- ArkOS y el candidato declaran códec RK817; Armbian detectó la tarjeta ALSA,
  el códec y su mixer.
- El DTS configura rutas de altavoz/audífonos. La detección ALSA por sí sola no
  demuestra que cada ruta física funcione; véanse los resultados de la prueba
  en hardware del 2026-10-28.

## Prueba física en la R36S (2026-10-28)

Unidad R36S-V22, perfil Panel 4 por software, con la imagen Armbian del kernel
6.18.58. Las pruebas controladas se hicieron sin cargador, con `Master` al 79 %
(201/255, −20,12 dB), dispositivo `hw:0,0`, tono seno de 1000 Hz y hasta 8 s
por ejecución. `amixer -c 0 scontents` mostró `Master` estéreo con el mismo
nivel en ambos canales y los controles `Mic Capture Gain` y `Playback Mux`.

| Salida / selección | Resultado observado |
|---|---|
| Parlante interno, `Playback Mux = HP` | Sonó en las pruebas controladas. |
| Parlante interno, `Playback Mux = SPK` | No sonó en dos pruebas consecutivas con el mismo volumen y sin cargador. |
| Audífonos estéreo de 3,5 mm con dos anillos (TRS), `Playback Mux = HP` | Sonaron ambos lados. |
| Primeros audífonos, con conector de cuatro contactos según el usuario, `Playback Mux = HP` | Solo sonó el lado izquierdo. La prueba aislada confirmó que el canal izquierdo suena y el derecho no; los mismos audífonos suenan por ambos lados en otro dispositivo. |
| Segundo par de audífonos de cuatro contactos, `Playback Mux = HP` | Funcionaron bien por ambos canales, según la prueba posterior del usuario. |

La reproducción por el parlante y por ambos canales de audífonos TRS queda
validada para esta unidad e imagen. La diferencia entre `HP` y `SPK` es
reproducible en las pruebas informadas, pero todavía no se ha determinado si se
debe al enrutamiento del DTS/códec o a otra condición de la placa. Como el
segundo par de audífonos de cuatro contactos funcionó por ambos canales, el
fallo del primer par no demuestra un problema del jack de la consola; la causa
específica del fallo de esos audífonos no está identificada.

No se validaron la detección automática del jack, el cambio de ruta al insertar
y retirar audífonos, ni la persistencia de la selección después de reiniciar.
Durante estas pruebas, `Playback Mux = HP` fue la selección que funcionó para
el parlante y los audífonos TRS.

## Pasos

1. En una microSD de prueba, guardar antes de reproducir el inventario ALSA,
   `dmesg` del códec, controles mixer y nodos de jack disponibles.
2. Reproducir una señal de prueba corta y de volumen bajo por altavoz; aumentar
   gradualmente y registrar canal, mixer usado, distorsión y cortes. No empezar
   con tonos de alta amplitud.
3. Repetir con audífonos conocidos. Insertarlos y retirarlos varias veces;
   comprobar detección de jack, silenciamiento/cambio de ruta y regreso al
   altavoz. Anotar si el diseño requiere una tecla o control manual.
4. Comparar los controles y rutas del mixer con la configuración de ArkOS y con
   el esquema/pistas disponibles. Verificar polaridad y GPIO de amplificador o
   jack antes de cambiar el DTS.
5. Si hay fallo, probar una hipótesis por cambio: ruta DAPM, nombre de control,
   GPIO, pinmux o alimentación. Compilar y revisar el DTB de cada imagen.
6. **Pendiente:** repetir después de reinicio y confirmar que las rutas
   persisten sin inicialización manual ni errores del driver.

## Criterios de cierre

- Altavoz, audífonos y detección de jack se describen con resultados separados.
- El cambio de DTB, si se requiere, se apoya en esquema, medición o comparación
  reproducible; la detección ALSA por sí sola no cuenta como prueba de audio.
- La prueba se realiza en la unidad observada y en imagen identificada.

## Estado

Reproducción física validada parcialmente en la unidad probada: parlante
interno y ambos canales de audífonos TRS y de un segundo par de cuatro contactos
funcionan con `Playback Mux = HP`. `SPK` no produjo sonido en dos pruebas
controladas. El primer par de cuatro contactos solo sonó por el canal izquierdo;
ese resultado aislado no señala un fallo del jack. La detección y ruta automática
del jack siguen pendientes.
