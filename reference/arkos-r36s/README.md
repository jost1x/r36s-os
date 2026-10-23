# Archivos de referencia de ArkOS

Snapshot de solo lectura obtenido por SSH desde `/boot` en la unidad descrita en [el inventario](../../docs/hardware-inventory.md), el 2026-10-23.

## Contenido

- `boot/boot.ini`: configuración de arranque encontrada en la raíz de `/boot`.
- `boot/rk3326-r35s-linux.dtb`: DTB encontrado en la raíz de `/boot`.
- `boot/ScreenFiles/`: directorios de variantes de panel, con los `PID.txt`, configuraciones, DTB y demás archivos que contenían. Se preservaron en su estructura original para poder comparar variantes. El directorio incluye una imagen `Panel 5/Image`.
- `SHA256SUMS`: hashes SHA-256 de los archivos importados, para detectar cambios accidentales.

La integridad del snapshot se comprobó localmente con `sha256sum -c reference/arkos-r36s/SHA256SUMS`: las 50 entradas verificaron `OK` el 2026-10-23. Repetir la comprobación después de copiar o mover esta carpeta.

## Uso y cautelas

Estos archivos son evidencia de la instalación ArkOS de una unidad concreta, no componentes aprobados para la imagen R36S Hybrid OS. No se han identificado de forma independiente las versiones o la procedencia aguas arriba de cada archivo. El repositorio público AeolusUX/R36S-DTB declara CC BY-NC-ND 4.0, pero no se ha verificado que cada archivo local provenga exactamente de esa publicación; tratar el snapshot como referencia privada y no redistribuirlo ni crear derivados a partir de él hasta aclarar los derechos. No flashear ni instalar estos binarios como parte del flujo de construcción.

No se copiaron el kernel `/boot/Image` ni el initramfs `/boot/uInitrd` de la raíz. La copia no incluye ROMs ni datos de usuario.
