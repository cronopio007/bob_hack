---
name: pattern-matcher
description: Analiza repositorios externos y bases de código para detectar anti-patrones y recomendar patrones de diseño MLOps limpios, modulares y parsimoniosos.
---

# Pattern Matcher Skill

## Propósito
Esta habilidad permite a los agentes de Trinity-AI inspeccionar repositorios externos, librerías o código de referencia para extraer las mejores prácticas arquitectónicas e identificar patrones de diseño recomendados.

## Flujo de Trabajo
1. **Inspección de Estructura**:
   - Mapear el árbol de directorios y la modularidad de componentes (ingesta, ingeniería de características, entrenamiento, inferencia).
   - Identificar responsabilidades únicas (SRP) y separación de capas.
2. **Detección de Anti-Patrones**:
   - Monolitos de entrenamiento en scripts sueltos o notebooks desordenados.
   - Acoplamiento fuerte entre la ingesta de datos y los estimadores de Machine Learning.
   - Ausencia de tipado (`Type Hints`) y validación de entradas.
3. **Recomendación de Patrones Limpios**:
   - **Pipeline Pattern**: Encapsulamiento de pasos transformadores deterministas e idempotentes.
   - **Strategy Pattern**: Intercambio dinámico de algoritmos de scoring o técnicas de imputación.
   - **Repository / Data Access Pattern**: Desacoplamiento entre almacenamiento y procesamiento.
   - **Schema Contract Pattern**: Uso de esquemas Pydantic / dataclasses para validar transferencias de datos entre agentes y etapas.

## Formato de Salida Esperado
Cada recomendación debe emitirse estructurada:
- **Patrón Identificado**: Nombre del patrón.
- **Justificación**: Ventaja en mantenimiento, velocidad o reducción de deuda técnica.
- **Ejemplo Mínimo Viable**: Fragmento Python parsimonioso (< 15 líneas) ilustrando la adopción.
