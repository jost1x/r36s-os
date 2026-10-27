# Plan: integrar y validar la detección del cargador RK817

## Objetivo

Investigar por qué el kernel candidato no refleja conexión/desconexión del
cargador y definir una integración mantenible para la señal física
`GPIO0_PB3` (`dc_det`) de la unidad observada.

## Evidencia disponible

- En ArkOS, con el cargador conectado, `ac/online=1`; en Armbian se observó
  repetidamente `rk817-charger/online=0` y `Not charging`.
- En Armbian, la lectura de `GPIO0_PB3` cambió de 0 desconectado a 1 conectado.
- El driver mainline 6.18 usa estado/IRQ internos del RK817 y no consume la
  propiedad BSP `dc_det_gpio`. Agregar esa propiedad al DTB sin cambiar el
  driver no conecta la señal al subsistema de alimentación.

## Pasos

1. Confirmar contra el commit exacto del kernel fijado el árbol del driver,
   binding y rutas de IRQ del RK817. Registrar qué eventos internos se esperan
   y qué power supplies deben actualizarse.
2. Definir la interfaz DT mantenible para la línea, preferentemente un
   descriptor GPIO estándar (`dc-det-gpios`) documentado en el binding. No
   copiar nombres privados del BSP sin revisar semántica y polaridad.
3. Diseñar el cambio del driver para leer el nivel inicial, solicitar IRQ de
   ambos flancos, actualizar estado/notificaciones de `power_supply` y manejar
   errores, suspensión y liberación del recurso. Evitar habilitar carga usando
   una señal cuyo sentido todavía no se haya validado.
4. Revisar contención: comprobar que PB3 no esté reclamado por otro nodo y que
   la polaridad activa alta observada corresponda al nivel lógico esperado.
5. Compilar driver y DTB desde el build fijado; inspeccionar el DTB extraído de
   la imagen y verificar los mensajes de probe/IRQ en logs.
6. En microSD de prueba, dejar inicialmente el cargador desconectado; registrar
   GPIO, `online`, `status` e IRQs. Conectar y desconectar una vez en momentos
   anotados, repetir y comprobar que cada flanco actualiza estado y notifica a
   userspace. Revisar también arranque con cargador ya conectado.

## Criterios de cierre

- La propiedad GPIO está documentada y validada por el binding.
- Los flancos físicos se reflejan correctamente en el power supply sin IRQs
  perdidas, estados trabados ni regresiones al arrancar/desconectar.
- La verificación estática y la prueba en hardware se reportan por separado.

## Estado

Plan preparado. La diferencia de ruta entre BSP y mainline y el nivel GPIO ya
están observados; la modificación del driver y su prueba siguen pendientes.
