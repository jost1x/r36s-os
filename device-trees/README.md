# Device trees de R36S

El perfil Armbian `.wip` usa ahora `rk3326-r36s-panel4.dtb`, agregado al árbol
Linux fijado mediante
[`0001-r36s-panel-and-device-tree.patch`](../config/armbian/patches/kernel/r36s-6.18/0001-r36s-panel-and-device-tree.patch).
La imagen construida incluye ese DTB y el módulo NV3051D, pero no se ha
validado en hardware. El perfil se limita a la configuración Panel 4
seleccionada en software por la unidad observada; no pretende cubrir las
demás variantes R36S.

Existe una referencia específica con licencia declarada: DTS
`rk3326-r36s.dts` en [AndreRenaud/linux-r36s, commit
`ba832b723d70318be2bdf65aff344194a807e6f5`](https://github.com/AndreRenaud/linux-r36s/tree/ba832b723d70318be2bdf65aff344194a807e6f5).
Su SPDX es `(GPL-2.0+ OR MIT)`. El driver de pantalla asociado declara
`GPL-2.0`; el patch porta su variante R36S al driver NV3051D de Armbian y
conserva su atribución.

La copia exacta del DTS auditado se conserva como referencia en
[`reference/rk3326-r36s-renaud.dts`](reference/rk3326-r36s-renaud.dts); su
SHA-256 y resultados de compilación preliminar están en la auditoría. Este
archivo no está conectado al build ni sustituye el perfil `.wip`.

La secuencia R36S añadida al driver NV3051D procede de
[`panel-newvision-nv3051d.c` en linux-r36s, commit `ba832b723d70318be2bdf65aff344194a807e6f5`](https://github.com/AndreRenaud/linux-r36s/blob/ba832b723d70318be2bdf65aff344194a807e6f5/drivers/gpu/drm/panel/panel-newvision-nv3051d.c#L242-L350).
El archivo declara `GPL-2.0`; el patch de este proyecto incorpora su origen y
commit junto a la secuencia adaptada a los helpers DSI multi-contexto de Linux
6.18.

La comparación con la unidad inspeccionada está en
[`docs/r36s-dts-audit.md`](../docs/r36s-dts-audit.md). El DTS de referencia
coincide en resolución, geometría y pin de reset; el patch propio usa los
29 MHz observados en ArkOS Panel 4 en vez de los 24,15 MHz de la referencia.
El controlador sigue siendo una hipótesis de software, no una lectura
electrónica del panel.

La lectura local del DTB ArkOS de esta misma unidad encontró `ramoops` con
una región reservada de 960 KiB desde `0x00110000`, un búfer de consola de
512 KiB y registros de 128 KiB. El DTB Armbian del proyecto incorpora esa
configuración para conservar mensajes del kernel entre reinicios. Esto es
una referencia observada en esta unidad; no confirma todavía que el firmware
preserve la RAM durante un reinicio por software. La imagen candidata que la
incluye se compiló y verificó offline; falta validarla en la consola.

No copiar la secuencia binaria del DTB ArkOS: su licencia/procedencia no se ha
resuelto. El patch usa la secuencia del driver R36S publicado bajo GPL-2.0; sus
153 registros principales coinciden con los del DTB Panel 4 local. El patch
compila, pero la compatibilidad física solo puede establecerse en una microSD
de prueba con UART y recuperación disponible.
