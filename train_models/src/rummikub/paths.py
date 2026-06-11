"""Project directory constants — import these instead of hardcoding paths."""

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

STAGE1_WEIGHTS   = STAGE1_RUN / "weights" / "best.pt"
