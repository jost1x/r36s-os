# AGENTS.md

## Proyecto

Sistema experimental basado en Armbian para la R36S original. La configuración apunta a una unidad observada con perfil Panel 4; no generalices compatibilidad a otras revisiones. Antes de cambiar alcance o reportar estado, consulta `README.md` y `docs/phase-status.md`. Separa evidencia, hipótesis y pendientes.

## Forma de trabajo

- Antes de editar, revisa `git status`, instrucciones locales y archivos relacionados; agrupa lecturas independientes. Conserva cambios preexistentes y limita el diff a la tarea.
- Identifica desde el inicio entregables y verificaciones pertinentes; completa el cambio y verifica todo lo posible en la misma pasada.
- Resuelve ambigüedades con una suposición conservadora y explícitala. Usa la evidencia del repo antes de preguntar; pregunta solo si falta un dato bloqueante o cambia materialmente una decisión.
- No escribas dispositivos, tarjetas ni almacenamiento de la consola sin petición explícita. No declares pruebas o validación de hardware sin evidencia.
- Ejecuta verificaciones pertinentes y reporta resultados y límites con precisión. Actualiza documentación existente en vez de duplicarla.

## Mapa del repositorio

- `README.md`, `docs/`: alcance, estado, auditorías y planes.
- `config/armbian/`, `extensions/`: placa WIP, parches y build.
- `scripts/`: build, diagnóstico y verificación de imágenes.
- `device-trees/`: DTS; `reference/`: artefactos ArkOS de referencia, no especificación universal.
- `work/`: salidas locales; no versionar builds ni secretos.

## Cambios de sistema e imagen

- Conserva `config/armbian/ARMBIAN_COMMIT` y digests fijados; justifica cualquier actualización.
- Build aislado: `scripts/build-armbian.sh prepare` y `scripts/build-armbian.sh build` (ver provisioning local en README).
- Prioriza la caché y artefactos ya compilados en `work/armbian-build`; evita limpiezas o rebuilds completos si basta una compilación incremental. Invalida la caché solo cuando sea necesario y explica por qué.
- Usa el provisioning `.example`; nunca registres secretos en archivos, logs o documentación versionados.
- Mantén los parches compatibles con las fuentes fijadas y documenta evidencia/límites. La verificación estática no prueba hardware.
- `scripts/verify-image.py` abre imágenes regulares en solo lectura; no agregues flasheo automático.

## Estilo y comunicación

- Conserva el idioma del archivo (documentación principalmente en español); usa nombres técnicos y frases directas.
- En diagnósticos, comunica observación, hipótesis si aplica, límite y siguiente paso. En trabajos de varias etapas, da actualizaciones breves.
- Al final, resume cambios, verificaciones y pendientes relevantes sin repetir el diff.

## Commits

Usa Conventional Commits en inglés: `<type>(<scope>): <imperative summary>`. Tipos: `feat`, `fix`, `docs`, `build`, `refactor`, `test`, `chore`; ámbitos sugeridos: `armbian`, `kernel`, `uboot`, `diagnostics`, `docs`.

- Confirma solo si se solicita o la tarea lo requiere; revisa diff y staging e incluye solo archivos de la tarea.
- Escribe asunto y cuerpo en inglés. Para incompatibilidades, añade `BREAKING CHANGE:` en el cuerpo.

Examples: `docs: document first-image workflow`; `fix(kernel): detect RK817 DC input`.
