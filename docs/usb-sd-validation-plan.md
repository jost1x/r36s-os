# Plan: validar puertos USB y lector microSD

## Objetivo

Confirmar el pinmux y comportamiento de los conectores USB, alimentación/carga
por puerto y lector microSD con el DTB y kernel Armbian candidatos.

## Evidencia disponible

- El DTS candidato habilita USB host y deshabilita OTG; falta asociar cada
  función con los conectores físicos de esta revisión.
- ArkOS usa `mmc0` en `ff370000.dwmmc` y negocia SDR104. El DTB candidato usa
  el mismo controlador, GPIO de detección y capacidades UHS; el lector aún no
  se ha validado con el kernel candidato.
- ArkOS reportó `vccio_sd=1,8 V` y `vcc_sd=3,0 V`. El candidato conserva esos
  valores operativos, pero el rango ajustable de `vccio_sd` difiere.
- La consola del proyecto es R36S-V22, fecha 2024-12-18, lote 2548 (Panel 4
  V22). En ArkOS, `ff380000.dwmmc` se registra como segundo host, pero la tarjeta
  de Armbian insertada allí falla con `-ETIMEDOUT` al inicializarse. El DTS
  Armbian original solo habilitaba `ff370000`.
- El DTS Panel4-V22 publicado en AeolusUX/R36S-DTB habilita `ff380000`, usa
  SDIO en GPIO1 PC4-PC9, detección en GPIO3 PB6 y los reguladores `vcc_sd` /
  `vccio_sd`. El DTB candidato compilado habilita ese host como `mmc1`, a 50
  MHz, sin UHS, con detección activa baja y los mismos reguladores. Esto es una
  configuración de prueba derivada de la referencia; la prueba de hardware
  está registrada en la sección Estado.
- **Prueba TF2 en la R36S-V22 (2026-10-28):** Armbian `6.18.58` detectó la
  tarjeta `SC128` de 119 GiB como `/dev/mmcblk1` en `ff380000`, con negociación
  a 50 MHz y mensaje `new high speed SDXC card`. Enumeró `BOOT` (vfat), `root`
  (ext4) y `EASYROMS` (exfat). `EASYROMS` se montó primero en solo lectura y se
  listaron sus carpetas. Después se montó en lectura/escritura, se creó un
  archivo nuevo `r36s-write-test-<fecha>.txt`, se leyó su contenido tras
  `sync`, y se desmontó sin errores. Se confirma detección, lectura y escritura
  básica en esta tarjeta y consola; no se ha medido escritura sostenida ni
  probado otra tarjeta.

## Pasos: USB

1. Identificar y fotografiar cada conector, distinguir host de carga y anotar
   qué cable/adaptador se usa. No asumir que ambos puertos tienen la misma
   función eléctrica.
2. En Armbian de prueba, guardar `dmesg`, topología USB, dispositivos, PHY,
   reguladores y estado VBUS antes y después de conectar un periférico conocido.
3. Probar enumeración host con un dispositivo de bajo consumo; luego verificar
   estabilidad al retirar/reconectar. Si se necesita medir alimentación,
   utilizar medidor USB, sin provocar cortocircuitos ni sobrecarga.
4. Probar el puerto de carga por separado y coordinar el resultado con el plan
   RK817. Enumeración USB y detección de cargador son funciones distintas.
5. Ajustar host/OTG, PHY, VBUS o GPIO solo tras relacionar cada señal con el
   conector mediante inspección o esquema.

## Pasos: microSD

1. Usar una tarjeta de prueba y guardar hash/imagen base antes de probar. No
   usar la tarjeta ArkOS funcional.
2. Confirmar que el kernel enumera ambos lectores (`mmc0`/`mmc1`) y registrar
   controlador, timing negociado, frecuencia/tensión reportada, errores
   CRC/I/O y eventos de inserción. Para aislar el segundo slot, empezar con el
   modo conservador de 50 MHz sin UHS antes de probar modos más rápidos.
3. Probar lectura/escritura de archivos en la tarjeta desechable, sincronizar y
   verificar hashes; repetir reinicio en frío y extracción segura.
4. Comparar con ArkOS los reguladores `vccio_sd`/`vcc_sd`, pin de detección,
   capacidad UHS y retardo hotplug. No subir frecuencia/tensión más allá de la
   evidencia observada.
5. Si hay errores, reducir temporalmente el modo UHS como diagnóstico separado
   y comparar logs; no confundir una mejora diagnóstica con configuración
   final validada.

## Criterios de cierre

- Función de cada conector USB identificada; host y carga probados por
  separado.
- El lector opera en la tarjeta de prueba con modo/tensión registrados y sin
  errores de lectura/escritura en las verificaciones realizadas.
- Los cambios de DTB se vinculan a señales físicas observadas, no solo a la
  coincidencia con otro árbol de software.

## Estado

**Subhito microSD TF2: validado y cerrado para la tarjeta probada.** La imagen
se compiló el 2026-10-28 y pasó la verificación offline de FAT32, ext4,
estructura, `boot.scr`, DTB y U-Boot exacto. El DTB habilita `mmc1` en
`ff380000`, bus SD de 4 bits hasta 50 MHz, sin UHS. En la consola, el kernel
enumeró la tarjeta SC128 de 119 GiB como SDXC a 50 MHz; se leyó `EASYROMS` en
solo lectura y se completó una escritura pequeña, lectura de regreso, `sync` y
desmontaje limpio. No se midió rendimiento sostenido ni se validaron otras
tarjetas. La validación de conectores USB y carga continúa pendiente.
