# Plan: corregir y validar la inversión de los sticks analógicos

## Objetivo

Corregir la lectura del eje `ABS_Y` en el driver genérico `adc-joystick` usado
por el DTB Panel 4 de este proyecto y confirmar en Armbian los cuatro ejes,
direcciones, centros y recorridos. El alcance inicial es la R36S probada; no
generalizar los valores a otras unidades o revisiones.

## Evidencia de la prueba guiada

La prueba se hizo en Armbian desde `/dev/input/event2` (`adc-joystick`). El
recolector pidió cada posición y leyó el estado ABS actual. Las lecturas
principales fueron:

| Posición | Eje observado | Valor aproximado |
|---|---|---:|
| Ambos sticks en reposo | `X` / `Y` | `427` / `-514` |
| Izquierdo arriba | `Y` | `-796` |
| Izquierdo abajo | `Y` | `-265` |
| Izquierdo izquierda | `X` | `70` |
| Izquierdo derecha | `X` | `739` (el valor varió durante la captura) |
| Derecho arriba | `RY` | `160` |
| Derecho abajo | `RY` | `808` |
| Derecho izquierda | `RX` | `179` |
| Derecho derecha | `RX` | `853` |
| Ambos sticks en reposo | `RX` / `RY` | `505` / `510` |

Esto confirma que los dos sticks producen cambios en sus cuatro ejes y que la
asignación observada es izquierda `X/Y`, derecha `RX/RY`. Los controles
`Z`, `RZ` y `HAT0X/Y` aparecen en cero y no forman parte de los cuatro canales
analógicos configurados.

## Diagnóstico del eje Y

El DTS configura el canal 2 como `ABS_Y` con `abs-range = <880 80>`, que activa
la inversión en el driver. En el kernel fijado, `drivers/input/joystick/adc-joystick.c`
llama a `adc_joystick_invert(input, i, val)`. La función espera un **código de
eje Linux** para consultar sus límites con `input_abs_get_min/max()`, pero `i`
es el índice del canal. Para este eje, `i = 2` y el código es `ABS_Y = 1`; por
tanto, obtiene los límites del slot `ABS_Z`, no los de `ABS_Y`. La captura de
`Y` negativo es consistente con esa discrepancia.

El perfil configura `poll-interval = <60>`, así que el camino activo es
`adc_joystick_poll()`. La misma llamada a la función de inversión aparece
también en el camino IIO buffer; corregir ambos mantiene coherencia para otros
usuarios del driver.

## Propuesta de implementación

1. **Conservar la evidencia actual.** Mantener las lecturas anteriores como
   prueba de hardware antes del cambio; no usarlas como calibración final.
2. **Preparar un patch kernel separado.** Añadir un patch numerado después de
   `0003-px30-prefer-cru-restart.patch` que pase `joy->axes[i].code` a
   `adc_joystick_invert()` en los dos sitios del driver, en lugar del índice
   `i`.
3. **Integrarlo al build fijado.** Actualizar `scripts/build-armbian.sh` para
   instalar el nuevo patch en `work/armbian-build/userpatches/kernel/r36s-6.18/`;
   conservar las fuentes y digests fijados. No editar solo el árbol de trabajo,
   porque el build debe poder reproducirse desde el repositorio.
4. **Verificar estáticamente.** Confirmar que el patch aplica a la versión de
   kernel fijada y que en ambas rutas la inversión consulta el código del eje.
   Compilar kernel y módulos, revisar que el DTB conserve los cuatro rangos y
   verificar la imagen resultante offline.
5. **Repetir la prueba guiada en una microSD de prueba.** Copiar el recolector
   actualizado y capturar `event2`. En reposo, `Y` debe estar dentro de su
   rango configurado `80–880`; arriba debe bajar respecto al centro y abajo
   subir. Confirmar además `X`, `RX` y `RY`, centro, repetibilidad y que al
   soltar cada stick vuelve cerca del valor de reposo.
6. **Ajustar calibración solo con la corrección probada.** Si los extremos
   quedan fuera de los rangos o el centro deriva, medir varias repeticiones
   antes de tocar `abs-range`, deadzone o fuzz. Registrar cada cambio y volver
   a probarlo.

## Criterios de cierre

- El patch usa el código Linux del eje para obtener los límites de inversión en
  ambos caminos del driver.
- `ABS_Y` ya no genera valores negativos ni queda fuera del rango configurado.
- Los cuatro ejes responden en las direcciones físicas indicadas y vuelven a
  valores de reposo repetibles.
- La imagen compilada pasa verificación offline y la nueva captura se realiza
  en Armbian desde una tarjeta de prueba.
- La documentación separa lecturas anteriores/posteriores al cambio y limita
  las conclusiones a la unidad probada.

## Estado

Plan preparado. La prueba física confirma los cuatro canales y sus posiciones
cardinales en esta unidad. El arreglo del driver, la compilación de una imagen
con el patch y su validación posterior en hardware siguen pendientes.
