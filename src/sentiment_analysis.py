"""Shared sentiment inference helpers for WeLoveReviews (notebook + app)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

MODEL_NAME = "nlptown/bert-base-multilingual-uncased-sentiment"

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_REVIEWS_PATH = REPO_ROOT / "data" / "raw" / "reviews.csv"
PROCESSED_OUTPUT_PATH = REPO_ROOT / "data" / "processed" / "reviews_with_sentiment.csv"


def stars_to_sentiment(stars: int) -> str:
    """Map 1–5 star rating to negative / neutral / positive bands."""
    if stars <= 2:
        return "negative"
    if stars == 3:
        return "neutral"
    return "positive"


def parse_predicted_stars(label: str) -> int:
    """Parse Hugging Face label such as ``'4 stars'`` → ``4``."""
    return int(str(label).split()[0])


def load_sentiment_pipeline():
    """Load the pinned Hugging Face model once (weights are not stored in repo)."""
    from transformers import pipeline

    return pipeline(
        "sentiment-analysis",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
    )


def run_inference(df: pd.DataFrame, classifier, *, text_col: str = "review_text") -> pd.DataFrame:
    """Run batch inference; model is loaded once outside this function."""
    texts = df[text_col].astype(str).tolist()
    outputs = classifier(texts, truncation=True, max_length=512)

    predicted_stars = [parse_predicted_stars(item["label"]) for item in outputs]
    out = df.copy()
    out["predicted_stars"] = predicted_stars
    out["predicted_sentiment"] = [stars_to_sentiment(s) for s in predicted_stars]
    out["model_confidence"] = [float(item["score"]) for item in outputs]
    out["model_name"] = MODEL_NAME
    return out


def load_reviews(path: Path | None = None) -> pd.DataFrame:
    path = path or RAW_REVIEWS_PATH
    df = pd.read_csv(path)
    required = {"review_id", "review_text", "human_rating"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")
    return df


def sentiment_distribution(df: pd.DataFrame, column: str = "predicted_sentiment") -> pd.Series:
    return df[column].value_counts(normalize=True).mul(100).round(1)


def compare_to_business_average(
    df: pd.DataFrame,
    *,
    business_avg: float = 4.5,
    stars_col: str = "predicted_stars",
) -> dict[str, Any]:
    model_avg = float(df[stars_col].mean())
    dist = sentiment_distribution(df).to_dict()
    return {
        "business_star_average": business_avg,
        "model_star_average": round(model_avg, 2),
        "positive_pct": dist.get("positive", 0.0),
        "neutral_pct": dist.get("neutral", 0.0),
        "negative_pct": dist.get("negative", 0.0),
        "gap_vs_business_avg": round(model_avg - business_avg, 2),
    }


def find_false_negatives(df: pd.DataFrame) -> pd.DataFrame:
    """Human 4–5 stars but model predicts 1–2 (domain-mismatch pattern)."""
    mask = (df["human_rating"] >= 4) & (df["predicted_stars"] <= 2)
    return df.loc[mask].copy()


def save_processed(df: pd.DataFrame, path: Path | None = None) -> Path:
    path = path or PROCESSED_OUTPUT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path
