---
name: learnings
description: Extrae aprendizajes clave, decisiones técnicas y lecciones aprendidas durante la sesión para consolidarlos de forma incremental en memory.md.
---

# Learnings Extractor Skill

## Propósito
Permite a los agentes de Trinity-AI capturar conocimiento operativo de alto valor generado durante las iteraciones de desarrollo, asegurando persistencia de contexto y evitando regresiones o repetición de errores.

## Triggers de Activación
- Finalización de una fase (`Think`, `Do`, `Docs`).
- Resolución exitosa de un bug o cuello de botella de rendimiento.
- Consenso de una decisión arquitectónica clave con el usuario.

## Protocolo de Extracción
1. **Identificar Hallazgos**:
   - Hipótesis validadas o refutadas en los datos.
   - Trucos de rendimiento o librerías específicas adoptadas.
   - Directivas y preferencias del usuario durante la iteración.
2. **Actualizar `memory.md`**:
   - Localizar la sección `## Aprendizajes y Patrones Clave`.
   - Agregar una entrada fechada con el siguiente formato:
     ```markdown
     - [AAAA-MM-DD HH:MM] **[Categoría]**: Síntesis del aprendizaje y su impacto en el pipeline.
     ```
3. **Validación de Concisión**:
   - Evitar redundancias y explicaciones verbosas.
   - Máximo 2 oraciones por punto de aprendizaje.
