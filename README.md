# Rummikub — Train Models

Python pipeline for training and running Rummikub tile detection and classification models.

## Layout

```
train_models/
  src/rummikub/
    stage1_detection/      # YOLO tile detection
    stage2_classification/ # tile number/color classifier
    stage3_board/          # board reconstruction from detections
    pipeline/              # end-to-end detect + classify
    tools/                 # dataset download & inspection
```

Data, trained weights, and outputs live under `train_models/` (`data/`, `models/`, `weights/`, `outputs/`) and are gitignored.

## Setup

From `train_models/`:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install ultralytics albumentations opencv-python torch tqdm pyyaml roboflow
set PYTHONPATH=src
```

Adjust dependencies to match your environment and GPU setup.

## Run

Examples (from `train_models/`, with `PYTHONPATH=src`):

```bash
python -m rummikub.stage1_detection.train
python -m rummikub.stage2_classification.train
python -m rummikub.pipeline.detect_and_classify
```
