# Plan: reducir paquetes de la imagen Armbian para R36S

## Objetivo

Reducir el tamaño instalado, el espacio de almacenamiento y los servicios de
fondo de la imagen sin perder arranque, Wi-Fi/SSH, diagnóstico y soporte del
hardware confirmado en la R36S observada. El resultado debe poder reconstruirse
desde la configuración del proyecto; no se limpiará a mano la consola activa.

## Estado y evidencia actual

- El build ya usa `BUILD_MINIMAL=yes` y `BUILD_DESKTOP=no`; por tanto, no parte
  de una imagen de escritorio. La limpieza debe concentrarse en paquetes CLI,
  herramientas de administración y servicios que Armbian agrega al perfil
  mínimo.
- El resumen del build local más reciente disponible es del 2026-10-24. Entre
  los paquetes agregados al rootfs enumera `htop`, `btrfs-progs`, `figlet`,
  `toilet`, `man-db`, `debsums`, `pahole`, `nano`, `bash-completion`,
  `alsa-utils`, `usbutils`, `mmc-utils`, `curl`, `wget`, `rsync`, `lsof`,
  `parted`, `fdisk`, `jq`, `bc` y `iputils-ping`. También figura
  `armbian-config` instalado por una extensión del framework.
- La imagen del proyecto depende de acceso por SSH y Wi-Fi, `sudo`, Netplan,
  `systemd-networkd`, `wpa_supplicant`, firmware Realtek, consola local/UART,
  diagnóstico del kernel y soporte de entrada/ADC. Esos componentes no son
  candidatos a eliminación sin una sustitución probada.
- La lista del resumen de build no equivale al inventario final del rootfs:
  faltan paquetes transitivos, versiones, tamaños instalados y servicios
  habilitados. La lista final debe extraerse de la imagen concreta.

## Método propuesto

1. **Fijar una línea base.** Elegir una imagen generada por este repositorio y
   registrar hash, tamaño del archivo y tamaño real de las particiones. Extraer
   en solo lectura el inventario `dpkg`, tamaños instalados y unidades
   habilitadas. Compararlo con el inventario de la R36S en ejecución, teniendo
   presente que el sistema reporta actualizaciones disponibles.
2. **Clasificar paquetes y servicios.** Marcar cada elemento como:
   - imprescindible para arranque/kernel/initramfs y rootfs;
   - necesario para hardware probado (Wi-Fi, entrada/sticks, audio, batería,
     almacenamiento y pantalla);
   - necesario para acceso y recuperación (SSH, red, `sudo`, UART y consola);
   - diagnóstico útil durante bring-up;
   - administración genérica prescindible para el uso previsto;
   - no utilizado, con dependencia y tamaño confirmados.
3. **Acordar dos perfiles conceptuales.** Mantener un perfil de diagnóstico
   con utilidades como `htop`, `usbutils`, `mmc-utils` y `alsa-utils`; preparar
   un perfil de uso final más pequeño solo después de cerrar la validación de
   hardware. No retirar herramientas de diagnóstico antes de tener un camino
   sencillo para recopilar logs y recuperar conectividad.
4. **Probar candidatos individualmente.** Revisar primero paquetes pequeños o
   claramente orientados a interfaz/banners (por ejemplo `figlet`, `toilet`,
   `bash-completion` o `man-db`). Evaluar aparte `armbian-config`, `htop`,
   `btrfs-progs`, `pahole`, `debsums`, `nano`, `rsync`, `curl`, `wget`,
   `usbutils`, `mmc-utils` y `alsa-utils`; algunos son útiles para mantenimiento
   o diagnóstico y no deben quitarse solo por parecer genéricos. Confirmar
   dependencias inversas, scripts de primer inicio y servicios afectados.
5. **Aplicar exclusiones en el build.** Usar el mecanismo de paquetes/extensiones
   del framework fijado o un hook del perfil con lista explícita y comentada.
   Evitar un `apt autoremove` genérico tardío que pueda quitar dependencias de
   red, firmware, consola o los módulos de hardware; comprobar también si una
   extensión vuelve a instalar paquetes como `armbian-config`.
6. **Construir una sola variante candidata.** Conservar intacta la imagen de
   referencia y registrar manifiesto, tamaños, servicios habilitados y cambios
   de paquete. Comparar bytes de imagen y espacio de rootfs, no solo el número
   de paquetes.
7. **Verificar offline y arrancar desde una microSD de prueba.** Ejecutar el
   verificador existente; después comprobar arranque, pantalla, acceso local,
   Wi-Fi/SSH, actualización de paquetes, almacenamiento, sticks/botones,
   audio, PMIC/batería, apagado y recolección de diagnósticos. Revisar `dmesg`
   y el journal por servicios fallidos.
8. **Promover solo los cambios con evidencia.** Si una eliminación rompe una
   función o recuperación, revertirla o conservar el paquete en el perfil de
   diagnóstico. Documentar cuánto espacio se ahorró y qué pruebas se pasaron.

## Componentes que se deben preservar inicialmente

- Kernel, módulos y firmware del adaptador Wi-Fi; Netplan, `systemd-networkd`,
  `wpa_supplicant`, resolución DNS y SSH.
- U-Boot, initramfs, systemd, udev, montaje FAT/ext4, `sudo`, usuario `r36s`,
  getty de consola/UART y servicios `r36s-*` instalados por el proyecto.
- Driver de pantalla, `gpio-keys`, joystick ADC, mux IIO, herramientas de
  diagnóstico de solo lectura y utilidades necesarias para actualizar o
  recuperar el sistema.
- `alsa-utils` y controladores/audio hasta que la salida física esté validada;
  herramientas de MMC hasta completar pruebas de tarjeta y almacenamiento.

Esta lista es un punto de partida, no un manifiesto definitivo; cada paquete
puede llegar como dependencia de otro que se conserve.

## Criterios de cierre

- Existe un manifiesto completo de la imagen base con tamaños y servicios.
- Cada paquete retirado tiene justificación y se conoce su impacto en
  dependencias y tareas de recuperación.
- La imagen candidata es menor de forma medible y supera la verificación
  offline.
- El conjunto de funciones preservadas arranca y funciona en la R36S desde una
  tarjeta de prueba; las limitaciones siguen documentadas por revisión.
- El build reproducible incluye la política de paquetes y no depende de borrar
  paquetes manualmente en la consola.

## Estado

Plan preparado. El build ya desactiva escritorio y usa el objetivo mínimo de
Armbian. Los paquetes citados son candidatos de revisión del resumen local, no
una lista aprobada para eliminación. Aún falta producir el inventario completo,
medir ahorros y probar cualquier imagen reducida en hardware.
