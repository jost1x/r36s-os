# Plan: validar pantalla y secuencia de encendido

## Objetivo

Confirmar en la unidad Panel 4 observada que el DTB y el driver NV3051D del
candidato Armbian inicializan pantalla, reset y backlight de forma estable.
La coincidencia de configuración con ArkOS no identifica físicamente el IC ni
garantiza compatibilidad con otras revisiones.

## Evidencia disponible

- ArkOS y el DTS candidato declaran 640×480 a 60 Hz, reloj de píxel de 29 MHz
  y reset en GPIO3 PC0 activo bajo.
- La secuencia del driver R36S con licencia GPL coincide en sus 153 registros
  principales con los datos de Panel 4 archivados. El IC no se ha identificado
  por marcado o lectura de ID.
- La unidad mostró imagen con una imagen candidata en una prueba reportada; una
  prueba posterior tuvo pantalla negra. La ruta de fallo no está aislada.

## Pasos

1. Registrar la revisión de PCB, etiquetas del panel/conector y fotografías
   antes de conectar instrumentos. No asumir que Panel 4 identifica el módulo
   físico.
2. Preparar una microSD de prueba recuperable y una captura UART desde el
   encendido. Mantener intactos la tarjeta funcional y el entorno U-Boot.
3. Arrancar la imagen candidata y guardar la secuencia UART completa. Buscar
   detección del panel, errores DSI/regulador, activación del backlight y
   montaje del rootfs; distinguir fallo de boot de fallo exclusivo de imagen.
4. Si hay SSH, guardar `dmesg`, estado DRM/conectores, modos disponibles,
   reguladores `vcc_lcd`/`vcc_backlight` y estado del dispositivo backlight.
   No cambiar timings mientras no exista evidencia del modo activo.
5. Hacer varios arranques en frío y reinicios desde la tarjeta de prueba.
   Registrar pantalla visible, estabilidad, parpadeos, orientación y tiempo
   hasta imagen. Comparar con ArkOS usando la misma unidad.
6. Si falla, separar las hipótesis: secuencia/driver DSI, reset, alimentación,
   backlight, DTB cargado o arranque anterior al kernel. Cambiar una variable
   por build y conservar UART y hash de cada imagen.

## Criterios de cierre

- La unidad física y la configuración de software probada están identificadas.
- Se observa imagen estable en varios arranques de la imagen identificada y se
  archivan UART, versión/hash de imagen y estado DRM.
- Los valores eléctricos se describen como declarados o medidos según la
  evidencia; no se atribuye un IC sin leer su marcado o ID.

## Estado

Plan preparado. La compatibilidad del panel con la imagen candidata y la causa
de la pantalla negra intermitente requieren una prueba con UART.
