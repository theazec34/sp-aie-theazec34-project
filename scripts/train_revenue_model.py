#!/usr/bin/env python3
"""Backward-compatible entrypoint — delegates to ``train_sales_forecast``."""

from __future__ import annotations

from train_sales_forecast import candidate_models, main

__all__ = ["candidate_models", "main"]

if __name__ == "__main__":
    raise SystemExit(main())
