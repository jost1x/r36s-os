# Comparación del flujo de arranque

**Fecha:** 2026-10-23  
**Alcance:** archivos ArkOS copiados de la consola y la imagen Armbian experimental construida localmente. La consulta SSH a la consola fue de solo lectura.

## Arranque activo de ArkOS en esta unidad

- `/boot` está montado desde `/dev/mmcblk0p1` (FAT).
- El kernel recibe `root=UUID=e139ce78-9841-40fe-8823-96a304a09859`; el resto del sistema está en otra partición.
- El comando vivo incluye `console=/dev/ttyFIQ0` y `panel=unset`.
- El `boot.ini` de ArkOS carga desde `mmc 1:1` los archivos `Image`, `uInitrd` y `rk3326-r35s-linux.dtb`, y termina con `booti`.
- `boot.ini` también puede guardar variables de entorno y escribir un DTB de selección de panel a FAT. Esas ramas dependen de botones y no se usaron en la inspección.

Esto describe el flujo actualmente instalado y observado, pero no identifica por sí solo el origen ni el binario exacto de U-Boot que ejecuta la consola.

## Arranque esperado por la imagen Armbian

La partición FAT de la imagen contiene `boot.scr`, `boot.cmd`, `armbianEnv.txt`, `Image`, `uInitrd` y el directorio `dtb/rockchip/`. Se inspeccionó la tabla MBR y se leyó FAT de forma no modificante:

| Partición | Inicio | Tamaño | Uso observado |
|---|---:|---:|---|
| 1 | sector 32768 | 512 MiB | FAT de arranque |
| 2 | sector 1081344 | 1872 MiB | ext4 raíz |

`armbianEnv.txt` establece `fdtfile=rockchip/rk3326-r36s-panel4.dtb` y `rootdev=UUID=b65689c7-49d0-4e85-839d-d95d2de56cc0` en la imagen candidata actual. Por ello el script genérico `boot-rockchip64.cmd` no usa finalmente su valor por defecto `/dev/mmcblk0p1`: importa el UUID de la raíz desde `armbianEnv.txt`. El script carga el initramfs, kernel y DTB desde FAT y ejecuta `booti`.

U-Boot se compiló desde el fork R36S v2024.04, commit `afcfed9c686cb8fe90b683050a83e1f62a04e818`, con `r36s_defconfig` y el parche de proyecto `0001-r36s-boot-from-sdmmc.patch`. El kernel candidato también fija el commit `2926d88bb7fc4608fd942453d929c39e4e5ec006` en la definición de placa. El `.config` declara `CONFIG_DEFAULT_DEVICE_TREE="rk3326-r36s"`, `CONFIG_BOOTCOMMAND="bootflow scan"`, `CONFIG_BOOTSTD_DEFAULTS=y`, `CONFIG_BOOTSTD_BOOTCOMMAND=y`, `CONFIG_BOOTMETH_SCRIPT=y`, `CONFIG_LEGACY_IMAGE_FORMAT=y`, `CONFIG_MMC_DW_ROCKCHIP=y`, `CONFIG_DOS_PARTITION=y`, `CONFIG_FS_FAT=y`, `CONFIG_CMD_BOOTI=y`, `CONFIG_CMD_FAT=y` y `CONFIG_BAUDRATE=1500000`. Se decompilaron los `u-boot.dtb` y `spl/u-boot-spl.dtb` recién compilados: ambos confirman `/aliases/mmc0 = /mmc@ff370000`, `/aliases/mmc1 = /mmc@ff390000` y `/chosen/u-boot,spl-boot-order = /mmc@ff370000`. La microSD PX30 es `ff370000`; `ff390000` corresponde a eMMC. El método de scripts recorre `/` y `/boot/` por defecto, y acepta `boot.scr.uimg` o `boot.scr`; el archivo Armbian está en `/boot.scr` de la partición FAT. `CONFIG_BOOTSTD_FULL` está desactivado, pero el comando simple `bootflow scan` sigue siendo compatible según la documentación de ese commit; no dispone de las funciones completas de listado/menú. Esta correspondencia es estática: no prueba que el controlador inicialice la tarjeta ni que el scan encuentre el flujo en la R36S física. El entorno persistente está configurado en FAT (`CONFIG_ENV_IS_IN_FAT`, dispositivo/partición `1:1`).

### DRAM en el TPL realmente compilado

El candidato no incorpora un blob DDR de `rkbin`: el `r36s_defconfig` deja `CONFIG_ROCKCHIP_EXTERNAL_TPL` apagado, activa `CONFIG_ROCKCHIP_PX30` y compila el TPL open source del fork. [`px30-board-tpl.c`](https://github.com/AndreRenaud/u-boot-r36s/blob/afcfed9c686cb8fe90b683050a83e1f62a04e818/arch/arm/mach-rockchip/px30-board-tpl.c) llama a `sdram_init()` y luego retorna al BootROM para que continúe con la siguiente etapa. En la configuración compilada no se selecciona ninguna opción `CONFIG_RAM_ROCKCHIP_DDR4/LPDDR2/LPDDR3/LPDDR4`; [`sdram_px30.c`](https://github.com/AndreRenaud/u-boot-r36s/blob/afcfed9c686cb8fe90b683050a83e1f62a04e818/drivers/ram/rockchip/sdram_px30.c) usa por su `#else` la tabla [`sdram-px30-ddr3-detect-333.inc`](https://github.com/AndreRenaud/u-boot-r36s/blob/afcfed9c686cb8fe90b683050a83e1f62a04e818/drivers/ram/rockchip/sdram-px30-ddr3-detect-333.inc). Por tanto, el candidato ejecuta inicialización de la familia DDR3 a 333 MHz con detección de organización/capacidad por el código PX30; no selecciona explícitamente LPDDR3. DDR3L es la variante DDR3 de bajo voltaje (Micron describe sus partes DDR3L a 1,35 V y ciertas partes admiten también 1,5 V; no se debe generalizar ese margen a todo chip). La documentación oficial de [RK3326](https://www.rock-chips.com/a/en/products/RK33xilie/2018/0514/901.html) lista DDR3, DDR3L y LPDDR3 como opciones distintas de interfaz. El tipo que más claramente queda fuera de la tabla seleccionada es LPDDR3; aun así, ni el `.config`, ni la cantidad de RAM que muestra Linux, ni el nodo `ddr_timing` genérico del DTB ArkOS Panel 4 (con tablas para DDR2/3/4 y LPDDR2/3/4) identifican la memoria física ni sus requisitos eléctricos/timings de placa. Resolverlo requiere leer el marcado del chip/PCB o capturar el arranque antes de atribuir un fallo a la inicialización de RAM.

Como línea de investigación para una posible variante LPDDR3, las [notas oficiales de versión de Rockchip `rkbin`](https://github.com/rockchip-linux/rkbin/blob/master/doc/release/RK3326_EN.md) dicen que `rk3326_ddr_333MHz_v2.10.bin` corrigió un problema de arranque intermitente con LPDDR3. No demuestra que esa imagen use LPDDR3 ni que el binario cubra automáticamente todos los tipos de DRAM. Antes de sustituir el TPL fuente por ese blob habría que fijar versión/hash, revisar términos de redistribución y confirmar su selección de tipo. Por ahora se conserva el candidato fuente DDR3 y el arranque en hardware sigue siendo el criterio definitivo.

## Diferencias relevantes para la primera prueba

| Área | ArkOS observado | Imagen Armbian | Implicación |
|---|---|---|---|
| Consola de kernel | `ttyFIQ0`, driver Rockchip `fiq-debugger` con `serial-id=2`, 1.5 Mbaud y pinmux `uart2m1_xfer` | `ttyS2,1500000`, según el script Rockchip64 empaquetado (8N1 por defecto), UART2 con `uart2m1_xfer` | El número de UART y pinmux coinciden; confirmar pads accesibles en esta PCB. |
| U-Boot de compilación | No identificado con certeza | Fork R36S de U-Boot v2024.04, `r36s_defconfig`; TPL PX30 de fuente, tabla DDR3 por defecto | El tipo DRAM de esta unidad no se ha identificado. SPL/TPL/ATF y el arranque real siguen sin probar; confirmar el chip RAM y capturar UART. |
| Selección de kernel/DTB | `boot.ini`, DTB R35S seleccionado por el perfil Panel 4 | `armbianEnv.txt`, DTB propio Panel 4 | Nombres y rutas no son intercambiables; la imagen lleva su propio conjunto de arranque. |
| UUID raíz | `e139ce78-9841-40fe-8823-96a304a09859` | `b65689c7-49d0-4e85-839d-d95d2de56cc0` (imagen actual) | Cada imagen apunta a su propia raíz; no reutilizar ni sustituir por el UUID ArkOS. |
| Entorno persistente | `boot.ini` incluye ramas `saveenv` | El arranque Armbian normal no necesita cambiar el entorno | En la prueba no ejecutar `saveenv` ni las opciones de selector de panel. |

La consola del kernel `ttyS2,1500000` procede del script Rockchip64 de Armbian (8N1 por defecto). U-Boot declara `CONFIG_BAUDRATE=1500000`. Su función `serial_check_stdout()` usa `stdout-path` para resolver `serial2`, pero corta la cadena en `:` antes de buscar el alias; no procesa `115200n8` como velocidad. `board_f.c` inicializa `gd->baudrate` desde la variable de entorno `baudrate` y usa `CONFIG_BAUDRATE` si no existe. Por tanto, el DTS por sí solo no demuestra que U-Boot cambie a 115200; en una tarjeta nueva sin override, el valor de respaldo es 1.5 Mbaud. La velocidad efectiva sigue dependiendo del entorno encontrado en esa tarjeta. Véanse [`serial-uclass.c`](https://github.com/AndreRenaud/u-boot-r36s/blob/afcfed9c686cb8fe90b683050a83e1f62a04e818/drivers/serial/serial-uclass.c) y [`board_f.c`](https://github.com/AndreRenaud/u-boot-r36s/blob/afcfed9c686cb8fe90b683050a83e1f62a04e818/common/board_f.c). La dirección `DEBUG_UART_BASE=0xFF160000` está en la configuración R36S compilada; en su DTS `serial2` apunta a `ff160000` (UART2), habilitado con `uart2m1_xfer`. La consulta de solo lectura a ArkOS mostró `ttyFIQ0` bajo `fiq-debugger`; su nodo declara `rockchip,serial-id=<2>`, `rockchip,baudrate=<1500000>` y `pinctrl-0=<0xba>`. Al comparar ese phandle en el DTB Panel 4 archivado, `0xba` resuelve a `uart2m1_xfer` (GPIO2_PB4/PB6). ArkOS desactiva el nodo UART2 normal porque está reclamado por `fiq-debugger`; el controlador está presente y tiene seleccionado el mismo pinmux. El DTS U-Boot y el kernel candidato usan también `uart2m1_xfer`, así que la ruta lógica UART2 coincide en ArkOS y en el candidato. La guía de UART de Rockchip describe `rockchip,serial-id` como el selector de puerto, y el código R36S del proyecto configura la misma función de pines. Esto no confirma qué pads accesibles exponen esas señales en la revisión de PCB conectada; inspeccionar la placa antes de cablear. El defconfig guarda el entorno en FAT `1:1`; no ejecutar `saveenv` ni `fw_setenv` sobre ArkOS. Además, `CONFIG_VIDEO_ROCKCHIP` y `CONFIG_VIDEO_MIPI_DSI` están desactivados: no se espera una imagen en pantalla durante U-Boot; la pantalla se probará desde el kernel.

## Estado y próximo paso

**Validado estáticamente:** las dos tablas de particiones tienen un esquema coherente; están presentes los archivos que espera el script Armbian; el UUID configurado coincide con la raíz ext4 de esa imagen; el nombre de DTB en el entorno coincide con el DTB empaquetado; U-Boot compiló con comandos de escaneo, FAT y `booti`.

**Sin validar en hardware:** que el BootROM acepte el `idbloader.img` generado; la secuencia DDR/SPL/TPL/ATF; el UART y pinout; que `bootflow scan` encuentre `boot.scr`; el traspaso al kernel; el panel y el resto de periféricos.

La barrera de hardware sigue siendo una microSD de prueba, UART de 3.3 V capaz de capturar a 1.5 Mbaud y confirmación visual de los pads/GND de esta PCB. La comparación de árboles da una correspondencia consistente para UART2 y `uart2m1_xfer` entre ArkOS, U-Boot y kernel candidato; no demuestra por sí sola a qué puntos de prueba o cabecera llegan esas pistas en la revisión física. Probar 115200 solo como diagnóstico si la salida no se decodifica. No alterar el entorno persistente ni la tarjeta original.
