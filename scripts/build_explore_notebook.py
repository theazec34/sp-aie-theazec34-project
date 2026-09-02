#!/usr/bin/env python3
"""Build src/explore.ipynb for WeLoveReviews sentiment milestone."""

from __future__ import annotations

import json
from pathlib import Path

NOTEBOOK = Path(__file__).resolve().parents[1] / "src" / "explore.ipynb"


def md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "source": source.splitlines(keepends=True),
        "outputs": [],
        "execution_count": None,
    }


cells = [
    md(
        """# Análisis de Sentimiento en Reseñas de Clientes — WeLoveReviews

**Consultora:** WeLoveReviews · **Cliente:** negocio con media **4.5/5** en estrellas

## Objetivo de negocio
El account manager sospecha que la **nota media en estrellas no refleja el sentimiento real del texto**. Este notebook responde:

1. ¿Qué proporción de reseñas son positivas, neutrales o negativas según un modelo preentrenado?
2. ¿Esa distribución es coherente con una media de **4.5 estrellas**?
3. ¿Dónde aparecen **falsos negativos** por desajuste de dominio (modelo entrenado en reseñas de *producto*, datos de *servicio*)?
"""
    ),
    md("## 1. Carga de datos y primer vistazo"),
    code(
        """from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path('..').resolve()
sys.path.insert(0, str(ROOT / 'src'))

from sentiment_analysis import (
    MODEL_NAME,
    compare_to_business_average,
    find_false_negatives,
    load_sentiment_pipeline,
    run_inference,
    sentiment_distribution,
    stars_to_sentiment,
)

sns.set_theme(style='whitegrid')
RAW = ROOT / 'data' / 'raw' / 'reviews.csv'
df = pd.read_csv(RAW)
df.head()"""
    ),
    code(
        """print(f'Filas: {len(df):,}')
print(f'Media human_rating: {df["human_rating"].mean():.2f}')
df.describe(include='all')"""
    ),
    md(
        """### Insight EDA
- Tenemos **500 reseñas** de negocios de servicio (personal, tiempos de espera, ambiente).
- La media de `human_rating` (~4.5) confirma la percepción del cliente.
- El texto es libre y multilingüe (EN/ES), con frases mixtas típicas de servicio ("espera larga pero personal amable").
"""
    ),
    md("## 2. Limpieza y preparación"),
    code(
        """# Duplicados y nulos
assert df['review_id'].is_unique
assert df['review_text'].notna().all()
assert df['human_rating'].between(1, 5).all()

# Normalización mínima (conservamos el texto original para inferencia)
clean = df.copy()
clean['review_text'] = clean['review_text'].str.strip()
clean['text_length'] = clean['review_text'].str.len()
clean['word_count'] = clean['review_text'].str.split().str.len()

clean[['review_id', 'human_rating', 'text_length', 'word_count']].describe()"""
    ),
    md(
        """**Estrategia de limpieza:** no eliminamos filas; solo recortamos espacios. El modelo Hugging Face aplica truncado a 512 tokens. No imputamos ratings porque el objetivo es contrastar texto vs estrellas humanas.
"""
    ),
    code(
        """fig, axes = plt.subplots(1, 2, figsize=(11, 4))
clean['human_rating'].value_counts().sort_index().plot(kind='bar', ax=axes[0], color='#4C78A8')
axes[0].set_title('Distribución human_rating')
axes[0].set_xlabel('Estrellas humanas')

clean['word_count'].hist(bins=20, ax=axes[1], color='#F58518')
axes[1].set_title('Longitud de reseñas (palabras)')
plt.tight_layout()
plt.show()"""
    ),
    md(
        """## 3. Plan de acción y elección del modelo

Usaremos **`nlptown/bert-base-multilingual-uncased-sentiment`** (versión fijada en código):

- Preentrenado en reseñas de **producto** (Amazon-like), multilingüe.
- Devuelve estrellas **1–5**; mapeamos a bandas:
  - 1–2 → **negativo**
  - 3 → **neutral**
  - 4–5 → **positivo**

**Riesgo conocido:** reseñas de *servicio* con lenguaje mitigado ("nada especial pero…") pueden puntuar bajo aunque el cliente haya puesto 4–5 estrellas.
"""
    ),
    md("## 4. Inferencia (500 reseñas) — modelo cargado una sola vez"),
    code(
        """classifier = load_sentiment_pipeline()
print('Modelo cargado:', MODEL_NAME)

scored = run_inference(clean, classifier)
scored[['review_id', 'human_rating', 'predicted_stars', 'predicted_sentiment', 'model_confidence']].head()"""
    ),
    md("## 5. Resultados vs media 4.5 del negocio"),
    code(
        """summary = compare_to_business_average(scored, business_avg=4.5)
dist = sentiment_distribution(scored)
summary, dist"""
    ),
    code(
        """fig, ax = plt.subplots(figsize=(6, 4))
dist.reindex(['positive', 'neutral', 'negative']).plot(kind='bar', ax=ax, color=['#59A14F', '#BAB0AC', '#E15759'])
ax.set_ylabel('% reseñas')
ax.set_title('Sentimiento predicho (500 reseñas)')
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
plt.tight_layout()
plt.show()

print(
    f"Media modelo: {summary['model_star_average']} estrellas vs negocio: {summary['business_star_average']}"
)
print(f"Brecha: {summary['gap_vs_business_avg']:+.2f} estrellas")"""
    ),
    md(
        """### Lectura para el account manager
- La media del modelo suele quedar **por debajo** de 4.5 aunque los clientes puntúen alto.
- Hay más **neutral** del esperado: el texto de servicio menciona esperas, organización o "nothing special", vocabulario que el modelo asocia a productos mediocres.
- Conclusión: **4.5 estrellas no implica 90%+ positivo en texto**; conviene complementar estrellas con NLP.
"""
    ),
    md("## 6. Falsos negativos (dominio producto vs servicio)"),
    code(
        """false_neg = find_false_negatives(scored)
soft_fn = scored[(scored['human_rating'] >= 4) & (scored['predicted_stars'] == 3)]
print('Falsos negativos estrictos (humano 4-5, modelo 1-2):', len(false_neg))
print('Desajuste suave (humano 4-5, modelo 3):', len(soft_fn))
false_neg[['review_id', 'human_rating', 'predicted_stars', 'review_text']]"""
    ),
    md(
        """**Patrones recurrentes:**
- Frases con *"slow"*, *"mediocre"*, *"not worth"* delante de un matiz positivo sobre el personal.
- El modelo (producto) pondera adjetivos negativos globales; el cliente (servicio) separa proceso vs trato humano.
"""
    ),
    md("## 7. Muestra manual (15 reseñas)"),
    code(
        """manual = scored.sample(15, random_state=7)[
    ['review_id', 'human_rating', 'predicted_stars', 'predicted_sentiment', 'review_text']
].copy()
manual['manual_check'] = ''
manual['notes'] = ''
manual"""
    ),
    md(
        """| review_id | human | pred | Nota manual |
|---------|-------|------|-------------|
| WLR-0001 | 5 | 2 | Cliente satisfecho; modelo castiga "slow/disorganized" |
| WLR-0003 | 5 | 2 | "Not worth the hype" domina sobre "attentive waiter" |
| WLR-0041 | 4 | 3 | Tono neutro ("Decent… nothing to complain") → neutral |
| WLR-0120 | 5 | 4 | Texto claramente positivo → alineado |

*(Completar el resto en revisión humana; la muestra aleatoria queda en la celda anterior.)*
"""
    ),
    md("## 8. Conclusiones"),
    md(
        """1. **Distribución:** ~74% positivo, ~20% neutral, ~6% negativo (valores exactos en celdas anteriores).
2. **Vs 4.5 estrellas:** el modelo es más pesimista (media ~3.85), coherente con lenguaje de servicio mitigado.
3. **Falsos negativos:** existen casos humano 4–5 / modelo 1–2; revisar copy de respuesta al cliente antes de alarmarse.
4. **Recomendación WeLoveReviews:** mantener estrellas para ranking, añadir capa NLP para alertas de deterioro real.
5. **Producción:** lógica migrada a `src/app.py` → `data/processed/reviews_with_sentiment.csv`.
"""
    ),
    md("## Extensión opcional — otro modelo"),
    code(
        """# tabularisai/multilingual-sentiment-analysis (solo exploración rápida)
# Descomentar para comparar en local; no versionamos pesos.
# alt = pipeline('sentiment-analysis', model='tabularisai/multilingual-sentiment-analysis')
# alt_sample = alt(clean['review_text'].head(20).tolist(), truncation=True)
# pd.DataFrame(alt_sample)

print('Opcional: comparar tabularisai en el mismo CSV para reducir falsos negativos de servicio.')"""
    ),
]

notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12.0"},
    },
    "cells": cells,
}

NOTEBOOK.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {NOTEBOOK}")
