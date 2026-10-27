# Plan: validar batería y calibrar sus datos declarados

## Objetivo

Determinar qué propiedades de batería del DTB candidato describen el pack
instalado y cuáles deben ajustarse. No tratar los datos copiados de ArkOS como
mediciones de capacidad o calibración.

## Evidencia disponible

- El candidato declara 3380 mAh, 100 mΩ y una curva OCV de 21 puntos portada
  desde el DTB Panel 4 de ArkOS.
- ArkOS informó `charge_full=3380000 µAh`; esto refleja el valor del driver,
  no una medición independiente de capacidad.
- En una prueba con Armbian el cargador no se detectó correctamente. Resolver
  primero la ruta RK817 indicada en
  [el plan de detección del cargador](rk817-charger-detection-plan.md).

## Pasos

1. Fotografiar etiqueta y dimensiones del pack, registrar fabricante/modelo,
   química, tensión nominal y límites impresos. No abrir ni perforar el pack.
2. Revisar contra el binding y driver exactos qué significan capacidad,
   resistencia, tensión de diseño, terminación y curva OCV. Marcar cada dato
   como valor del fabricante, lectura reportada o medición.
3. Tras reparar la detección de cargador, registrar telemetría a intervalos
   durante ciclos normales de carga y uso: tensión, corriente, temperatura,
   estado, `charge_now`, `charge_full` y nivel reportado. No forzar descarga
   profunda ni modificar límites de protección.
4. Comparar carga completa y descenso normal con un medidor externo apropiado
   si se necesita estimar capacidad real; documentar precisión e incertidumbre.
   No inferir mAh reales de una sola lectura de porcentaje/OCV.
5. Cambiar una propiedad por vez y justificarla con especificación o medición.
   Mantener la curva OCV existente hasta disponer de muestras de reposo con
   niveles de carga conocidos y temperatura registrada.
6. Compilar la imagen, extraer el DTB, comprobar las propiedades finales y
   validar telemetría en una tarjeta de prueba antes de promover los valores.

## Criterios de cierre

- Se identifica el pack o se declara explícitamente que su modelo sigue
  desconocido.
- Cada propiedad final tiene fuente, unidad y nivel de confianza documentados.
- La carga y la descarga normal reportan estados coherentes; no se presentan
  lecturas del driver como mediciones independientes.

## Estado

Plan preparado. Capacidad, resistencia y curva permanecen provisionales; la
detección del cargador aún es un prerrequisito para validar telemetría.
