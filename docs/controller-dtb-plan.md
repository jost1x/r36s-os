# Plan: ajustar y validar el mapeo de controles

## Objetivo

Dejar documentado el mapeo observado en la R36S que ejecuta Armbian de este
proyecto y, después, decidir si conviene cambiar las etiquetas o los códigos
Linux del DTB. Conservar el alcance en la unidad observada y su perfil Panel 4;
no asumir que otras revisiones R36S tienen el mismo cableado.

## Evidencia disponible

- La prueba se hizo pulsando los controles físicos mientras corría el Armbian
  construido desde `r36s-os`.
- La prueba mostró estos códigos Linux para los botones identificados:

  | Botón físico | Código decimal | Código hexadecimal | Nombre declarado hoy en DTS |
  |---|---:|---:|---|
  | SELECT | 704 | `0x2c0` | `BTN_TRIGGER_HAPPY1` / `F1` |
  | START | 705 | `0x2c1` | `BTN_TRIGGER_HAPPY2` / `F2` |
  | ZL | 706 | `0x2c2` | `BTN_TRIGGER_HAPPY3` / `F3` |
  | ZR | 707 | `0x2c3` | `BTN_TRIGGER_HAPPY4` / `F4` |
  | FN | 708 | `0x2c4` | `BTN_TRIGGER_HAPPY5` / `F5` |
  | PLUS | 115 | `0x73` | `KEY_VOLUMEUP` / `BTN-VOLUP` |
  | MINUS | 114 | `0x72` | `KEY_VOLUMEDOWN` / `BTN-VOLDOWN` |

- La tabla refleja la prueba comunicada por el usuario en Armbian. No implica
  que todos los controles se hayan validado en cada revisión de placa.
- La fuente que entra al build está dentro de
  `config/armbian/patches/kernel/r36s-6.18/0001-r36s-panel-and-device-tree.patch`.
  `device-trees/reference/rk3326-r36s-renaud.dts` es una referencia y no se
  instala directamente.
- Los códigos `704–708` llegan al sistema; sus etiquetas `F1–F5` no describen
  los nombres físicos confirmados. Aún falta decidir si basta con corregir las
  etiquetas o si las aplicaciones necesitan códigos Linux semánticos.

## Propuesta de trabajo

1. **Conservar la captura de referencia.** Registrar para cada pulsación el
   nombre del dispositivo de entrada, código decimal/hexadecimal, nombre de
   evento y transición de pulsado/liberado. Repetir una tecla a la vez y anotar
   cualquier código adicional que aparezca.
2. **Auditar colisiones.** Comparar esos resultados con todas las entradas
   `gpio-keys` del DTS candidato, especialmente `BTN_TL`, `BTN_TR`, `BTN_TL2`
   y `BTN_TR2`. No reasignar ZL/ZR a códigos de gatillo estándar si esos códigos
   ya los emiten otros GPIO.
3. **Elegir la corrección mínima.** Si el objetivo inmediato es que el nombre
   visible sea correcto, cambiar solo las etiquetas de `F1–F5` a `SELECT`,
   `START`, `ZL`, `ZR` y `FN`, manteniendo GPIO y códigos. Si se necesita
   compatibilidad con juegos/frontend, definir después códigos Linux
   semánticos sin duplicados y actualizar juntos la prueba de gamepad y su
   documentación.
4. **Actualizar la fuente del DTB y la documentación.** Modificar el DTS
   añadido por el parche de kernel, no el DTS de referencia. Actualizar la
   auditoría y el inventario para separar lo medido en esta unidad de lo que
   solo se hereda del perfil Panel 4.
5. **Verificar la compilación.** Aplicar el parche a las fuentes fijadas,
   compilar el DTB y revisar con `dtc` que GPIO, polaridad y códigos finales
   coinciden con la decisión. Verificar la imagen offline y registrar su hash.
6. **Validar en hardware.** Arrancar la imagen candidata desde una microSD de
   prueba recuperable; capturar eventos de cada botón y comprobar que el evento
   de pulsación y liberación coincide con la tabla. No modificar la tarjeta
   funcional ni el entorno persistente de U-Boot.

## Criterios de cierre

- La tabla distingue código observado, etiqueta DTS y código final instalado.
- No hay colisiones involuntarias entre botones.
- El DTB compilado contiene los GPIO, polaridades y códigos aprobados.
- La prueba en Armbian confirma individualmente cada botón y su liberación.
- La documentación identifica explícitamente unidad/perfil probado y límites
  de generalización.

## Estado

Plan preparado. La prueba física de los códigos 704–708, 115 y 114 ya fue
realizada por el usuario en el Armbian de este proyecto. La auditoría de
colisiones, cualquier cambio al DTS y la validación de una imagen posterior
quedan pendientes; este documento no afirma que se haya recompilado ni probado
una corrección.
