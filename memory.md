# MEMORY DEL PROYECTO: TRINITY-AI

## Estado Actual
- **Fase Activa**: `Think` (Ideación de Modelo de Riesgo Crediticio)
- **Fecha de Inicialización**: 2026-09-26
- **Objetivo**: Desarrollar un sistema de scoring y clasificación de riesgo crediticio con explicabilidad y baja latencia (<50ms).

## Resumen de Fases de Trinity-AI
| Fase | Agente | Estado | Entregable Principal |
| :--- | :--- | :--- | :--- |
| **Think** | Estratega MLOps | 🟡 En Progreso | `docs/1_architecture_plan.md` |
| **Do** | Ingeniero MLOps | ⚪ Pendiente | `src/` & `reports/metrics.json` |
| **Docs** | Redactor Técnico | ⚪ Pendiente | `docs/3_final_pipeline.md` |

## Decisiones Arquitectónicas Registradas
- **ADR-001**: Adopción de arquitectura Human-in-the-loop desacoplada en tres agentes especialistas (`Think`, `Do`, `Docs`).
- **ADR-002**: Estándar de desarrollo en Python 3.11+ con contratos estrictos Pydantic y Type Hints en todos los módulos.
- **ADR-003**: Persistencia centralizada de métricas e historial en `reports/metrics.json` para monitoreo reactivo desde Streamlit.

## Aprendizajes y Patrones Clave
- [2026-09-26 10:55] **[Inicialización]**: Estructura base configurada bajo estándares de parsimonia y modularidad para la IBM Bob 2.0 Hackathon.

## Tareas Pendientes Inmediatas
1. Definir la variable target y features prioritarias con el usuario en la fase `Think`.
2. Consolidar el plan en `docs/1_architecture_plan.md`.
3. Iniciar la ingesta y baseline de datos en `data/raw_data.csv`.
