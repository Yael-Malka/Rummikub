"""Shared folder paths — use these instead of string literals."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR     = PROJECT_ROOT / "data"
MODELS_DIR   = PROJECT_ROOT / "models"
WEIGHTS_DIR  = PROJECT_ROOT / "weights"
ASSETS_DIR   = PROJECT_ROOT / "assets"
OUTPUTS_DIR  = PROJECT_ROOT / "outputs"
ARCHIVE_DIR  = PROJECT_ROOT / "_archive"

BASE_WEIGHTS_DIR = WEIGHTS_DIR / "base"

STAGE1_RUN = MODELS_DIR / "stage1_detection" / "rummikub-yolo11m"
STAGE2_RUN = MODELS_DIR / "stage2_classification" / "rummikub-classifier-v4"

STAGE1_WEIGHTS   = STAGE1_RUN / "weights" / "best.pt"
STAGE2_WEIGHTS   = STAGE2_RUN / "best.pt"
STAGE2_METADATA  = STAGE2_RUN / "metadata.json"

def resolve_data_path(stored: str) -> Path:
    """Turn a manifest-relative path into something under data/."""
    p = Path(str(stored).replace("\\", "/"))
    if p.is_absolute():
        return p
    parts = p.parts
    if parts and parts[0] in ("datasets", "data"):
        return DATA_DIR.joinpath(*parts[1:])
    return PROJECT_ROOT / p
