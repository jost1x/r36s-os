# Paquetes runtime para NEXUS

Lista de paquetes para ejecutar `nexusd`, `nexusctl` y la variante ARM64 de
`nexus-ui` en la imagen Debian Bookworm/Armbian de R36S. Esto documenta el
runtime; las dependencias de compilación (`cmake`, compilador, `*-dev`, `protoc`
y `grpc_cpp_plugin`) pertenecen al PC de desarrollo y no deben instalarse en la
consola.

## Paquetes directos

Para ejecutar la UI framebuffer y habilitar las funciones del prototipo:

```sh
apt install \
  libsdl2-2.0-0 \
  libgrpc++1.51 \
  libprotobuf32 \
  iw \
  alsa-utils \
  polkitd \
  libc-bin
```

| Paquete | Uso |
|---|---|
| `libsdl2-2.0-0` | SDL2 runtime, usado por `nexus-ui` para leer los controles físicos. |
| `libgrpc++1.51` | Runtime gRPC C++ usado por `nexus-ui`. APT incorpora `libgrpc29` y sus dependencias. |
| `libprotobuf32` | Runtime C++ de Protocol Buffers usado por `nexus-ui`; también es dependencia de gRPC en Bookworm. |
| `iw` | Estado y escaneo Wi‑Fi desde `nexusd`. |
| `alsa-utils` | Proporciona `amixer`, que `nexusd` usa para leer y cambiar el volumen. |
| `polkitd` | Autoriza las acciones de reinicio y apagado configuradas por el despliegue de NEXUS. Requiere el `systemd-logind` de la imagen. |
| `libc-bin` | Proporciona `ldconfig`, que usa el playbook para detectar qué bibliotecas del bundle ya están instaladas. No es una dependencia directa de la UI. |

`nexusd` y `nexusctl` se generan como ejecutables Go ARM64 estáticos; no
necesitan paquetes de bibliotecas compartidas propios. Sus funciones usan
herramientas y servicios del sistema: `iw`, `amixer`, `busctl` y
`systemd-logind`. `systemd` forma parte de la base de esta imagen.

## Dependencias transitivas de la UI

En Bookworm ARM64, instalar `libsdl2-2.0-0`, `libgrpc++1.51` y
`libprotobuf32` con APT es preferible a copiar individualmente cada `.so`. APT
resuelve las dependencias de ABI del repositorio, incluidas las bibliotecas de
Abseil, gRPC, TLS, audio, X11/Wayland y sus dependencias comunes. No añadir a la
lista de la imagen cada nombre como `libabsl_*.so`, `libxcb.so` o
`libwayland-*.so`: son archivos de esas dependencias y pueden variar con la
versión de Debian.

El playbook de despliegue de la UI instala directamente `libc-bin`,
`libsdl2-2.0-0`, `libgrpc++1.51` y `libprotobuf32`; después copia del bundle solo
las bibliotecas que aún no aparecen en el caché de `ldconfig`. La lista de
arriba añade `iw`, `alsa-utils` y `polkitd` para que la imagen también incluya
las utilidades que necesita el daemon para esas funciones.

La instalación de paquetes no crea los dispositivos ni permisos de hardware:
la imagen aún debe proporcionar soporte del kernel para framebuffer,
`gpio-keys`, ALSA, Wi‑Fi, batería, térmicas y backlight. El servicio necesita
acceso a `/dev/input`, `/dev/snd`, el socket de `nexusd` y los atributos sysfs
correspondientes; el despliegue configura los grupos y reglas para el
prototipo.

Referencias de paquetes para Bookworm: [`libsdl2-2.0-0`](https://packages.debian.org/bookworm/libsdl2-2.0-0), [`libgrpc++1.51`](https://packages.debian.org/bookworm/libgrpc++1.51), [`libprotobuf32`](https://packages.debian.org/bookworm/libprotobuf32), [`iw`](https://packages.debian.org/bookworm/iw), [`alsa-utils`](https://packages.debian.org/bookworm/alsa-utils) y [`polkitd`](https://packages.debian.org/bookworm/polkitd).
