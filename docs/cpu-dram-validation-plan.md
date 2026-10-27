# Plan: validar perfil de CPU y memoria DRAM

## Objetivo

Comprobar que los OPP/reguladores de CPU del DTB candidato son estables y que
el perfil DRAM seleccionado por U-Boot corresponde a la memoria montada en la
unidad observada.

## Evidencia disponible

- ArkOS llegó a 1,512 GHz en una muestra con `vdd_arm=1,30 V`; el candidato
  limita el perfil PX30 a 1,296 GHz y el OPP superior solicita 1,35 V.
- La temperatura observada fue una lectura instantánea, no una prueba sostenida.
- Linux reporta aproximadamente 1 GiB, pero no identifica el estándar de DRAM.
  El TPL candidato selecciona familia DDR3; el tipo/modelo del chip sigue sin
  identificarse y LPDDR3 es una incertidumbre de compatibilidad.

## Pasos: CPU y reguladores

1. Guardar la tabla OPP, límites del regulador, governor y lecturas de
   temperatura/frecuencia en reposo en ArkOS y Armbian; registrar kernel y DTB.
2. Inspeccionar el marcado del SoC/placa y comparar el DTS con los rangos
   permitidos por el regulador. No tomar una lectura instantánea de ArkOS como
   autorización para reducir voltajes.
3. En imagen de prueba, hacer carga gradual y breve, supervisando throttling,
   errores, reinicios y temperaturas. Definir límites conservadores y detener
   la prueba ante comportamiento anómalo.
4. Probar cualquier cambio de OPP o voltaje por separado. Compilar una imagen,
   revisar el DTB extraído y repetir exactamente la misma carga antes/después.
5. Mantener 1,296 GHz como límite candidato hasta que exista una razón medida
   para cambiarlo y estabilidad repetible en esa unidad.

## Pasos: DRAM y arranque

1. Fotografiar la revisión de PCB y leer el marcado del chip RAM. Buscar su
   datasheet para confirmar protocolo, densidad, organización y tensiones.
2. Si el marcado no es legible, no inferir el tipo por la capacidad reportada
   ni por referencias comunitarias. Mantener el perfil TPL actual como
   hipótesis no confirmada.
3. Contrastar el perfil seleccionado por TPL/U-Boot y sus parámetros con el
   datasheet; confirmar fuente de reloj, timings y alimentación disponibles.
4. En microSD de prueba con captura UART, registrar desde SPL/TPL hasta Linux,
   probar varios arranques en frío y revisar errores de memoria. No modificar
   variables U-Boot persistentes ni el medio funcional.
5. Cambiar el perfil DRAM solo si la identificación física o evidencia de
   arranque exige el cambio; conservar imagen recuperable y capturas UART.

## Criterios de cierre

- El perfil DRAM se vincula al chip identificado o queda explícitamente
  pendiente, sin afirmar compatibilidad física.
- La CPU pasa pruebas repetibles bajo carga con OPP/voltajes documentados y
  temperaturas medidas; no se extrapola desde una única muestra.
- La imagen y el método de recuperación quedan registrados.

## Estado

Plan preparado. La frecuencia candidata está limitada conservadoramente; la
identidad física de la RAM y la estabilidad sostenida aún no están validadas.
