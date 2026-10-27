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
2. Confirmar que el kernel enumera el lector y registrar bus, timing negociado,
   frecuencia/tensión reportada, errores CRC/I/O y eventos de inserción.
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

Plan preparado. La detección de `mmc0` y el soporte USB están descritos por
software; falta validación funcional de los conectores con Armbian.
