"""TileClassifier — shared CNN backbone, separate number and color heads."""

from __future__ import annotations

import torch
import torch.nn as nn

# Class maps — the canonical ordering used everywhere (training + metadata.json).
NUMBER_CLASSES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "joker"]
COLOR_CLASSES  = ["black", "blue", "joker", "orange", "red"]  # alphabetical (matches Counter sort)

# Set True only after `pip install timm` AND a HuggingFace token is configured.
USE_PRETRAINED = False

try:
    import timm
    _TIMM_AVAILABLE = USE_PRETRAINED
except ImportError:
    _TIMM_AVAILABLE = False

def _build_custom_cnn() -> nn.Module:
    """Lightweight VGG-style CNN for when timm is unavailable."""
    def block(cin, cout, pool=True):
        layers = [
            nn.Conv2d(cin, cout, 3, padding=1, bias=False),
            nn.BatchNorm2d(cout), nn.ReLU(inplace=True),
            nn.Conv2d(cout, cout, 3, padding=1, bias=False),
            nn.BatchNorm2d(cout), nn.ReLU(inplace=True),
        ]
        if pool:
            layers.append(nn.MaxPool2d(2))
        return nn.Sequential(*layers)

    return nn.Sequential(
        block(3,   32),          # 128->64
        block(32,  64),          # 64->32
        block(64,  128),         # 32->16
        block(128, 256),         # 16->8
        block(256, 512, pool=False),
        nn.AdaptiveAvgPool2d(1),
        nn.Flatten(),
    )

class TileClassifier(nn.Module):
    def __init__(self, n_numbers: int = 14, n_colors: int = 5, feat_dim: int = 1280):
        super().__init__()
        if _TIMM_AVAILABLE:
            base = timm.create_model("efficientnet_b0", pretrained=True, num_classes=0)
            self.backbone = base
            self.feat_dim = base.num_features
        else:
            # Fallback: small custom CNN (~2.8M params), no pretrained weights.
            self.backbone = _build_custom_cnn()
            self.feat_dim = 512

        self.num_head = nn.Linear(self.feat_dim, n_numbers)
        self.col_head = nn.Linear(self.feat_dim, n_colors)

    def forward(self, x: torch.Tensor):
        feat = self.backbone(x)          # (B, feat_dim)
        return self.num_head(feat), self.col_head(feat)

def backbone_name() -> str:
    return "efficientnet_b0" if _TIMM_AVAILABLE else "custom_cnn"
