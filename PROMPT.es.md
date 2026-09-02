# PROMPT.es.md — EDA con agente de código (WeLoveReviews)

> Usa el contenido **debajo de esta cabecera** como prompt para el agente. El agente debe trabajar en `src/explore.ipynb`, hacer exploración, generar insights y proponer limpieza. **No** debe implementar inferencia ni modelado; eso queda para el desarrollador en el mismo notebook y en `src/app.py`.

---

Explora el dataset `data/raw/reviews.csv` (500 reseñas de clientes de negocios de servicio) y documenta en `src/explore.ipynb`:

1. **Dimensiones y tipos** — filas, columnas, nulos, duplicados.
2. **Estadísticos de `human_rating`** — media, distribución; contrasta con la media de negocio **4.5 estrellas**.
3. **Longitud del texto** — caracteres/palabras; idiomas presentes (EN/ES).
4. **Ejemplos cualitativos** — reseñas muy positivas vs neutrales en texto con rating alto.
5. **Propuesta de limpieza** — qué normalizar antes de inferencia (sin eliminar filas salvo duplicados exactos).
6. **Hipótesis de negocio** — ¿el texto parece tan positivo como 4.5 estrellas?

Entrega celdas markdown breves entre bloques de código. No cargues modelos Hugging Face en esta fase.
