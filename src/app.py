#!/usr/bin/env python3
"""Production inference: enrich reviews with nlptown sentiment predictions."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from sentiment_analysis import (  # noqa: E402
    PROCESSED_OUTPUT_PATH,
    RAW_REVIEWS_PATH,
    compare_to_business_average,
    load_reviews,
    load_sentiment_pipeline,
    run_inference,
    save_processed,
    sentiment_distribution,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("wlr_app")


def main() -> int:
    logger.info("Loading reviews from %s", RAW_REVIEWS_PATH)
    df = load_reviews(RAW_REVIEWS_PATH)
    logger.info("Loaded %d reviews (human avg %.2f stars)", len(df), df["human_rating"].mean())

    logger.info("Loading model once: nlptown/bert-base-multilingual-uncased-sentiment")
    classifier = load_sentiment_pipeline()

    enriched = run_inference(df, classifier)
    out_path = save_processed(enriched, PROCESSED_OUTPUT_PATH)

    summary = compare_to_business_average(enriched)
    dist = sentiment_distribution(enriched)
    logger.info("Saved %s", out_path)
    logger.info(
        "Sentiment distribution — positive: %.1f%% neutral: %.1f%% negative: %.1f%%",
        dist.get("positive", 0),
        dist.get("neutral", 0),
        dist.get("negative", 0),
    )
    logger.info(
        "Model avg %.2f vs business avg %.1f (gap %+.2f)",
        summary["model_star_average"],
        summary["business_star_average"],
        summary["gap_vs_business_avg"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
