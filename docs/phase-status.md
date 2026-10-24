# Estado de fases del proyecto

Actualizado: 2026-10-24.

Este documento sigue los criterios del brief inicial. “Compilado” y “verificado offline” no equivalen a “funciona en la consola”. La Fase 1 permanece abierta hasta observar un arranque real de esta unidad.

## Fase 1 — Placa y primera imagen Armbian

| Requisito | Estado | Evidencia / pendiente |
|---|---|---|
| Revisar el framework Armbian y opciones RK3326 | Completado en software | [`armbian-support-survey.md`](armbian-support-survey.md); checkout Armbian fijado y revisado. |
| Analizar arranque conocido y U-Boot | Auditado estáticamente; perfil DRAM pendiente de confirmar | [`boot-flow-comparison.md`](boot-flow-comparison.md); U-Boot R36S compilado con `r36s_defconfig` y SD `ff370000` como única fuente SPL. La reconsulta ArkOS ubica `mmc0` en `ff370000.dwmmc` y ve la tarjeta en SDR104; confirma el lector activo, no la compatibilidad del U-Boot nuevo. El TPL fuente selecciona la familia DDR3 a 333 MHz (DDR3L comparte esa familia de interfaz; LPDDR3 usa otra tabla). ArkOS/Linux no identifica el chip ni sus requisitos eléctricos. Falta leer el marcado de RAM físicamente y probar el arranque. |
| Analizar DTB R36S/panel de la unidad | Completado como hipótesis de software | [`r36s-dts-audit.md`](r36s-dts-audit.md), [`panel-variants.md`](panel-variants.md) e inventario. La unidad carga Panel 4 por software; revisión física e IC LCD sin identificar. |
| Crear definición Armbian para la placa | Completado en el checkout del proyecto | Definición `r36s.wip` y configuración de CPU 600–1296 MHz. |
| Integrar DTB y drivers necesarios para el primer diagnóstico | Compilado y empaquetado | DTB `rk3326-r36s-panel4.dtb`, módulo NV3051D R36S, `adc-joystick.ko`, `iio-mux.ko` y `mux-gpio.ko` están en la última imagen. La comparación de DTB confirma que los 17 GPIO/códigos de teclas coinciden con ArkOS. Una captura estática por SSH confirmó cuatro ejes ABS; el mapeo de canales del candidato coincide estáticamente con la tabla del mux BSP al considerar `GPIO_ACTIVE_LOW`. Para el adaptador Wi-Fi ArkOS `0bda:0179`, el kernel candidato incluye `rtl8xxxu.ko` y las dependencias inalámbricas `cfg80211`/`mac80211`; el paquete de firmware incluye `rtl8188eufw.bin`. Es soporte estático del paquete, pendiente probar asociación y tráfico al arrancar Armbian. Véase [`r36s-dts-audit.md`](r36s-dts-audit.md#comparación-de-controles-y-joystick) y [`hardware-inventory.md`](hardware-inventory.md). |
| Preparar build repetible con fuentes fijadas | Implementado; reproducibilidad binaria no garantizada | [`scripts/build-armbian.sh`](../scripts/build-armbian.sh), Armbian commit `4c0583c6…`, kernel commit `2926d88b…`, U-Boot commit `afcfed9c…`, TF-A v2.13.0 y contenedor principal fijado al digest `bffb2b34…` mediante el wrapper Docker. Se comprobó la redirección a digest y la imagen candidata se reconstruyó con ella. Las versiones de paquetes Debian no están congeladas y la imagen genera UUID ext4 nuevo; no se afirma que dos builds produzcan el mismo SHA-256. |
| Construir imagen mínima | Completado; reconstruida 2026-10-23 | Debian Bookworm ARM64, systemd, APT, kernel 6.18.58, U-Boot R36S configurado para priorizar la microSD y rootfs. La imagen candidata actual incluye provisioning local de usuario/Wi-Fi, regla de nombre `wlan0`, habilitación del MOTD, detección DC RK817 por GPIO, módulos ADC y override de `agetty` a 1.5 Mbaud para `ttyS2`; hash y log en [`first-image-test-plan.md`](first-image-test-plan.md). Una revisión anterior arrancó dos veces, pero falló Netplan; la candidata actual aún requiere prueba en consola. |
| Verificar artefacto antes de escribirlo | Completado offline; última verificación 2026-10-23 | [`first-image-test-plan.md`](first-image-test-plan.md) registra SHA-256 `1968f3a8…`, comparación binaria de U-Boot con el paquete correcto, boot.scr/DTB y comprobaciones FAT/ext4 en copias temporales. Incluye la regla Wi-Fi `wlan0` y el servicio que habilita el MOTD; esta verificación no prueba el arranque de la revisión. |
| Arrancar hasta una terminal en esta R36S | **Arranque logrado; corrección Wi-Fi generalizada pendiente de probar** | La revisión anterior llegó a SSH con Wi-Fi usando `wlx7cc709338230`. El journal del build problemático confirma que systemd renombra `wlan0` a ese nombre derivado de MAC y que el generador Netplan falla. La imagen reconstruida incluye una regla `.link` que asigna `wlan0` a la interfaz inalámbrica y Netplan usa ese nombre; falta comprobar generación Netplan, asociación y DHCP en consola. Evidencia y límites en [`first-image-test-plan.md`](first-image-test-plan.md). |

### Pendientes tras los primeros arranques

- Continuar auditorías estáticas y mantener los valores no medidos como provisionales. La interpretación de `design_capacity`, `charge_full`, la interpolación OCV y los límites RK817 ya se trazó en una rama BSP 4.4.189 relacionada con ArkOS; el commit exacto del kernel de esta unidad sigue sin demostrarse.
- Identificar y fotografiar la revisión de PCB, el marcado del chip RAM y el pack cuando haya acceso visual a la consola. El TPL actual usa la familia DDR3; hay que distinguir DDR3/DDR3L de LPDDR3 y comprobar los requisitos del chip y la placa.
- Preparar una microSD desechable y UART lógico de 3,3 V con captura a 1.5 Mbaud; identificar visualmente TX/RX/GND accesibles de UART2 `uart2m1` (GPIO2_PB4/PB6) en la revisión concreta antes de cablear.
- Capturar el arranque por UART desde encendido y guardar logs antes de cambiar parámetros.

La prueba inicial no debe escribir la microSD ArkOS funcional ni guardar cambios en el entorno persistente de U-Boot. No se requiere tocar ese entorno para intentar el arranque desde una tarjeta aparte.

## Fases posteriores

| Fase | Estado | Criterio para iniciar o cerrar |
|---|---|---|
| 2 — Soporte de hardware | No iniciada como fase de validación | Iniciar tras obtener una terminal en la unidad. Validar por separado pantalla, controles/sticks, audio, carga/batería, CPU y apagado; no generalizar a otras revisiones. |
| 3 — Sistema híbrido | No iniciada | Solo después de estabilizar el arranque y soporte base. Añadir RetroArch/frontend y cambio de modo Linux/Gaming. |
| 4 — Optimización | No iniciada | Requiere métricas reproducibles de arranque, memoria, rendimiento, temperatura y batería. |
| 5 — Distribución | No iniciada | Requiere imagen instalable/recuperable, build reproducible, versionado, instalación, actualización y recuperación documentadas. |

## Decisión inmediata

La imagen nueva pasó las verificaciones offline y el journal confirma que arrancó dos veces. El perfil ahora asigna `wlan0` a la interfaz Wi-Fi y configura Netplan con ese nombre; el siguiente paso es reconstruir y comprobar que Netplan genere la unidad WPA y que la consola obtenga DHCP. La captura UART sigue pendiente; falta localizar pads accesibles en la PCB. RAM, panel y batería no están confirmados físicamente, y la prueba reciente no confirma funcionamiento de Wi-Fi ni del cargador.
