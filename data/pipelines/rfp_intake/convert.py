"""PDF → Markdown via MarkItDown (+ readability metrics)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def pdf_to_markdown(pdf_path: str | Path) -> str:
    """Convert PDF (or text-like) to Markdown using MarkItDown."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(str(path))

    # Allow .md fixtures in tests without MarkItDown
    if path.suffix.lower() in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")

    from markitdown import MarkItDown

    md = MarkItDown()
    result = md.convert(str(path))
    text = getattr(result, "text_content", None) or str(result)
    return text.strip()


def compute_readability(markdown: str) -> dict[str, Any]:
    """Flesch-Kincaid + Gunning Fog via py-readability-metrics when possible."""
    text = re.sub(r"[#*_>`\[\]()]", " ", markdown or "")
    text = re.sub(r"\s+", " ", text).strip()
    words = [w for w in re.split(r"\s+", text) if w]
    word_count = len(words)
    out: dict[str, Any] = {
        "word_count": word_count,
        "flesch_kincaid": None,
        "gunning_fog": None,
    }
    if word_count < 10:
        return out
    try:
        from readability import Readability

        r = Readability(text)
        try:
            out["flesch_kincaid"] = float(r.flesch_kincaid().score)
        except Exception:  # noqa: BLE001
            pass
        try:
            out["gunning_fog"] = float(r.gunning_fog().score)
        except Exception:  # noqa: BLE001
            pass
    except Exception:  # noqa: BLE001
        # Fallback heuristic
        sentences = max(1, len(re.findall(r"[.!?]+", text)))
        syllables = max(1, sum(_approx_syllables(w) for w in words))
        out["flesch_kincaid"] = round(
            0.39 * (word_count / sentences) + 11.8 * (syllables / word_count) - 15.59, 2
        )
        complex_words = sum(1 for w in words if _approx_syllables(w) >= 3)
        out["gunning_fog"] = round(
            0.4 * ((word_count / sentences) + 100 * (complex_words / word_count)), 2
        )
    return out


def _approx_syllables(word: str) -> int:
    w = re.sub(r"[^a-záéíóúüñ]", "", word.lower())
    if not w:
        return 1
    groups = re.findall(r"[aeiouáéíóúü]+", w)
    return max(1, len(groups))
