"""End-to-end detect + classify (+ optional board stage)."""

from rummikub.pipeline.detect_and_classify import classify_crop, load_classifier

__all__ = ["load_classifier", "classify_crop"]
