# Auditoría del DTS candidato R36S

Fecha de revisión: 2026-10-23.

## Alcance y fuentes

Esta auditoría compara:

1. La consola accesible como `ark@192.168.100.29`, consultada por SSH sin modificarla.
2. El DTB Panel 4 copiado desde `/boot/rk3326-r35s-linux.dtb` a `reference/arkos-r36s/boot/` (SHA-256 registrado en `reference/arkos-r36s/SHA256SUMS`). Se decompiló con el `dtc` incluido en el árbol de kernel Armbian local.
3. El DTS `rk3326-r36s.dts` del commit `ba832b723d70318be2bdf65aff344194a807e6f5` de [AndreRenaud/linux-r36s](https://github.com/AndreRenaud/linux-r36s/tree/ba832b723d70318be2bdf65aff344194a807e6f5). El archivo declara SPDX `(GPL-2.0+ OR MIT)`.

La consola volvió a reportar `Game Console R35S/R36S fix by lxc`, compatibles `rockchip,rk3326-odroidgo3-linux` y `rockchip,rk3326`, y kernel ArkOS 4.4.189. El nodo de pantalla activo por DRM reporta 640×480p60. Esta consulta confirma estado del software en ejecución, no la identidad física del panel.

## Comparación de datos

| Subsistema | Evidencia ArkOS / unidad | DTS Linux R36S candidato | Evaluación |
|---|---|---|---|
| SoC | Compatible RK3326; modelo de software R35S/R36S | `rockchip,rk3326` | Coincide en SoC; la etiqueta/modelo genérica no distingue revisiones. |
| Pantalla, resolución | DTB Panel 4: 640×480; DRM activo 640×480p60 | Modo R36S: 640×480 | Coincidencia fuerte de modo. |
| Pantalla, geometría | 52×70 mm en DTB Panel 4 | 70×52 mm | Coincide al intercambiar orientación; revisar convención de orientación. |
| Pantalla, reloj | 29 MHz declarado en DTB Panel 4 | 29 MHz en el modo DRM del driver R36S del kernel | Coincide en la configuración actual. La frecuencia no se midió eléctricamente y el panel aún no se probó con Armbian. |
| Pantalla, reset | DTB: phandle GPIO3, offset 16 (PC0), activo bajo | GPIO3 PC0, activo bajo | Coincidencia exacta de pin/polaridad. Es evidencia de compatibilidad del cableado de reset, no del IC del panel. |
| Pantalla, controlador | Compatible declarado `elida,kd35t133` + `simple-panel-dsi`; init DSI de 773 bytes | Patch usa `gameconsole,r36s-panel` asociado a NV3051D; modo Panel 4 | Las declaraciones de ArkOS y Linux difieren. Los 153 registros de dos bytes coinciden exactamente. El compatible sigue siendo una etiqueta de software, no una lectura del IC. |
| Pantalla, alimentación | DTB conecta pantalla a `vcc_lcd` 2,8 V y backlight a `vcc_backlight` 3,3 V | DTS de referencia conecta `vdd` e `iovcc` a `vcc_lcd`; patch propio entrega `vdd` al driver y backlight al PWM | Solo se conecta `vdd` en el patch porque el driver/binding actual no consume `iovcc`; verificar arranque/orden de alimentación en hardware. |
| Batería / PMIC | DTB declara RK817; `design_capacity=3380`, `design_qmax=3718`, `bat_res=100`; curva OCV de 21 entradas | `simple-battery`: 3380 mAh, resistencia interna 100 mΩ y curva OCV de 21 puntos portada desde Panel 4 | Coinciden los parámetros trasladables desde el DTB activo de ArkOS. Siguen siendo valores declarados por software y provisionales hasta medir/identificar físicamente el pack; otras propiedades del cargador no tienen equivalentes directos. |
| CPU / reguladores | OPP disponibles hasta 1,512 GHz; en una muestra estaba a 1,512 GHz con `vdd_arm=1,30 V`, `vdd_logic=0,975 V` y SoC a 54,166 °C. El DTB incluye OPP de 1,512 GHz con voltajes por niveles `L0`–`L3`. | OPP PX30 hasta 1,296 GHz; ese punto solicita 1,35 V. `vdd_arm` permite 0,95–1,35 V y `vdd_logic` 0,95–1,15 V. | El perfil limita frecuencia máxima frente a ArkOS y usa el OPP base PX30 sin tabla de bins. La lectura de una sola muestra ArkOS no basta para bajar voltajes ni extrapolar una curva; comprobar frecuencia, voltaje y temperatura en el candidato antes de ajustar rendimiento. |
| Audio | ArkOS declara codec RK817 | DTS candidato configura codec RK817 por I2S y routing de jack/altavoz | Candidato plausible, no se verificó cada GPIO/ruta en la unidad. |
| Entrada | DTB instalado contiene `odroidgo3-keys` y `odroidgo3-joypad` | DTS candidato define `gpio-keys` y `adc-joystick` multiplexado | Se compararon estáticamente los GPIO y códigos: las 17 teclas del joypad coinciden con ArkOS. Las teclas de volumen también usan los mismos GPIO/códigos, pero el candidato las agrupa en `gpio-keys`. La ruta ADC y su driver son distintos; intervalo y calibración no son equivalentes y requieren prueba. |
| MicroSD / almacenamiento | DTB ArkOS asigna `mmc0` a `ff370000` (`dwmmc`), GPIO0_PA3 activo bajo y UHS SDR12/25/50/104. Linux negocia SDR104. Reguladores leídos en ejecución: `vccio_sd=1,8 V` (fijo) y `vcc_sd=3,0 V` (rango DTB 1,8–3,0 V). | DTS candidato asigna `mmc0` a `ff370000`, GPIO0_PA3 activo bajo y las mismas capacidades UHS. `vccio_sd` permite 1,8–3,3 V (suspensión 1,8 V); `vcc_sd` queda fijo en 3,0 V (también en suspensión). | Se igualaron las tensiones operativas observadas en ArkOS y se mantuvo ajustable `vccio_sd` para el control UHS del kernel. El retardo de detección difiere: 800 ms ArkOS y 200 ms candidato. El bus funciona en ArkOS; el lector con el kernel candidato y la tarjeta de prueba siguen sin validarse. |
| USB / carga | RK817 y USB presentes en DTB | DTS candidato habilita USB host y deshabilita OTG | Requiere contrastar funciones de puertos físicos; la conectividad observada por software no prueba el pinmux completo. |

### Nota sobre el DTB de ArkOS

La raíz del DTB Panel 4 deriva en gran medida de la configuración ODROID-GO3 del proveedor: modelo y compatible así lo indican, y el gamepad usa nodos `odroidgo3-*`. Es útil como registro de lo que ArkOS necesita para esta consola y como fuente de mediciones del panel, pero no es una descripción upstream limpia de la placa. El candidato R36S de Andre Renaud es más apropiado para iniciar la definición de placa, con cada señal marcada como observada, inferida o pendiente.

### Verificación de la secuencia Panel 4

Se decodificó `panel-init-sequence` del DTB local y se comparó con `panel_nv3051d_init_sequence_r36s()` del driver fuente. Los **153 comandos de dos bytes** coinciden en orden y valor. ArkOS añade al final `exit sleep` (`0x11`) con 200 ms de espera y `display on` (`0x29`) con 20 ms; el driver publicado emite esos comandos con los helpers DCS estándar y espera 200 ms entre ambos. El driver incluye además escrituras `0x11,0x00` y `0x29,0x00` dentro de su secuencia antes de usar los helpers. Se debe preservar ese comportamiento al portar inicialmente; no asumir que esos paquetes son idénticos.

La referencia declara el driver bajo SPDX GPL-2.0 y mantiene atribución al autor del driver base. El match ofrece trazabilidad técnica fuerte para adaptar la variante al Panel 4 de esta unidad; no identifica físicamente el IC ni certifica el resto del driver.

### Comparación de controles y joystick

Se decompiló de nuevo el DTB Panel 4 archivado con el `dtc` del kernel fijado y se compararon sus nodos de entrada con el DTB Panel 4 producido por el build. La comparación es de descripciones de software; no prueba continuidad eléctrica ni pulsación física.

- **Teclas digitales:** los 17 GPIO y códigos declarados por ArkOS coinciden con los del DTS candidato: D-pad, cuatro botones frontales, cuatro gatillos/bumpers, cinco botones F y sus códigos Linux. También coinciden los dos GPIO/códigos de volumen. El DTB ArkOS separa volumen (`odroidgo3-keys`) del joypad (`odroidgo3-joypad`); el candidato pone las 19 teclas en un nodo `gpio-keys`, mientras los ejes ADC quedan en un segundo dispositivo. Es una diferencia de agrupación que podría afectar qué dispositivo selecciona un frontend, aunque conserva la señal/código de cada tecla.
- **A/B:** ambos mapeos declaran GPIO1_PA2 como etiqueta A con código Linux `BTN_EAST`/`BTN_B` (0x131), y GPIO1_PA5 como etiqueta B con código `BTN_SOUTH`/`BTN_A` (0x130). La inversión observada está en los códigos de software de ambas configuraciones; no hay base para cambiarla sin una prueba de los botones físicos y la expectativa del frontend.
- **Sticks:** ambos usan SARADC canal 1, dos líneas de selección de mux GPIO3_PB3/PB0, habilitación GPIO3_PB5, cuatro canales multiplexados y ejes `ABS_X`, `ABS_RX`, `ABS_Y`, `ABS_RY`. El candidato usa el driver genérico mainline `io-channel-mux` + `adc-joystick`; ArkOS usa `odroidgo3-joypad`.
- **Lectura en ejecución de ArkOS (SSH, 2026-10-23):** `evtest /dev/input/event2` confirmó `GO-Super Gamepad`, handler `js0`, cuatro ejes y capacidad ABS `0x1b`. Al abrir, cada eje reportó 0, rango −1800…1800 y fuzz/flat 32. El dmesg del driver registró `invert-absx=1`, `invert-absy=1`, `invert-absrx=0`, `invert-absry=0`; escala 2, deadzone 64 y calibraciones ADC [1784, 1768, 1792, 1760]. Sysfs mostró polling de 10 ms, `adc_flat=32`, `adc_fuzz=32` y `amux-count=4`. Es una lectura estática sin mover los sticks: no mide centro mecánico, extremos ni respuesta.
- **Orden del mux, con salvedad:** el DTB vivo no contiene `amux-channel-mapping`. En la rama BSP relacionada [`odroidgo3-joypad.c`](https://github.com/lcdyk0517/arkos.bsp.4.4/blob/rg351/drivers/input/joystick/odroidgo3-joypad.c), el orden predeterminado del driver vendor es ch0=RY, ch1=RX, ch2=Y, ch3=X; la selección física documentada es 00=RY, 01=RX, 10=LY, 11=LX. El binario/commit exacto de ArkOS no está identificado, así que esto orienta la lectura, pero no confirma qué eje físico cambia en esta unidad. En el candidato, `gpio-mux` recibe los bits del estado en el mismo orden que `mux-gpios`; `GPIO_ACTIVE_LOW` invierte cada bit en el pin. Por eso, estados lógicos 0, 1, 2 y 3 seleccionan físicamente 11, 01, 10 y 00. El mapeo candidato X, RX, Y, RY corresponde entonces a LX, RX, LY, RY según la tabla de selección del BSP: la asignación estáticamente coincide con la geometría documentada. Falta comprobar en esta unidad que el cableado y el driver correspondan a esa tabla, mediante una prueba de movimiento con la imagen candidata.
- **Diferencia de configuración:** ArkOS fija `poll-interval = 10` ms; el candidato, 60 ms. El candidato fija rangos 30–900 / 80–960 / 80–880 / 60–850 y deadzone/fuzz 10. ArkOS usa parámetros de tuning del driver vendor en vez de `abs-range` estándar y solicita invertir X/Y; el driver genérico candidato invierte X/Y con rangos descendentes. El código exacto compilado, [`adc-joystick.c` de Linux v6.18.58](https://github.com/torvalds/linux/blob/2926d88bb7fc4608fd942453d929c39e4e5ec006/drivers/input/joystick/adc-joystick.c), confirma que intercambia el mínimo/máximo y refleja el valor al leer, de modo que las dos maneras de invertir son equivalentes. No se conoce la escala efectiva real de los potenciómetros en esta unidad.
- **Decisión:** conservar el polling y rangos del DTS R36S de referencia para el primer arranque; no copiar directamente el polling más rápido del driver vendor ni presentar rangos no medidos como calibrados. En Fase 2, probar recorrido, centro, sentido, latencia y consumo; ajustar intervalo/deadzone/rangos solo con lecturas físicas repetibles. Registrar la agrupación de volumen como una diferencia de userspace pendiente, no como un fallo eléctrico.

### Comparación de batería y cargador

Se decompiló el DTB Panel 4 archivado y se compararon sus propiedades RK817 con el nodo `simple-battery` del DTS candidato. ArkOS usa el esquema del driver RK817 del kernel proveedor; el candidato usa el binding genérico `simple-battery` y el driver RK817 actual. Por eso, los números solo se comparan cuando la magnitud/unidad es explícita; no se equiparan propiedades por nombre parecido.

| Magnitud | DTB Panel 4 de ArkOS | DTS candidato | Lectura |
|---|---:|---:|---|
| Capacidad / `charge_full` | `design_capacity=<3380>`; `design_qmax=<3718>`; sysfs ArkOS reportó `charge_full=3380000 µAh` | `charge-full-design-microamp-hours=<3380000>` (3380 mAh) | El binding define `design_capacity` como capacidad real probada con herramienta (mAh) y `design_qmax` como nominal ×1,1; `3718 = 3380 × 1,1`. En el código de la rama BSP `rg351`, `CHARGE_FULL` y `CHARGE_FULL_DESIGN` devuelven `design_capacity × 1000`, lo que explica exactamente 3380000 µAh. El Makefile de esa rama es 4.4.189, igual que el kernel observado, pero no se confirmó el commit/binario exacto instalado; por tanto 3380 es un valor DTB anunciado como medido, no una medición independiente realizada en esta inspección. |
| Resistencia | `bat_res=<100>` | `factory-internal-resistance-micro-ohms=<100000>` (100 mΩ) | El binding BSP RK 4.4 especifica `bat_res` en mΩ. El candidato ahora porta el valor declarado por ArkOS; su correspondencia con la resistencia real del pack y el modelo del driver genérico requiere validación. |
| Curva OCV | 21 valores: `<0xc5d ... 0xfa0>` = 3165–4000 mV | 21 pares SOC/voltaje, misma curva convertida a µV y en orden descendente | El binding describe la relación voltaje/SOC y el driver BSP `rg351` distribuye los 21 puntos uniformemente de 0 a 100 % (5 puntos porcentuales por intervalo), interpolando linealmente entre voltajes. La tabla candidata conserva esos valores en el formato que consume `simple-battery`; no implica que la capacidad o curva se hayan medido independientemente ni que ambos drivers estimen idéntico SOC. |
| Voltaje mínimo de entrada | Cargador: `min_input_voltage=<4500>` | Sin propiedad equivalente | El driver BSP convierte el número en mV: 4500 selecciona 4,5 V. El DTS candidato no expresa este límite. |
| Corriente máxima de entrada | Cargador: `max_input_current=<1500>` | Sin propiedad equivalente | El driver trata el valor en mA; 1500 selecciona el límite de entrada de 1,5 A. No está expresado por el nodo candidato. |
| Corriente máxima de carga | Cargador: `max_chrg_current=<2000>` | Batería: `constant-charge-current-max-microamp=<2000000>` (2 A) | El driver BSP interpreta mA y selecciona 2 A para 2000; coincide con el máximo declarado por el candidato. |
| Voltaje máximo de carga | Cargador: `max_chrg_voltage=<4200>` | Batería: `constant-charge-voltage-max-microvolt=<4200000>` (4,2 V) | El driver BSP interpreta mV y selecciona 4,2 V para 4200; coincide con el máximo declarado por el candidato. |
| Corriente de terminación | Cargador: `chrg_finish_cur=<52>`; `chrg_term_mode=<0>` | Batería: `charge-term-current-microamp=<150000>` (150 mA); sin equivalente para modo | El driver usa modo 0 analógico; cualquier valor menor que 200 selecciona el escalón de terminación 150 mA. Así, 52 no significa un límite físico de 52 mA en esta rama: el umbral efectivo candidato se ajustó a 150 mA. |
| Resistencias de muestreo | `sample_res=<10>` tanto en batería como en cargador | `rockchip,resistor-sense-micro-ohms=<10000>` (10 mΩ) | Coinciden: el driver identifica el valor como 10 mΩ y el candidato declara 10000 µΩ. |
| Corrientes de reposo/filtro | `sleep_enter_current=<300>`, `sleep_exit_current=<300>`, `sleep_filter_current=<100>` | `rockchip,sleep-enter-current-microamp=<300000>`, `rockchip,sleep-filter-current-microamp=<100000>` | El binding BSP RK 4.4 especifica mA para las propiedades antiguas; coinciden tras convertir a µA. El candidato no declara un umbral separado de salida (`sleep_exit_current`). |
| Umbral de apagado | `power_off_thresd=<3000>` | `voltage-min-design-microvolt=<3500000>` (3,5 V) | El binding BSP especifica el umbral antiguo como tensión VSYS en mV. No equivale a la tensión mínima de diseño de `simple-battery`; el candidato no declara ese mismo umbral explícitamente. |
| Parámetros del algoritmo | `zero_algorithm_vol=<3850>`, `max_soc_offset=<60>`, `monitor_sec=<5>`, `virtual_power=<0>` | Sin equivalentes en las propiedades estándar usadas | Son controles del algoritmo proveedor; no trasladarlos al DTS genérico por semejanza de nombre. |
| GPIO y detección del cargador | `dc_det_gpio` = GPIO0_PB3 activo alto, `bat_low_gpio`, `extcon=<0x67>` | El nodo RK817 candidato no pasa esas propiedades; mainline lee plug-in/out del PMIC por IRQ GPIO0_PB2 | Confirmado: en Armbian `gpioget gpiochip0 11` devolvió 0 desconectado y 1 conectado; sin embargo `rk817-charger/online` y sus IRQ plug-in/out permanecieron en cero. El driver BSP ArkOS sí consume `dc_det_gpio` como entrada/IRQ; el mainline no. Falta integrar el soporte de esa señal y la configuración de carga asociada en Armbian. |

#### Comparación ordinal de las curvas OCV

El binding BSP llama a `ocv_table` una relación entre voltaje y SOC y su ejemplo muestra voltajes en mV. El código de la rama `rg351` confirma la interpolación sobre los índices de la tabla: con 21 puntos, cada intervalo representa 5 puntos porcentuales. La tabla siguiente muestra los valores alineados por ese código; los voltajes candidatos se redondean al mV. Esta interpretación es de la rama relacionada, cuya correspondencia exacta con el binario ArkOS de la unidad sigue pendiente.

| SOC asignado por el driver BSP | ArkOS DTB (mV) | DTS candidato (mV) |
|---:|---:|---:|
| 0 % | 3165 | 3165 |
| 5 % | 3220 | 3220 |
| 10 % | 3280 | 3280 |
| 15 % | 3330 | 3330 |
| 20 % | 3380 | 3380 |
| 25 % | 3430 | 3430 |
| 30 % | 3480 | 3480 |
| 35 % | 3530 | 3530 |
| 40 % | 3580 | 3580 |
| 45 % | 3630 | 3630 |
| 50 % | 3670 | 3670 |
| 55 % | 3710 | 3710 |
| 60 % | 3750 | 3750 |
| 65 % | 3790 | 3790 |
| 70 % | 3830 | 3830 |
| 75 % | 3870 | 3870 |
| 80 % | 3910 | 3910 |
| 85 % | 3950 | 3950 |
| 90 % | 3990 | 3990 |
| 95 % | 3995 | 3995 |
| 100 % | 4000 | 4000 |

También se registró en ArkOS `monitor_sec=5`, `sample_res=10` y `virtual_power=0`; son opciones del controlador proveedor sin equivalencia directa en el DTS genérico. El candidato ya porta 3,38 Ah, 100 mΩ y la curva declarada por ArkOS Panel 4. Las capturas de sysfs existentes incluyen lecturas durante carga (4,06–4,13 V y 0,58–0,72 A) y una lectura SSH del 2026-10-23 con estado `Full`, AC online, 4,183 V y 0,242 A reportados. Son instantáneas en carga/alimentación externa: no deducen capacidad real ni validan la curva OCV.

**Decisión:** para el siguiente build se portó la curva, capacidad declarada, resistencia y terminación efectiva de ArkOS al candidato. No se cambió el umbral de diseño de 3,5 V porque no equivale al apagado VSYS de 3,0 V; tampoco se inventaron equivalentes para propiedades privadas. Estos datos siguen provisionales: identificar el marcado/revisión física del pack y tomar lecturas durante carga y descarga controladas antes de calibrarlos. No hacer pruebas de descarga profunda.

### Fuentes consultadas para interpretar las propiedades

- [Binding RK817 de la rama `rg351` del kernel BSP 4.4](https://github.com/lcdyk0517/arkos.bsp.4.4/blob/382f9c6ddcb4a8d4f0162228305545e647cca97c/Documentation/devicetree/bindings/power_supply/rk817-battery.txt): especifica capacidad probada en mAh, `design_qmax` nominal ×1,1, `bat_res` en mΩ, corrientes sleep en mA y `power_off_thresd` como VSYS en mV. El repo se identifica como kernel de modificaciones para (d)ArkOS4Clone; no se verificó que el binario de nuestra consola se construyera de este commit.
- [Binding del cargador RK817 en la misma rama](https://github.com/lcdyk0517/arkos.bsp.4.4/blob/382f9c6ddcb4a8d4f0162228305545e647cca97c/Documentation/devicetree/bindings/power/rk817-charger.txt): define qué significan los límites de entrada/carga y la corriente de terminación, pero no declara las unidades de esos campos.
- [Driver RK817 de esa rama `rg351`](https://github.com/lcdyk0517/arkos.bsp.4.4/blob/382f9c6ddcb4a8d4f0162228305545e647cca97c/drivers/power/rk817_battery.c) y [driver del cargador](https://github.com/lcdyk0517/arkos.bsp.4.4/blob/382f9c6ddcb4a8d4f0162228305545e647cca97c/drivers/power/rk817_charger.c): inspeccionados localmente en el commit `382f9c6ddcb4a8d4f0162228305545e647cca97c`. El código devuelve `design_capacity × 1000` para `CHARGE_FULL` y confirma la interpolación uniforme de OCV; el driver cargador confirma unidades/rangos y la cuantización analógica del umbral de terminación. El Makefile declara 4.4.189, pero falta demostrar que este commit sea la fuente exacta del kernel instalado en la unidad.
- [Driver RK817 upstream de Linux](https://code.googlesource.com/linux/torvalds/linux/%2B/2a565258b3f4bbdc7a3c09cd02082cb286a7bffc/drivers/power/supply/rk817_charger.c): describe la diferencia entre capacidad de diseño y capacidad completa, el uso de mAh para el valor de capacidad guardado en NVRAM del BSP y la inicialización de la capacidad completa a partir de `charge-full-design`. Es una guía semántica del driver mainline, no el código exacto de ArkOS.
- [DTB modificado para una placa G80CAMB v1.2](https://github.com/xunicatt/rk3326-g80cambv12-linux-dtb): su autor usa 3000 mAh y cambia `design_qmax`/umbral para esa placa. Sirve como evidencia de que circulan configuraciones distintas, no como valor transferible a nuestra consola.

Se localizó e inspeccionó el código de un fork BSP 4.4.189 relacionado con ArkOS4Clone. Sus bindings/drivers aclaran las unidades, muestran que `charge_full` se obtiene directamente de `design_capacity` y especifican cómo la tabla OCV se convierte a SOC. La versión coincide con la reportada por la consola; la procedencia exacta del binario ArkOS sigue sin demostrarse, así que estos resultados describen con precisión esa rama y explican las observaciones, pero no certifican que el binario de la unidad sea idéntico.

## Decisión técnica

- Aceptar como datos de partida: RK3326, salida MIPI-DSI de cuatro lanes (DTB ArkOS), modo visible 640×480p60, geometría declarada 52×70 mm y reset GPIO3 PC0 activo bajo.
- No declarar identificado el controlador LCD. `elida,kd35t133` y NV3051D son compatibles declarados por fuentes distintas; no se leyó un ID electrónico ni se inspeccionó el marcado físico.
- Mantener el reloj en 29 MHz, valor declarado por el DTB ArkOS y usado en el modo DRM del driver R36S candidato. No es una medición eléctrica; validar la imagen y estabilidad en la pantalla física.
- Usar como hipótesis de driver NV3051D la variante R36S publicada bajo GPL, con atribuciones. El modo DRM adaptado usa el valor declarado por ArkOS (29 MHz, 640×480, 52×70 mm); el ID físico del panel continúa sin leerse.
- No copiar el init sequence del DTB ArkOS: se conserva como evidencia debido a que su procedencia/licencia no está resuelta. En su lugar, el driver publicado con SPDX GPL-2.0 proporciona una fuente licenciada cuya secuencia tiene match exacto con los 153 registros de dos bytes observados en ArkOS Panel 4; conservar copyright y atribuciones al portarla.
- El kernel Armbian fijado upstream incluye el driver genérico NV3051D, pero no su variante R36S. El patch local añade el compatible `gameconsole,r36s-panel`, el modo DRM 52×70 mm/29 MHz y el binding correspondiente. El binding upstream `newvision,nv3051d.yaml` no enumera ese compatible.
- No usar aún valores de batería, ADC/joystick ni detección UHS como valores finales.

## Próximo artefacto y validación

El patch ya porta al kernel Armbian el DTS Panel 4, su perfil RK817 provisional y su modo observado (29 MHz, 640×480, área declarada 70×52 mm), la secuencia del driver R36S GPL con atribuciones y los compatibles en sus bindings. La siguiente validación es física por UART y microSD de prueba; quedan por revisar señales de entrada, alimentación, MMC con el kernel candidato, audio y batería. ArkOS ya muestra SDR104 en el lector físico. El perfil candidato iguala `vcc_sd` en 3,0 V y conserva `vccio_sd` ajustable entre 1,8 y 3,3 V, con 1,8 V durante suspensión. El retardo de hotplug es 800 ms en ArkOS frente a 200 ms en el candidato.

La compilación actual prueba sintaxis, referencias y empaquetado; falta validar el panel en ejecución. El gate de uso real sigue siendo: microSD de prueba con respaldo y recuperación, UART conectado, observar SPL/U-Boot, luego kernel/rootfs, y probar pantalla/entrada/audio/batería por separado. No escribir la microSD original ni el entorno persistente de U-Boot.

### Compilación preliminar del DTS de referencia

Se guardó una copia de referencia licenciada en [`device-trees/reference/rk3326-r36s-renaud.dts`](../device-trees/reference/rk3326-r36s-renaud.dts), sin alterarla. SHA-256 del fuente: `4eedc8eb295471e6550ba485c00ce4abb3addfd1963cae6f1ecc0b92004f8ea8`.

La primera compilación de esa copia (antes de corregir el nodo DSI en el patch propio) generó DTB v17 de 48.595 bytes, SHA-256 `d3a1148ac386669daec343b21736b9b6e414a4aa787dc809da6d820c667c2848`. Los warnings de `reg_format` del panel se corrigieron añadiendo `#address-cells = <1>` y `#size-cells = <0>` al nodo DSI; el build final no reporta esos warnings. Persisten dos warnings de graph en `px30.dtsi`, heredados del SoC.

### Build Armbian con panel R36S y sticks ADC

El patch del proyecto `config/armbian/patches/kernel/r36s-6.18/0001-r36s-panel-and-device-tree.patch` (SHA-256 actual `b61b231b50cca609b6d1c76f0b3c6a579fc3663d828f8b7fa27316b23d1f918c`) se aplicó después de `archive/rockchip64-6.18`. La compilación inicial terminó en 7:51 min. El último rebuild de kernel añadió los módulos para sticks y terminó en 7:23 min, con 171 s de compilación. El rebuild posterior con el contenedor fijado por digest terminó en 1:58 min y reutilizó esos paquetes de kernel/U-Boot. Su log está en `work/armbian-build/output/logs/log-build-d969f91c-87e0-402c-a667-6938987b6c57.log.ans`; el log que compila los módulos ADC sigue en `work/armbian-build/output/logs/log-build-9f525907-ad18-47df-a34d-9f7d55370827.log.ans`. El kernel usa el commit fijado `2926d88bb7fc4608fd942453d929c39e4e5ec006`. La build instaló el DTB `rk3326-r36s-panel4.dtb` y registró `CONFIG_DRM_PANEL_NEWVISION_NV3051D=m`, `CONFIG_JOYSTICK_ADC=m` y `CONFIG_IIO_MUX=m`.

Artefactos verificados:

| Artefacto | Evidencia |
|---|---|
| Imagen candidata actual | `work/armbian-build/output/images/Armbian-unofficial_26.11.0-trunk_R36s_bookworm_current_6.18.58_minimal.img`, 2.516.582.400 bytes (2,52 GB decimales / 2,34 GiB); SHA-256 `1968f3a8ffd3df0929996214eb07dd89f706d16ea88b6e3de698ade5f3210800`; UUID raíz `6dfe7755-f703-42cf-8091-ca49127e5ff1` |
| DTB empaquetado | Verificador leyó desde la imagen `dtb/rockchip/rk3326-r36s-panel4.dtb`; SHA-256 `246443338f2e1083697423fec93a9aadc00c6c29bc86f4e563c6a7ff823e42fd` |
| Driver | `panel-newvision-nv3051d.ko` incluido en paquete `linux-image`; `modinfo` de la build inicial mostró alias `gameconsole,r36s-panel` y licencia GPL. el paquete de la imagen nueva contiene el mismo módulo; SHA-256 verificado `dd27a087f585adff6120eb60c4324175f5e99b610030d5ff9933fd20d39dc231` |
| Particiones | MBR/DOS; FAT de 512 MiB desde sector 32768; ext4 desde sector 1081344; inspeccionado con `sfdisk` |
| Kernel package | SHA-256 `67838f56b8d748d7af23c99ac914bcc2c0c38ced1da65ee7fc36bd6234ec3fe0`; incluye `adc-joystick.ko`, `iio-mux.ko`, `mux-gpio.ko` |
| U-Boot package | `linux-u-boot-r36s-current_26.11.0-trunk_arm64__2024.04-Safcf-Pfce2-Ha199-Vfb0e-Bb936-R448a.deb`; SHA-256 `d173fad9957999ffae787bbd67d0c8f8f7c5ff8d175060f8d89a4361be7c8e4d`; contiene alias SD-first verificados en SPL y U-Boot general |
| Log de build actual | `work/armbian-build/output/logs/log-build-2853efd7-b5af-4885-afff-3f74f4b37303.log.ans`; el último rebuild incluye U-Boot SD-first y conserva `agetty` a 1.5 Mbaud. El kernel ADC se compiló en el log anterior `log-build-9f525907-ad18-47df-a34d-9f7d55370827.log.ans` |

Esto verifica patching, compilación del kernel/DTB/driver y empaquetado de la imagen. No demuestra que U-Boot arranque en esta placa ni que la pantalla/controles/batería funcionen. La imagen continúa sin instalarse en una tarjeta.

En la reconstrucción incremental del 2026-10-23 se portó al `simple-battery` del candidato el perfil declarado por ArkOS Panel 4: 3380000 µAh, 100000 µΩ, terminación 150000 µA, máximo de diseño 4200000 µV y los 21 puntos OCV convertidos a µV. Se extrajo el DTB de la partición FAT de la imagen con el lector FAT de `scripts/verify-image.py`, se decompiló con el `dtc` del kernel fijado y se comprobaron esas propiedades en el resultado. El rebuild posterior ajustó además los reguladores SD a los valores observados en ArkOS. SHA-256 del DTB actual: `800d230ce63508e1d258bc5c21a66e68685574043b4fbfc6f1aa4b56ebb89d25`. DTC conserva dos warnings de graph en nodos heredados LVDS/DSI del SoC; la extracción confirma contenido del archivo, no validez eléctrica ni calibración del pack.

## Reproducir la decompilación de referencia

Desde la raíz del proyecto:

```sh
work/armbian-build/cache/sources/linux-kernel-worktree/6.18__rockchip64__arm64/scripts/dtc/dtc \
  reference/arkos-r36s/boot/rk3326-r35s-linux.dtb \
  -o /tmp/r36s-panel4.dts
```

`dtc` reporta warnings de estructura/nombres en el DTB de proveedor; la decompilación terminó correctamente. Esos warnings no validan el árbol contra bindings upstream. Para recompilar la copia de referencia contra el kernel Armbian actual:

```sh
K=work/armbian-build/cache/sources/linux-kernel-worktree/6.18__rockchip64__arm64
cpp -nostdinc -I "$K/include" -I "$K/arch/arm64/boot/dts" \
  -I "$K/arch/arm64/boot/dts/rockchip" -undef -D__DTS__ \
  -x assembler-with-cpp device-trees/reference/rk3326-r36s-renaud.dts |
  "$K/scripts/dtc/dtc" -I dts -O dtb -o /tmp/r36s-candidate-local.dtb -
```
