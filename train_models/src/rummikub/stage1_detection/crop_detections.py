"""Quick utility: run the detector and dump each box as a separate JPEG."""

import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO

from rummikub.paths import DATA_DIR, MODELS_DIR, PROJECT_ROOT as ROOT
WEIGHTS = MODELS_DIR / "stage1_detection/rummikub-yolo11m/weights/best.pt"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image", help="Path to input image")
    parser.add_argument("output_dir", help="Directory to save cropped tiles")
    parser.add_argument("--conf", type=float, default=0.25)
    args = parser.parse_args()

    img_path = Path(args.image)
    out_dir  = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    img = cv2.imread(str(img_path))
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {img_path}")

    model   = YOLO(str(WEIGHTS))
    results = model.predict(source=str(img_path), conf=args.conf, imgsz=640, verbose=False)
    r       = results[0]
    names   = model.names

    print(f"Detected {len(r.boxes)} tile(s) — saving crops to {out_dir}/")

    for i, box in enumerate(r.boxes):
        cls   = names[int(box.cls)]
        conf  = float(box.conf)
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        # Clamp to image bounds.
        x1 = max(0, x1); y1 = max(0, y1)
        x2 = min(img.shape[1], x2); y2 = min(img.shape[0], y2)

        crop     = img[y1:y2, x1:x2]
        filename = f"{i} - {cls} - {conf:.2f}.jpg"
        cv2.imwrite(str(out_dir / filename), crop)

    print(f"Done. {len(r.boxes)} crops saved.")

if __name__ == "__main__":
    main()
