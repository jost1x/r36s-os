# R36S Hybrid OS

Proyecto para investigar y desarrollar una distribución Linux para la consola R36S original. La prioridad inicial es verificar el hardware y conseguir una base que pueda reconstruirse con fuentes fijadas y probarse en la consola antes de trabajar en la interfaz de juegos.

## Documentación

- [Inventario de hardware y revisión inicial](docs/hardware-inventory.md)
- [Comparación de variantes de pantalla](docs/panel-variants.md)
- [Auditoría del DTS y perfil Panel 4](docs/r36s-dts-audit.md)
- [Revisión inicial de Armbian/RK3326](docs/armbian-support-survey.md)
- [Comparación del flujo de arranque ArkOS/Armbian](docs/boot-flow-comparison.md)
- [Estado de los device trees R36S](device-trees/README.md)
- [Plan de prueba de la primera imagen](docs/first-image-test-plan.md) (incluye [`scripts/collect-r36s-diagnostics.sh`](scripts/collect-r36s-diagnostics.sh) para recopilar un informe de solo lectura tras el primer arranque)
- [Estado de fases y criterios de salida](docs/phase-status.md)
- [Paquetes runtime necesarios para NEXUS](docs/nexus-runtime-packages.md)

Los datos del inventario proceden de una sesión SSH de solo lectura en una consola con ArkOS. Son observaciones de esa unidad; no deben tomarse como especificación de todas las revisiones R36S.

## Estado actual

La unidad observada usa la configuración de software Panel 4 de ArkOS; el identificador físico del LCD aún no está verificado. Se añadió al kernel un driver NV3051D con secuencia R36S cuya secuencia coincide en sus 153 registros principales con Panel 4, y un DTB propio con los timings observados. La imagen mínima Debian Bookworm/Armbian usa kernel 6.18.58, el `r36s_defconfig` de U-Boot R36S y `rk3326-r36s-panel4.dtb`; incluye módulos para joystick ADC y multiplexor IIO. Una revisión anterior llegó a una terminal por Wi-Fi/SSH en la unidad observada, pero otra build falló al generar Netplan. La imagen candidata actual asigna `wlan0` a la interfaz Wi-Fi, configura Netplan con ese nombre y restaura el MOTD dinámico de Armbian. Pasó la verificación offline; falta probar esta revisión en la consola. No se escribió la tarjeta original ni el almacenamiento de la consola. Ver [revisión de Armbian, panel y U-Boot](docs/armbian-support-survey.md) y el [plan de prueba](docs/first-image-test-plan.md).

## Prototipo Armbian

Hay una definición de placa `.wip`, patches específicos del kernel y U-Boot y un script aislado para preparar o iniciar un build del Armbian Build Framework fijado a un commit. El script también fija por digest el contenedor principal de build aunque el framework use una etiqueta móvil. El perfil está dirigido a la configuración Panel 4 por software de la unidad observada; no es todavía una imagen validada ni cubre todas las revisiones de pantalla R36S. Ejecuta `scripts/build-armbian.sh prepare` para preparar el checkout, o `scripts/build-armbian.sh build` para producir la imagen mínima. Antes de grabar, verifica la imagen y deja que el verificador elija el paquete U-Boot exacto con `python3 scripts/verify-image.py --check-filesystems --uboot-packages-dir work/armbian-build/output/debs RUTA/IMAGEN.img`. La opción `--check-filesystems` requiere `fsck.fat`, `e2fsck` y unos 1,9 GB libres para la copia temporal más grande; no modifica la imagen. El hash, log, contenido y limitaciones están registrados en la revisión Armbian.

El verificador acepta una ruta a archivo de imagen regular y la abre solo para lectura; no escribe a dispositivos de bloque. Comprueba el MBR, FAT32, archivos de arranque, formato y CRC del `boot.scr`, coincidencia del script empaquetado con `boot.cmd`, UUID ext4 y existencia/hash del DTB configurado. Con `--uboot-packages-dir`, selecciona el paquete `.deb` cuyo binario coincide byte por byte con el U-Boot escrito en la imagen; también se puede indicar un paquete concreto con `--uboot-package`. Con `--check-filesystems`, copia temporalmente las particiones y ejecuta `fsck.fat -n` y `e2fsck -fn` sobre esas copias. Ninguna opción valida el arranque en hardware.
