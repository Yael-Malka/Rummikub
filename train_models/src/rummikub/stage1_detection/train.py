"""Stage 1 YOLO training — find tile boxes.

Missed tiles hurt more than false positives, so we bias recall.
Heavy aug is offline; online aug stays mild.
"""

import os

# before importing torch — helps on 8.5 GB GPUs
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

from pathlib import Path

from ultralytics import YOLO

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
DATA_YAML  = str(DATA_DIR / "stage1_detection/ready/data.yaml")
BASE_MODEL = str(ROOT / "weights/base/yolo11m.pt")
PROJECT    = str(MODELS_DIR / "stage1_detection")
RUN_NAME   = "rummikub-yolo11m"

def main():
    """Train, eval on test split, export ONNX."""
    model = YOLO(BASE_MODEL)

    model.train(

        data       = DATA_YAML,
        epochs     = 200,
        patience   = 50,
        imgsz      = 640,
        batch      = 8,         # 8.5 GB VRAM with AMP
        device     = 0,
        workers    = 0,         # Windows multiprocessing is flaky
        cache      = False,        amp        = True,
        project    = PROJECT,
        name       = RUN_NAME,
        exist_ok   = True,

        optimizer       = "SGD",
        lr0             = 0.01,
        lrf             = 0.01,
        momentum        = 0.937,
        weight_decay    = 0.0005,
        warmup_epochs   = 3.0,
        warmup_momentum = 0.8,
        warmup_bias_lr  = 0.1,
        cos_lr          = True,

        # most aug already done offline
        hsv_h        = 0.005,
        hsv_s        = 0.2,
        hsv_v        = 0.15,
        degrees      = 5.0,
        translate    = 0.1,
        scale        = 0.3,
        shear        = 0.5,
        perspective  = 0.0,
        flipud       = 0.0,
        fliplr       = 0.5,
        mosaic       = 0.5,
        mixup        = 0.05,
        copy_paste   = 0.1,
        erasing      = 0.2,
        close_mosaic = 10,

        save        = True,
        save_period = 25,
        plots       = True,
        verbose     = True,
        val         = True,
    )

    best_pt = Path(model.trainer.best)
    print(f"\nLoading best weights for test-set evaluation: {best_pt}")
    best = YOLO(str(best_pt))

    test_metrics = best.val(
        data    = DATA_YAML,
        split   = "test",
        imgsz   = 640,
        batch   = 8,
        workers = 0,
        device  = 0,
        conf    = 0.001,   # low conf for PR curve on test only
        iou     = 0.6,
        plots   = True,
        save_json = True,
        project = PROJECT,
        name    = f"{RUN_NAME}-test",
        exist_ok = True,
    )

    print("\nTest metrics:")
    print(f"  precision   {test_metrics.box.mp:.4f}")
    print(f"  recall      {test_metrics.box.mr:.4f}")
    print(f"  mAP@0.50    {test_metrics.box.map50:.4f}")
    print(f"  mAP@0.50-95 {test_metrics.box.map:.4f}\n")

    print("Exporting best.pt to ONNX...")
    onnx_path = best.export(
        format   = "onnx",
        imgsz    = 640,
        dynamic  = True,
        simplify = True,
        opset    = 12,
    )
    print(f"\nBest weights : {best_pt}")
    print(f"ONNX model   : {onnx_path}")
    print(f"Run dir      : {Path(PROJECT) / RUN_NAME}")

if __name__ == "__main__":
    main()
