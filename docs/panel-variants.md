# Comparación de variantes de pantalla de ArkOS

**Fuente:** snapshot local de `/boot/ScreenFiles` y del DTB situado en la raíz de `/boot`, obtenido por SSH el 2026-10-23. Los hashes de los archivos copiados están en [SHA256SUMS](../reference/arkos-r36s/SHA256SUMS).

## Resumen

Las carpetas no son solo nombres alternativos: los `rk3326-r35s-linux.dtb` contienen distintas secuencias de inicialización MIPI-DSI, retardos de reset y parámetros de temporización. Todos los DTB de esta colección declaran el mismo compatible (`elida,kd35t133`, `simple-panel-dsi`), así que la variación parece estar en la programación y temporización de paneles/revisiones dentro de esa familia. El compatible es una declaración del device tree, no una lectura electrónica del identificador del LCD.

| Variante | Etiqueta de `PID.txt` | Diferencias observadas en el DTB `rk3326-r35s-linux.dtb` |
|---|---|---|
| Panel 0 | `PANEL 0 - Original Panel` | Secuencia de inicialización propia. Temporizaciones distintas del grupo 1–4. PWM/backlight usa valores diferentes a los paneles 1–4. Los modos etiquetados 50/75 Hz calculan 50/75 Hz; el de 60 Hz calcula ~61,22 Hz. |
| Panel 1 | `PANEL 1` | Secuencia propia; preparación/reset de 20/150 ms; PWM/backlight distinto de Panel 0. Los tres modos tienen los mismos timings y reloj de 29 MHz: calculan ~68,54 Hz. |
| Panel 2 | `PANEL 3` | Secuencia propia, diferente de Panel 1 y 3; los tres modos tienen los mismos timings y reloj de 29 MHz: calculan ~77,38 Hz. El PID contradice el nombre de carpeta; posible error de etiqueta en ArkOS. |
| Panel 3 | `PANEL 3` | Secuencia propia, distinta de Panel 2; los tres modos tienen los mismos timings y reloj de 29 MHz: calculan ~77,38 Hz. |
| Panel 4 | `PANEL 4` | Secuencia propia; el modo 60 Hz usa 29 MHz y calcula ~59,94 Hz; los modos 50/75 tienen los mismos timings y calculan ~77,38 Hz. El DTB instalado en la raíz de `/boot` tiene el mismo SHA-256 que este archivo. |
| Panel 4 - V22 | `PANEL 4 V22` | Secuencia y temporización distintas de Panel 4; reloj de 58 MHz y timings iguales en los tres modos, que calculan ~78,21 Hz. Su `boot.ini` tiene el mismo contenido lógico que los demás scripts, con finales de línea CRLF. |
| Panel 5 | `PANEL 5 - Soy Sauce Console` | Configuración más divergente: secuencia propia, GPIO adicionales para enable/LED, distintos pines y PWM de backlight, retardos 100/50 ms. Incluye un `Image` y DTB adicionales; hay que verificar qué script los carga antes de inferir su uso. Los modos 50/75 calculan sus frecuencias nominales; el de 60 Hz calcula ~77,67 Hz. |

Las frecuencias anteriores se calcularon como `pixel clock / (total horizontal × total vertical)` usando los valores de cada modo DTB; son resultados de la descripción de software, no mediciones eléctricas ni garantía del refresco visible. En Panel 1, 2, 3 y 4 - V22, los modos llamados 50/60/75 Hz repiten exactamente el mismo conjunto de timings, por lo que las etiquetas no representan tres frecuencias distintas. Panel 4 es la única variante observada en ejecución en esta unidad: DRM reportó `640x480p60`, consistente con su modo Panel 4 `60Hz` calculado a ~59,94 Hz. La inspección comparó datos binarios del DTB, pero no probó físicamente otras variantes.

## Archivos comunes y diferencias de nombres

- Los `rk3326-r35s-linux.dtb` de las carpetas son diferentes entre variantes.
- `rk3326-rg351mp-linux.dtb` tiene el mismo hash en Panel 0–4, al igual que sus copias `.orig` y `.tony`; no distingue esas variantes en este snapshot.
- Los `boot.ini` de Panel 0–5 tienen el mismo hash. El de Panel 4 - V22 es lógicamente igual, pero almacenado con finales de línea CRLF.
- `Panel 2/PID.txt` dice `PANEL 3`, igual que `Panel 3/PID.txt`. No renombrar ni corregir ese dato sin contrastarlo con la fuente de ArkOS y la identificación física.

## Qué indica sobre la consola inspeccionada

El archivo `/boot/rk3326-r35s-linux.dtb` obtenido de la raíz tiene hash `ac546dd7ca90c53c2d6111449b9624fc0d875fbe8b1eeead8a9e25c538b1cd98`, idéntico al de `ScreenFiles/Panel 4/rk3326-r35s-linux.dtb` y distinto del DTB de `Panel 4 - V22`. La línea de comandos observada tenía `panel=unset` y el `boot.ini` carga el DTB de la raíz cuando no hay `PanelNum`. Una lectura directa de `/sys/firmware/devicetree/base` confirmó en el kernel en ejecución los valores de panel descritos abajo. Por tanto, la configuración activa es Panel 4.

Ese DTB declara (y los valores principales se contrastaron con el árbol de dispositivos vivo):

- Compatible: `elida,kd35t133` y `simple-panel-dsi`.
- Resolución: 640×480; 4 lanes DSI.
- Tamaño declarado: 52×70 mm.
- Retardos declarados: reset 150 ms, prepare 20 ms, init 20 ms, enable 120 ms.
- Secuencia de inicialización DSI: 773 bytes (SHA-256 `b98004a555bc0a00ad6cd503f610755b783bd7a772a5f5a68178ff1e43d5193e`).
- `display-timings/60Hz` declara un pixel clock de 29 MHz y `vfront-porch = 165`. Con los totales de línea y cuadro del DTB (732×661), resulta aproximadamente 59.94 Hz, coherente con el modo 640×480p60 observado por DRM.

Esto identifica la **configuración seleccionada en software**, no confirma el identificador impreso en el LCD ni demuestra que Panel 4 sea la selección correcta para futuras imágenes. La consola muestra imagen funcionando con ese DTB, lo que sí confirma compatibilidad operativa básica en ArkOS.

## Lectura del entorno U-Boot

`fw_printenv` está instalado en ArkOS, pero falla porque no existe `/etc/fw_env.config`. Tampoco hay particiones MTD listadas en `/proc/mtd`. No se ha leído ni cambiado el entorno persistente. No se debe adivinar el offset del entorno en la microSD; hace falta identificarlo a partir de la configuración/build de U-Boot concreta antes de intentar leerlo con otra configuración.

## Referencias externas y licencia

- El [repositorio AeolusUX/R36S-DTB](https://github.com/AeolusUX/R36S-DTB) documenta DTB para R35S/R36S y advierte de pantallas nuevas con archivos específicos. Su README declara licencia CC BY-NC-ND 4.0. El snapshot local procede de la instalación ArkOS y aún no se ha demostrado que cada archivo sea idéntico a un archivo concreto de esa publicación; por eso no se considera material autorizado para modificar o redistribuir.
- El archivo público [Panel4-V22.dts](https://github.com/AeolusUX/R36S-DTB/blob/main/DTS/Panel4-V22.dts) es una referencia de fuente legible, pero corresponde a Panel 4 - V22, no al Panel 4 activo en esta consola.
- El proyecto externo [icefirex/nixos-r36s](https://github.com/icefirex/nixos-r36s/tree/60c190db8a3df1aaad10b862c03c00b05b363844) identifica su Panel 4 como NV3051D y reporta que el driver mainline no tiene la secuencia R36S que necesita. Es una pista independiente, no una identificación de nuestra unidad: su propio README dice que solo incluye Panel 4 y utiliza una secuencia/configuración de Panel 4 de ArkOS, un driver genérico DSI de ROCKNIX y un blob precompilado de U-Boot Armbian. No tomamos esa identificación como prueba física ni copiamos sus binarios/init sequence; la procedencia/licencia de dichos assets no queda demostrada por la licencia MIT del repositorio.

## Siguientes pasos de identificación

1. Identificar en la versión concreta de U-Boot/ArkOS dónde se almacena el entorno persistente, para ver si es viable configurarlo para `fw_printenv`; no adivinar offsets ni ejecutar `saveenv` o el selector.
2. Si se abre la consola, fotografiar la serigrafía de revisión/fecha de la PCB y cualquier etiqueta legible del LCD por separado. Una referencia pública con fotos de placas distingue la revisión V12/V21/V30 de la variante de panel y advierte que no hay una tabla de correspondencia confirmada. Ver [análisis de revisión y panel](https://r36s.space/blog/dtb-and-board-revision) y [fotos de PCB](https://r36s.space/inside); son fuentes comunitarias, no una identificación de nuestra unidad.
3. Conseguir/obtener el DTS correspondiente exactamente al DTB Panel 4 y verificar las secuencias y temporizaciones antes de adaptarlas a Armbian.
4. Mantener los DTB y el `Image` de referencia fuera del proceso de compilación hasta confirmar procedencia, licencia y compatibilidad.

## Referencia independiente: `linux-r36s` de Andre Renaud

Se auditó el commit `ba832b723d70318be2bdf65aff344194a807e6f5` de [AndreRenaud/linux-r36s](https://github.com/AndreRenaud/linux-r36s/tree/ba832b723d70318be2bdf65aff344194a807e6f5), que contiene un DTS propio `rk3326-r36s.dts` y un driver R36S en `panel-newvision-nv3051d.c`. El DTS declara SPDX `(GPL-2.0+ OR MIT)` y el driver SPDX `GPL-2.0`. Es una fuente de referencia con licencia explícita, a diferencia de los blobs ArkOS cuya licencia no se ha establecido.

Coincidencias y diferencias con la unidad medida por software:

| Dato | Unidad ArkOS inspeccionada | `linux-r36s` auditado | Lectura |
|---|---|---|---|
| Resolución | 640×480 | 640×480 | Coincide |
| Geometría | 52×70 mm | 70×52 mm | Coincide al intercambiar orientación |
| Pixel clock | 29 MHz declarado por ArkOS | 29 MHz en el modo DRM del driver candidato | Coincide en configuración; no es una medición eléctrica y falta probar la pantalla con Armbian |
| GPIO reset | Según DTB ArkOS | GPIO3 PC0, activo bajo | Revisar contra el DTB de la unidad antes de adoptarlo |
| Controlador declarado | `elida,kd35t133` | `gameconsole,r36s-panel`, asociado a NV3051D | Hipótesis de controlador; no se ha leído ID físico |

El driver separa una secuencia R36S de la secuencia compartida por otros paneles NV3051D. El patch del proyecto porta esa variante bajo GPL-2.0, con atribución, al driver NV3051D que ya está en el kernel Armbian. La comparación encontró que sus 153 registros de dos bytes coinciden exactamente con los del DTB Panel 4 local; los comandos DCS finales tienen diferencias de codificación/retardo, detalladas en [`r36s-dts-audit.md`](r36s-dts-audit.md). Esto respalda la adaptación de software a esta unidad, pero no lee el ID físico ni valida la temporización en funcionamiento. El modo DRM del patch usa los 29 MHz declarados por ArkOS y geometría 70×52 mm.

La copia de auditoría está en `/tmp/r36s-linux-custom-audit` (fuera del árbol de producto). Se conserva el DTS exacto con licencia en `device-trees/reference/`; el patch con la adaptación propia se aplica al build Armbian. Referencias de código: [DTS R36S](https://github.com/AndreRenaud/linux-r36s/blob/ba832b723d70318be2bdf65aff344194a807e6f5/arch/arm64/boot/dts/rockchip/rk3326-r36s.dts) y [driver NV3051D](https://github.com/AndreRenaud/linux-r36s/blob/ba832b723d70318be2bdf65aff344194a807e6f5/drivers/gpu/drm/panel/panel-newvision-nv3051d.c).

### Orden recomendado para continuar

1. Arrancar la imagen Panel 4 en una microSD de prueba con UART. Confirmar SPL/U-Boot y consola serial antes de diagnosticar la pantalla.
2. Si llega a terminal, probar pantalla, controles, audio, batería/carga, microSD y apagado de forma separada; contrastar cada GPIO/regulador del DTS con el comportamiento real.
3. Si el LCD no enciende o muestra artefactos, capturar los logs y revalidar panel/timings antes de cambiar la secuencia. No asumir que las demás unidades R36S usan este panel.
4. No sobrescribir la tarjeta ArkOS ni el entorno persistente de U-Boot.

La auditoría comparativa está en [`r36s-dts-audit.md`](r36s-dts-audit.md). El patch ya integra el DTB y driver R36S Panel 4 en Armbian y la imagen se recompiló; la validación siguiente es el arranque en hardware por UART y microSD de prueba.
