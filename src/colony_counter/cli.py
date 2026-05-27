"""Command-line interface for colony-counter."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from .config import get_logger
from .detection import detect
from .excel import ImageReport, write_workbook
from .params import DEFAULT_PARAMS, DetectionParams
from .visualization import save_mask_figure

logger = get_logger(__name__)

SUPPORTED_SUFFIXES = (".tif", ".tiff", ".png", ".jpg", ".jpeg")


def find_images(input_dir: Path) -> list[Path]:
    """Return supported image files in ``input_dir``, sorted by name."""
    images: list[Path] = []
    for suffix in SUPPORTED_SUFFIXES:
        images.extend(input_dir.glob(f"*{suffix}"))
    return sorted(images)


def process_images(
    images: Sequence[Path],
    results_dir: Path,
    params: DetectionParams = DEFAULT_PARAMS,
) -> list[ImageReport]:
    """Run detection on each image and write its annotated mask."""
    masks_dir = results_dir / "masks"
    reports: list[ImageReport] = []
    for image_path in images:
        logger.info("Processing %s", image_path.name)
        result = detect(image_path, params)
        mask_path = masks_dir / f"{image_path.stem}_mask.png"
        save_mask_figure(result, mask_path)
        logger.info(
            "  colonies=%d  area=%.1f%%  density=%.1f",
            result.n_colonies,
            result.colony_area_pct,
            result.mean_density,
        )
        reports.append(ImageReport(name=image_path.name, result=result))
    return reports


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="colony-counter",
        description=(
            "Count colonies and measure stained area from "
            "crystal-violet petri-dish images."
        ),
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing .tif/.tiff/.png/.jpg images.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path.home() / "Desktop" / "results",
        help=(
            "Output directory (default: ~/Desktop/results). Writes "
            "colony_results.xlsx and masks/."
        ),
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_PARAMS.threshold,
        help="Signal threshold for colony pixels.",
    )
    parser.add_argument(
        "--min-colony-px",
        type=int,
        default=DEFAULT_PARAMS.min_colony_px,
        help="Minimum colony area in pixels.",
    )
    parser.add_argument(
        "--watershed-dist",
        type=int,
        default=DEFAULT_PARAMS.watershed_dist,
        help="Minimum distance between watershed peaks.",
    )
    parser.add_argument(
        "--dish-radius-frac",
        type=float,
        default=DEFAULT_PARAMS.dish_radius_frac,
        help="Dish radius as fraction of min(height, width).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    input_dir: Path = args.input_dir
    output_dir: Path = args.output

    if not input_dir.exists():
        logger.error("Input directory not found: %s", input_dir)
        return 1

    images = find_images(input_dir)
    if not images:
        logger.error("No supported images found in %s", input_dir)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "masks").mkdir(exist_ok=True)

    params = DetectionParams(
        threshold=args.threshold,
        min_colony_px=args.min_colony_px,
        watershed_dist=args.watershed_dist,
        dish_radius_frac=args.dish_radius_frac,
    )

    logger.info("Found %d image(s); output → %s", len(images), output_dir)
    reports = process_images(images, output_dir, params)

    excel_path = output_dir / "colony_results.xlsx"
    write_workbook(reports, excel_path)
    logger.info("Excel report saved → %s", excel_path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
