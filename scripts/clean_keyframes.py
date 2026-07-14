#!/usr/bin/env python3
"""Create text-free Jimeng keyframes with OCR masks and local inpainting."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def read_image(path: Path) -> np.ndarray:
    data = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unable to decode image: {path}")
    return image


def write_image(path: Path, image: np.ndarray) -> None:
    suffix = path.suffix.lower() or ".png"
    success, encoded = cv2.imencode(suffix, image)
    if not success:
        raise ValueError(f"Unable to encode image: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded.tofile(path)


def parse_box(value: str) -> tuple[int, int, int, int]:
    try:
        x1, y1, x2, y2 = (int(part.strip()) for part in value.split(","))
    except Exception as exc:  # noqa: BLE001
        raise argparse.ArgumentTypeError("box must be x1,y1,x2,y2 in pixels") from exc
    if x2 <= x1 or y2 <= y1 or min(x1, y1) < 0:
        raise argparse.ArgumentTypeError("box must satisfy 0 <= x1 < x2 and 0 <= y1 < y2")
    return x1, y1, x2, y2


def discover_images(input_path: Path) -> list[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError(f"Unsupported image type: {input_path.suffix}")
        return [input_path]
    if input_path.is_dir():
        return sorted(
            path for path in input_path.rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        )
    raise FileNotFoundError(input_path)


def build_reader(languages: list[str], gpu: bool) -> Any:
    try:
        import easyocr
    except ImportError as exc:
        raise RuntimeError("EasyOCR is required: python -m pip install easyocr") from exc
    return easyocr.Reader(languages, gpu=gpu)


def clean_one(
    source: Path,
    destination: Path,
    reader: Any | None,
    confidence: float,
    text_threshold: float,
    low_text: float,
    link_threshold: float,
    mag_ratio: float,
    padding: int,
    radius: int,
    manual_boxes: list[tuple[int, int, int, int]],
) -> dict[str, Any]:
    image = read_image(source)
    height, width = image.shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    detections: list[dict[str, Any]] = []

    if reader is not None:
        for polygon, text, score in reader.readtext(
            image,
            detail=1,
            paragraph=False,
            text_threshold=text_threshold,
            low_text=low_text,
            link_threshold=link_threshold,
            mag_ratio=mag_ratio,
        ):
            score = float(score)
            if score < confidence:
                continue
            points = np.array(polygon, dtype=np.int32)
            cv2.fillPoly(mask, [points], 255)
            detections.append({
                "text": str(text),
                "confidence": round(score, 4),
                "polygon": points.tolist(),
                "source": "ocr",
            })

    for x1, y1, x2, y2 in manual_boxes:
        if x2 > width or y2 > height:
            raise ValueError(f"Manual box exceeds {width}x{height}: {(x1, y1, x2, y2)}")
        cv2.rectangle(mask, (x1, y1), (x2, y2), 255, thickness=-1)
        detections.append({"box": [x1, y1, x2, y2], "source": "manual"})

    if padding:
        size = padding * 2 + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
        mask = cv2.dilate(mask, kernel)

    cleaned = cv2.inpaint(image, mask, radius, cv2.INPAINT_TELEA) if np.any(mask) else image.copy()
    clean_path = destination / f"{source.stem}-clean{source.suffix.lower()}"
    mask_path = destination / f"{source.stem}-text-mask.png"
    write_image(clean_path, cleaned)
    write_image(mask_path, mask)
    return {
        "source": str(source.resolve()),
        "clean": str(clean_path.resolve()),
        "mask": str(mask_path.resolve()),
        "width": width,
        "height": height,
        "detections": detections,
        "masked_pixel_ratio": round(float(np.count_nonzero(mask)) / float(mask.size), 6),
        "requires_visual_verification": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Keyframe image or folder")
    parser.add_argument("--out", required=True, type=Path, help="Output directory")
    parser.add_argument("--languages", default="ch_sim,en", help="Comma-separated EasyOCR languages")
    parser.add_argument("--confidence", type=float, default=0.10, help="Minimum OCR recognition confidence")
    parser.add_argument("--text-threshold", type=float, default=0.40)
    parser.add_argument("--low-text", type=float, default=0.20)
    parser.add_argument("--link-threshold", type=float, default=0.20)
    parser.add_argument("--mag-ratio", type=float, default=1.5, help="OCR enlargement for small text")
    parser.add_argument("--padding", type=int, default=6, help="Mask expansion in pixels")
    parser.add_argument("--radius", type=int, default=5, help="OpenCV inpaint radius")
    parser.add_argument("--gpu", action="store_true")
    parser.add_argument("--skip-ocr", action="store_true", help="Use only manual --box regions")
    parser.add_argument("--box", action="append", default=[], type=parse_box, help="Manual x1,y1,x2,y2 mask")
    args = parser.parse_args()

    if any(not 0 <= value <= 1 for value in (args.confidence, args.text_threshold, args.low_text, args.link_threshold)):
        parser.error("OCR confidence and threshold values must be between 0 and 1")
    if args.mag_ratio <= 0:
        parser.error("--mag-ratio must be greater than 0")
    if args.padding < 0 or args.radius < 1:
        parser.error("--padding must be >= 0 and --radius must be >= 1")
    if args.skip_ocr and not args.box:
        parser.error("--skip-ocr requires at least one --box")

    images = discover_images(args.input.resolve())
    if not images:
        raise ValueError(f"No supported images found: {args.input}")
    args.out.mkdir(parents=True, exist_ok=True)
    languages = [value.strip() for value in args.languages.split(",") if value.strip()]
    reader = None if args.skip_ocr else build_reader(languages, args.gpu)
    results = [
        clean_one(
            image,
            args.out,
            reader,
            args.confidence,
            args.text_threshold,
            args.low_text,
            args.link_threshold,
            args.mag_ratio,
            args.padding,
            args.radius,
            args.box,
        )
        for image in images
    ]
    report = {
        "version": 1,
        "method": "easyocr-mask+opencv-telea-inpaint" if reader is not None else "manual-mask+opencv-telea-inpaint",
        "images": results,
        "visual_verification_required": True,
    }
    report_path = args.out / "clean-keyframes.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
