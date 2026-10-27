# Plan: validar audio RK817

## Objetivo

Comprobar por separado salida de altavoz, audífonos, detección de jack,
controles del códec y rutas de alimentación declaradas por el DTS candidato.

## Evidencia disponible

- ArkOS y el candidato declaran códec RK817; Armbian detectó la tarjeta ALSA,
  el códec y su mixer.
- El DTS configura rutas de altavoz/audífonos, pero no existe evidencia
  registrada de reproducción o detección física correcta en Armbian.

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
6. Repetir después de reinicio y confirmar que las rutas persisten sin
   inicialización manual ni errores del driver.

## Criterios de cierre

- Altavoz, audífonos y detección de jack se describen con resultados separados.
- El cambio de DTB, si se requiere, se apoya en esquema, medición o comparación
  reproducible; la detección ALSA por sí sola no cuenta como prueba de audio.
- La prueba se realiza en la unidad observada y en imagen identificada.

## Estado

Plan preparado. La detección de ALSA está observada; las rutas físicas y el
comportamiento del jack siguen sin validar.
