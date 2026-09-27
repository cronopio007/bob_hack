name: project-context
description: Restaura el contexto completo del proyecto leyendo memory.md, changelog.md y reportes. Orienta a Bob sobre la fase activa, decisiones de arquitectura y próximos pasos sin re-escanear todo el repositorio.
user-invocable: true
---

Cuando este skill sea invocado (mediante `/project-context` o automáticamente al inicio de una sesión):

1. **Lectura de Memoria**: Lee inmediatamente el archivo `memory.md` en la raíz del proyecto para identificar:
   - Estado y fase actual del desarrollo (Think, Do o Docs).
   - Decisiones de Arquitectura (ADRs) registradas.
   - Restricciones no negociables vigentes.

2. **Inspección de Artefactos**:
   - Revisa `reports/metrics.json` para conocer el último estado de las métricas de ML.
   - Revisa `changelog.md` para ver los últimos componentes implementados en `src/`.
   - Revisa los contratos en `docs/1_architecture_plan.md` y `docs/2_data_strategy.md`.

3. **Output de Rehidratación**:
   Genera un reporte conciso de 3 puntos:
   - **Estado Actual**: Dónde nos quedamos en la última sesión.
   - **Artefactos Clave Disponibles**: Resumen de los archivos listos en `src/`, `docs/` y métricas actuales.
   - **Próxima Acción Sugerida**: La tarea prioritaria para continuar el flujo sin fricción.

No inventes estado previo. Basa tu resumen estrictamente en lo documentado en `memory.md` y los archivos del workspace.
