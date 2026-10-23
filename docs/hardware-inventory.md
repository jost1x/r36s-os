# Inventario de hardware — inspección inicial

**Fecha de inspección:** 2026-10-23  
**Equipo inspeccionado:** `ark@192.168.100.29`  
**Método:** sesión SSH de solo lectura a una unidad con ArkOS. No se modificaron archivos, variables de arranque ni particiones.

**Primer arranque Armbian reportado por el usuario (2026-10-23):** tras probar la imagen candidata, informa que el sistema carga, hay imagen en pantalla y observa carga. No se recibieron lecturas de `power_supply`, foto ni captura de consola; por ahora esto valida cualitativamente que la unidad inicia lo suficiente para mostrar imagen y que se conecta alimentación/carga, sin confirmar el estado real de carga de batería ni el porcentaje. El intento posterior de SSH a `ark@192.168.100.29` expiró, por lo que esa IP/servicio no quedaron confirmados bajo Armbian.

**Reconsulta de hardware por SSH (2026-10-23):** el modelo/compatible siguen siendo `Game Console R35S/R36S fix by lxc` / RK3326. `MemTotal` reporta 919228 KiB; el log de Linux muestra cerca de 1 GiB física reservada/usable, pero no imprime generación o tipo de DRAM. `mmc0` se resuelve a `ff370000.dwmmc`, y el kernel detectó allí la microSD como SDR104; esto concuerda con el controlador PX30 SD que el perfil Armbian configura primero. También se decompiló el DTB Panel 4 archivado: su nodo `ddr_timing` incluye parámetros para varios estándares (DDR2/3/4 y LPDDR2/3/4) y no selecciona cuál está montado en esta consola. Rockchip documenta soporte RK3326 para varias tecnologías de memoria ([anuncio oficial del SoC](https://www.rock-chips.com/a/en/News/Press_Releases/2018/0413/898.html)); eso no identifica la RAM de esta unidad. El TPL candidato usa la familia DDR3; falta comprobar el chip y sus requisitos eléctricos, sobre todo descartar LPDDR3.

**Seguimiento DRAM (2026-10-23):** una segunda consulta de solo lectura vuelve a mostrar `MemTotal=919228 kB`; `dmesg` informa 1.015.808 KiB detectados y 902.584 KiB disponibles tras reservas, sin mensaje que identifique el estándar. `cat /proc/iomem` devuelve `Permission denied` para `ark`, así que ese método no está disponible sin privilegios. Conviene distinguir DDR3L de LPDDR3: [Micron](https://my.micron.com/sales-support/sales/faqs) especifica DDR3L como DDR3 de bajo voltaje (1,35 V para sus partes DDR3L), mientras que LPDDR3 es una tecnología distinta. El código TPL candidato selecciona la tabla DDR3; eso hace de LPDDR3 la incertidumbre de compatibilidad de protocolo más clara, pero no prueba por sí solo que cualquier chip DDR3L y la alimentación de esta placa funcionen con esa configuración. El tipo/modelo exacto continúa sin identificar; no se cambió nada en la consola.

**Referencia comunitaria de memoria (no verificada en esta unidad):** el README de un proyecto NixOS para R36S describe la plataforma como 1 GB DDR3L ([nixos-r36s](https://github.com/icefirex/nixos-r36s)). Es una especificación general publicada por ese proyecto, sin foto/lectura del marcado del chip de nuestra consola; sirve como indicio de que la familia DDR3L se usa en R36S, pero no descarta variantes LPDDR3 ni sustituye la inspección física. No se cambió el perfil DDR del TPL por esta referencia.

**Lectura de reguladores SD por SSH (2026-10-23):** sin privilegios, `/sys/class/regulator/` reporta `vccio_sd=1.800.000 µV` (mínimo y máximo 1,8 V, enabled) y `vcc_sd=3.000.000 µV` (rango declarado 1,8–3,0 V, enabled). Esto coincide con el DTB ArkOS: LDO_REG5 fijo en 1,8 V y LDO_REG6 seleccionable hasta 3,0 V. El DTS candidato se ajustó para mantener `vcc_sd` a 3,0 V en operación/suspensión y permite a `vccio_sd` 1,8–3,3 V con 1,8 V durante suspensión. No se escribió ni cambió nada en la consola.

**Seguimiento de CPU, alimentación y temperatura por SSH (2026-10-23):** muestra instantánea con governor `interactive`, CPU a 1.512 GHz (frecuencias disponibles 1.008, 1.200, 1.248, 1.296 y 1.512 GHz), `vdd_arm=1,30 V`, `vdd_logic=0,975 V`, LCD `vcc_lcd=2,8 V`, backlight `vcc_backlight=3,3 V`, `vcc_ddr=0,5 V`, SD IO `vccio_sd=1,8 V` y SD card `vcc_sd=3,0 V`; los reguladores listados estaban habilitados salvo los que se indican en sysfs como deshabilitados. SoC/GPU: 54,166/54,583 °C. Batería: `Full`, 100 %, 4,204 V, corriente reportada 30 mA y AC online. No aparecieron coincidencias en `dmesg` para avisos de undervoltage, errores de regulador o sobrecorriente. No se midió carga, consumo ni estabilidad sostenida.

Relectura SSH de solo lectura (2026-10-23 18:14 UTC): LCD `connected` con modo `640x480p60`; CPU a 1.512 GHz con governor `interactive`; batería `Full`, 100 %, 4.204 V, 28 mA y salud `Good`; SoC/GPU a 55.909/54.166 °C. El filtro de avisos de `dmesg` solo encontró mensajes de sesiones de usuario systemd que no pudieron conectar a un socket de journal; no se observaron coincidencias de fallo de regulador, bajo voltaje o sobrecorriente en esa consulta. Es una muestra instantánea, sin prueba de carga térmica ni eléctrica.

El DTB candidato conserva el rango PMIC `vdd_arm=0,95–1,35 V` y la tabla PX30 de OPP 600/816/1008/1200/1296 MHz; a 1.296 GHz el OPP solicita 1,35 V. No incluye el OPP ArkOS de 1,512 GHz. ArkOS declara voltajes OPP diferenciados `L0`–`L3`; el valor observado de 1,30 V a 1,512 GHz no basta para identificar el bin ni copiar una curva reducida. Mantener el perfil candidato sin modificar hasta medirlo en la consola bajo carga.

## Identificación reportada por el sistema

| Componente | Observación | Evidencia |
|---|---|---|
| Modelo de placa | `Game Console R35S/R36S fix by lxc` | `/proc/device-tree/model`, `/proc/cpuinfo` |
| Compatibilidad del device tree cargado | `rockchip,rk3326-odroidgo3-linux`, `rockchip,rk3326` | `/proc/device-tree/compatible` |
| SoC / CPU | RK3326; 4 × ARM Cortex-A35, AArch64 | `lscpu`, `/proc/cpuinfo`, compatible del device tree |
| CPU frequency | Policy `interactive`; muestra más reciente a 1.512 GHz; frecuencias disponibles: 1.008, 1.200, 1.248, 1.296 y 1.512 GHz | `/sys/devices/system/cpu/cpufreq/policy0/*`; muestra instantánea, no prueba de carga |
| RAM | 919228 KiB total; alrededor de 897 MiB visibles en `free`. Este conteo no identifica el tipo de DRAM | `/proc/meminfo`, `free -h`; el TPL candidato usa la familia DDR3, pero no se conoce el tipo/modelo físico; auditoría en [`boot-flow-comparison.md`](boot-flow-comparison.md) |
| Pantalla | DSI conectada, modo `640x480p60`; framebuffer virtual 640×480. El árbol de dispositivos en ejecución declara `elida,kd35t133`, `simple-panel-dsi`, 4 lanes y tamaño 52×70 mm | `/sys/class/drm/card0-DSI-1/{status,modes}`, `/sys/class/graphics/fb0/virtual_size`, `/sys/firmware/devicetree/base/dsi@ff450000/panel@0/*` |
| Entradas | `GO-Super Gamepad` expone joystick `js0`, teclas y cuatro ejes ABS (`ABS=0x1b`); `odroidgo3-keys` y `rk8xx_pwrkey` aparecen como dispositivos separados | `/proc/bus/input/devices`, `/sys/class/input/event*/device/capabilities/*`; el driver informa 17 teclas GPIO y 4 entradas ADC |
| PMIC / batería | RK817. Muestra SSH de 2026-10-23 16:49 UTC: `Full`, 100 %, 4.183 V, `CURRENT_NOW=242000 µA`, salud `Good`, AC online y `charge_full=3380000 µAh`. Muestra posterior a las 18:14 UTC: 4.204 V y 28 mA reportados, también `Full`/100 % con AC online. Muestras previas durante carga: 4.062→4.129 V y ~0.58→0.72 A. El driver BSP 4.4.189 relacionado devuelve `design_capacity × 1000` para ese atributo, por lo que es un valor DTB, no una medición independiente de capacidad. Ninguna lectura caracteriza autonomía o curva de descarga. | `dmesg`, `/sys/class/power_supply/{battery,ac,usb}`; interpretación contrastada en [`r36s-dts-audit.md`](r36s-dts-audit.md) |
| Audio | Codec RK817 y dispositivo ALSA de reproducción detectados; mixer tiene `Playback Path` en `SPK_HP`, volumen 19 %, micrófono en `MIC OFF` durante la lectura | `/dev/snd`, `aplay -l`, `amixer -c 0 scontents`, `dmesg` |
| Wi-Fi (adaptador USB) | Realtek `802.11n NIC`, USB `0bda:0179`. En ArkOS, `wlan0` existe y el controlador activo enlazado al dispositivo es `r8188eu`; `dmesg` registra `assoc success` y `wlan0 link becomes ready`. También está cargado el módulo `8188eu`, pero el dispositivo está enlazado a `r8188eu`. En la imagen Armbian candidata, el kernel empaquetado incluye `rtl8xxxu.ko`, `cfg80211.ko` y `mac80211.ko`; el firmware empaquetado incluye `rtl8188eufw.bin`. El ID USB `0bda:0179` está cubierto por `rtl8xxxu`. No se ha probado la conexión Wi-Fi arrancando Armbian en la consola. | SSH de solo lectura: `/sys/bus/usb/devices/*/{idVendor,idProduct,product}`, `/sys/class/net/wlan0/device/{driver,uevent}`, `modinfo`, `dmesg`, `ip -s link`. Inspección de los paquetes kernel SHA-256 `67838f56…` y firmware SHA-256 `fddcbdf0…` con `ar`/`tar`; sin extraer ni alterar la imagen. |
| Térmico / GPU / memoria | Muestras sin carga controlada: SoC/GPU 47.272/48.636 °C (anterior), 54.166/54.583 °C (posterior) y 55.909/54.166 °C a las 18:14 UTC. Mali devfreq 400–520 MHz (actual 400 MHz) y DMC 528–786 MHz (actual 528 MHz) en la lectura registrada. No caracterizan temperaturas bajo carga. | `/sys/class/thermal`, `/sys/class/devfreq`; muestras instantáneas |
| Almacenamiento | microSD `SC128`, 249737216 sectores lógicos de 512 bytes (127865454592 bytes, aprox. 119.1 GiB). El identificador CID empieza `03534453` y el fabricante MMC reporta `0x000003`; no se infiere marca comercial solo de estos códigos. | `/sys/block/mmcblk0/{size,queue/logical_block_size,device/*}` |
| Kernel de referencia | Linux `4.4.189`, AArch64 | `uname -a` |

## Primera validación en Armbian (2026-10-23)

Informe completo: [`diagnostics/r36s-hardware-2026-10-23.md`](diagnostics/r36s-hardware-2026-10-23.md), generado remotamente con `/usr/local/sbin/r36s-diagnostics` y copiado por SSH. Es una sola muestra en reposo, no una prueba de carga.

| Componente | Lectura Armbian | Qué falta validar |
|---|---|---|
| Pantalla | DRM registra `DSI-1 connected`, modo `640x480`, framebuffer `rockchipdrmfb`. El usuario ya confirmó que ve imagen. | Brillo, estabilidad tras reinicio y artefactos durante uso. |
| CPU / temperatura | Governor `ondemand`, frecuencia instantánea `1.296 GHz` (máxima configurada); SoC `46.8 °C`, GPU `45.9 °C`; carga media 0.06. | Repetir tras unos minutos en reposo y bajo carga ligera; la lectura instantánea no demuestra que quede fijo en máximo. |
| Batería / carga | RK817 presente. ArkOS reporta `ac/online=1`, `Charging`; Armbian mantiene `rk817-charger/online=0` en la prueba de conexión en caliente. GPIO0_PB3 (gpiochip0 offset 11) sí cambia `0` desconectado → `1` conectado. | Integrar en Armbian la detección por GPIO que usa el BSP; luego validar carga real, transiciones, límites térmicos y autonomía. |
| Controles | En captura física de 25 s, `event0` emitió 282 eventos de botones y `event2` 914 eventos; se observaron cambios en `ABS_X/Y/RX/RY`. | Confirmar correspondencia física de cada código, orientación, centros/extremos y deadzone. |
| Audio | ALSA detecta codec RK817 con reproducción/captura; el mixer expone volumen y selector `Playback Mux=HP`. | Probar sonido en parlante y audífonos. |
| Almacenamiento | La SD aparece como `SC64G`, 59.5 GB; raíz ext4 montada en escritura. | Lectura/escritura sostenida y recuperación tras apagado limpio. |
| Wi-Fi | RTL8188ETV con `rtl8xxxu` y firmware; enlace operativo en `192.168.100.29` verificado por SSH en la consulta posterior. | Confirmar persistencia tras reinicio. |

El recolector se ejecutó como usuario `r36s`; `dmesg` fue denegado por permisos, por lo que el informe no incluye el buffer completo del kernel.

## Arranque observado en ArkOS

- `/boot/boot.ini` carga `Image`, `uInitrd` y `rk3326-r35s-linux.dtb`, y arranca con `booti`.
- La línea de comandos incluye `panel=unset`; esto no identifica por sí solo la revisión física del LCD.
- El script implementa un selector de panel con opciones `Panel 0` a `Panel 5`, además de una variante `Panel 4 - V22` en `/boot/ScreenFiles`.
- Hay distintos DTB e imágenes de kernel en esos directorios. Su presencia no demuestra cuál corresponde al panel instalado ni que sean compatibles con Armbian.
- El kernel registra un modo DRM de 640×480. También informa avisos de enlace inicial del display, propiedades del panel y energía de Mali; la pantalla termina registrándose como framebuffer.

## Mapeo de entradas declarado por el DTB activo

Se decompiló el [DTB Panel 4 de la raíz de `/boot`](../reference/arkos-r36s/boot/rk3326-r35s-linux.dtb), cuyo SHA-256 coincide con el archivo que cargó ArkOS en la unidad. El mapeo siguiente refleja lo que declara el driver vendor `odroidgo3-joypad` en ese DTB; no reemplaza una prueba de pulsación física.

| Control etiquetado en DTB | GPIO Rockchip activo bajo | Código Linux declarado |
|---|---|---|
| D-pad up / down / left / right | GPIO1_PB4 / PB5 / PB6 / PB7 | `BTN_DPAD_UP` `0x220` / `DOWN` `0x221` / `LEFT` `0x222` / `RIGHT` `0x223` |
| BTN-A / BTN-B | GPIO1_PA2 / PA5 | `0x131` (`BTN_B`) / `0x130` (`BTN_A`) |
| BTN-X / BTN-Y | GPIO1_PA7 / PA6 | `0x133` (`BTN_X`) / `0x134` (`BTN_Y`) |
| TOP-LEFT / TOP-RIGHT | GPIO2_PA6 / PA7 | `BTN_TL` `0x136` / `BTN_TR` `0x137` |
| TOP-LEFT2 / TOP-RIGHT2 | GPIO3_PB2 / PB7 | `BTN_TL2` `0x138` / `BTN_TR2` `0x139` |
| F1 / F2 | GPIO3_PB1 / PB4 | `BTN_TRIGGER_HAPPY1` `0x2c0` / `HAPPY2` `0x2c1` |
| F3 / F4 / F5 | GPIO2_PA2 / PA3 / PA4 | `BTN_TRIGGER_HAPPY3` `0x2c2` / `HAPPY4` `0x2c3` / `HAPPY5` `0x2c4` |
| Volume up / down (`odroidgo3-keys`) | GPIO2_PA0 / PA1 | `KEY_VOLUMEUP` 115 / `KEY_VOLUMEDOWN` 114 |

El power key aparece además como dispositivo `rk8xx_pwrkey` en `/proc/bus/input/devices`, separado del gamepad. Los GPIO de los controles indicados por el DTB son activos en bajo. La tabla suma 17 switches del joypad y las dos teclas de volumen reportadas en la sesión SSH.

**Discrepancia A/B:** el DTB etiqueta GPIO1_PA2 como `BTN-A`, pero le asigna el código `0x131` (`BTN_B`); GPIO1_PA5 se etiqueta `BTN-B` y recibe `0x130` (`BTN_A`). Esto prueba que la configuración de software intercambia esos códigos; la orientación física y el comportamiento percibido en juegos aún no se han ensayado.

El joypad declara cuatro ejes vía ADC multiplexado en el canal 1 de SARADC, `amux-count = 4`, polling de 10 ms, inversión de ABS_X y ABS_Y, y parámetros de escala/deadzone/fuzz/flat para los botones ADC. ArkOS expone cuatro ejes ABS en el dispositivo `GO-Super Gamepad`; no se ha medido el rango real de cada stick ni su centro, recorrido o calibración.

**Muestra de ejes por SSH (2026-10-23):** `evtest /dev/input/event2` identifica `GO-Super Gamepad` (`js0`) y declara ABS_X, ABS_Y, ABS_RX y ABS_RY con rango −1800…1800, fuzz/flat 32. Al abrirlo, los cuatro aparecieron en 0; esto es el estado reportado al abrir, no una medición del recorrido físico. El dmesg del driver informa calibraciones ADC 1784, 1768, 1792 y 1760, escala 2, rango −1800…1800, deadzone 64 y polling 10 ms; sysfs confirma intervalo 10 ms y amux de cuatro canales. No se movieron los sticks durante la captura, por lo que centro, extremos, sentido y linealidad siguen pendientes. No se escribió a `amux_debug` ni se cambió el estado de la consola. Véase la [auditoría de joystick](r36s-dts-audit.md#comparación-de-controles-y-joystick).

**Estado del kernel Armbian actual:** el DTS candidato declara `adc-joystick` e `io-channel-mux`. La última imagen habilita `CONFIG_JOYSTICK_ADC=m`, `CONFIG_IIO_MUX=m` y `CONFIG_MUX_GPIO=m`, y empaqueta sus módulos; el kernel integra SARADC. Al comparar el DTB compilado con el DTB ArkOS Panel 4, los 17 GPIO/códigos digitales del joypad coinciden, igual que los GPIO/códigos de volumen. El candidato agrupa las teclas de volumen dentro del nodo `gpio-keys`; ArkOS las expone en un dispositivo aparte. Falta comprobar que cada botón físico genere el evento esperado. Para los sticks, el candidato usa el driver genérico y polling de 60 ms; ArkOS usa su driver vendor y polling de 10 ms. Los rangos y la calibración candidata siguen sin medirse. `KEYBOARD_GPIO=y` y `INPUT_EVDEV=y` están activos; véase la [comparación detallada de controles](r36s-dts-audit.md#comparación-de-controles-y-joystick).

## Límites y pendientes

1. **Configuración de pantalla identificada como Panel 4 en ejecución.** El árbol de dispositivos vivo coincide en sus propiedades principales y el DTB de la raíz coincide por SHA-256 con la variante Panel 4. `elida,kd35t133` es lo que declara el software; no verifica por sí solo la serigrafía o el chip físico. Ver [comparación de variantes](panel-variants.md).
2. **Entorno U-Boot aún sin consultar.** `fw_printenv` está instalado, pero no funciona porque falta `/etc/fw_env.config`; `/proc/mtd` no lista MTD. No se ha leído ni cambiado la selección guardada por el selector. No adivinar el offset de almacenamiento.
3. **GPU:** existe `/dev/dri/card0` y `renderD128`, pero eso no valida aceleración gráfica funcional. `dmesg` informa `Power control initialization failed` durante la inicialización de Mali.
4. **Batería:** las lecturas fueron instantáneas y con el cargador conectado; no verifican autonomía, descarga, umbrales ni consumo. En una rama BSP 4.4.189 relacionada, `charge_full` es `design_capacity` del DTB convertido a µAh; como no se confirmó que el kernel instalado use exactamente ese commit, se conserva el dato observado con esa salvedad. En cualquier caso, no es una medición runtime de capacidad.
5. **Audio:** se detectan ALSA, reproducción y controles de mixer; aún no se ha probado salida audible por altavoz/auriculares ni botones de volumen. No cambiar el mixer por SSH sin coordinar la prueba.
6. **Controles:** botones y sticks generan eventos en esta unidad. Falta mapear cada pulsador físico a su código y comprobar orientación, calibración, deadzones y el intercambio A/B. La última imagen incluye `gpio-keys`, `adc-joystick`, `iio-mux` y `mux-gpio`.
7. **RAM:** el dato es memoria que el kernel expone, no una medición física independiente del módulo.
8. **Revisión de placa:** no se puede deducir del modelo RK3326 ni de la etiqueta Panel 4 del DTB. Una referencia pública con fotos de R36S V12/V21/V30 muestra códigos y fechas serigrafiados en la PCB; el artículo trata revisión de placa y variante de panel como ejes separados. No aporta un mapeo universal entre revisión y pinout. Ver [fotos de placas](https://r36s.space/inside) y [análisis de revisión y panel](https://r36s.space/blog/dtb-and-board-revision). Son referencias comunitarias, no un esquema oficial ni identificación de esta unidad.
9. **Hardware físico pendiente:** no se han verificado visualmente revisiones de placa, panel, batería, sticks, botones, altavoz ni conectores. Antes de cablear UART, registrar la serigrafía y fotografiar esta PCB. Una foto publicada de una placa V30 muestra pads rotulados GND/RX/TX/VCC; no asumir que las etiquetas o posición coinciden con la unidad inspeccionada.

### UART observada por software (consulta SSH de solo lectura)

- En el device tree activo de ArkOS, `serial1` apunta a `/serial@ff158000` y `serial2` a `/serial@ff160000`. El nodo `ff158000` está `okay`; `ff160000` está `disabled`.
- El kernel de ArkOS arranca con `console=/dev/ttyFIQ0`; sysfs muestra `ttyFIQ0` bajo `fiq_debugger.0` y `ttyS1` bajo `ff158000.serial`. El nodo `fiq-debugger` del árbol vivo declara `rockchip,serial-id=<2>`, `rockchip,baudrate=<1500000>` y `pinctrl-0=<0xba>`. En el DTB Panel 4 archivado, el phandle `0xba` es `uart2m1_xfer`; ese grupo usa GPIO2_PB4 y GPIO2_PB6. La [guía de UART de Rockchip](https://lo01.g77k.com/aeb/docs/en/Common/UART/Rockchip_Developer_Guide_UART_EN.pdf) indica que `serial-id` selecciona el UART y que el nodo serial de ese puerto puede quedar desactivado cuando lo reclama `fiq-debugger`.
- El U-Boot candidato selecciona `serial2`/UART2 (`ff160000`) como `stdout-path`, configura debug UART en esa base y habilita el mismo pinmux `uart2m1_xfer`; su respaldo es 1.500.000 bit/s. El kernel candidato también habilita UART2 con `uart2m1_xfer` y pide `ttyS2` a 1.500.000 bit/s.
- **Implicación para la prueba:** la inspección de los árboles de dispositivo muestra que ArkOS, U-Boot candidato y kernel candidato seleccionan UART2 por los mismos pines de función alternativa 1 (`GPIO2_PB4/PB6`). Que el nodo UART2 normal aparezca desactivado en ArkOS no significa que el UART esté sin uso: lo reclama el driver `fiq-debugger`. Esta coincidencia reduce la duda de controlador/pinmux, pero aún falta identificar visualmente pads accesibles y GND en esta revisión física antes de conectar.

## Siguiente paso

La inspección de software y la imagen candidata ya están preparadas. Antes de cablear, identificar visualmente la revisión de PCB y sus marcas UART; las fotos de referencia no sustituyen esta comprobación. Después, probar el arranque desde una microSD de prueba con captura UART, siguiendo el [plan de prueba de la primera imagen](first-image-test-plan.md). La R36S física y la tarjeta ArkOS no deben modificarse; no hace falta consultar ni escribir el entorno U-Boot persistente para esta prueba. Si la imagen alcanza una terminal, continuar con pruebas separadas de pantalla, pulsación de cada control y calibración de sticks, audio, batería/carga y apagado, registrando cada resultado aquí. Las frecuencias y temperaturas ya anotadas son muestras de una sesión, no medidas de rendimiento o consumo.

**Preparación de software para audio/PMIC:** el paquete de kernel de la imagen contiene los módulos RK817/I²S/simple-card, cargador RK817 y tecla de encendido; el DTS candidato declara el routing de altavoz/auriculares y cargador. Eso es soporte compilado, no validación funcional. Los parámetros `simple-battery` (incluida capacidad declarada de 3380 mAh, 100 mΩ y curva OCV portada del DTB ArkOS Panel 4) son provisionales y deben contrastarse con el pack instalado y mediciones antes de tratarlos como calibración.

## Notas de la sesión

- `lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL` no funcionó porque la versión instalada no reconoce la columna `MOUNTPOINTS`; se usó `/proc/partitions` y sysfs como alternativa.
- La advertencia de SSH sobre intercambio de claves poscuántico es informativa y no impidió la conexión.
- Revisión SSH de solo lectura (2026-10-23): `/dev/mmcblk0` tiene 249737216 sectores lógicos de 512 bytes. `mmcblk0p1` empieza en el sector 32768 y mide 229376 sectores (112 MiB); está montada como FAT en `/boot`. `mmcblk0p2` empieza en 262144 y mide 22214187 sectores (aprox. 10.6 GiB); es ext4 y contiene `/`. `mmcblk0p3` empieza en 22476331 y mide 227260885 sectores (aprox. 108.2 GiB); es exFAT y está montada en `/roms` y `/opt/system/Tools`. Los tamaños y montajes son coherentes con el esquema de particiones activo. No se leyó la tabla desde sectores crudos ni se escribió en la tarjeta.
- Identificadores de sysfs reportados: nombre `SC128`, fabricante MMC `0x000003`, serial `0xd394b089`, CID `035344534331323880d394b0890199c7`. Se registran como identificadores observados, no como autenticación de origen o capacidad genuina. La partición de ROMs ocupa casi todo el espacio restante; no es una microSD de prueba disponible.
