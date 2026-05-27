"""Colony detection from crystal-violet-stained petri dish images.

The pipeline:

1. Load image and build a circular dish mask.
2. Compute a "purple signal" channel combining blue-minus-red and darkness.
3. Subtract a Gaussian-blurred background estimate.
4. Threshold and clean up the binary mask with morphological operations.
5. Run a distance-transform / intensity-peak watershed to split touching
   colonies.
6. Measure per-colony properties (area, density, centroid).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

import numpy as np
import numpy.typing as npt
from PIL import Image
from scipy.ndimage import distance_transform_edt, gaussian_filter
from skimage import measure, morphology, segmentation
from skimage.feature import peak_local_max

from .params import DEFAULT_PARAMS, DetectionParams

FloatArray = npt.NDArray[np.float64]
BoolArray = npt.NDArray[np.bool_]
IntArray = npt.NDArray[np.int_]
RGBArray = npt.NDArray[np.uint8]


class ColonyRecord(TypedDict):
    """Per-colony measurements."""

    colony_id: int
    area_px: int
    area_pct: float
    density: float
    centroid_x: float
    centroid_y: float


@dataclass
class DetectionResult:
    """Result of running the detection pipeline on a single image."""

    image: RGBArray
    labels: IntArray
    colonies: list[ColonyRecord]
    n_colonies: int
    dish_area_px: int
    colony_area_px: int
    colony_area_pct: float
    mean_density: float


def load_image(image_path: Path) -> RGBArray:
    """Load an image as an RGB uint8 array."""
    return np.array(Image.open(image_path).convert("RGB"))


def build_dish_mask(shape: tuple[int, int], radius_frac: float) -> BoolArray:
    """Build a circular dish mask centred in the frame."""
    h, w = shape
    cy, cx = h // 2, w // 2
    radius = int(min(h, w) * radius_frac)
    yy, xx = np.ogrid[:h, :w]
    return ((xx - cx) ** 2 + (yy - cy) ** 2) <= radius**2


def purple_signal(img: RGBArray) -> FloatArray:
    """Combine blue-minus-red and overall darkness into a single channel.

    Crystal-violet-stained colonies are purple on a lighter background.
    Subtracting red from blue isolates the purple component; mixing in
    overall darkness keeps the signal robust for very dense colonies that
    are nearly black.
    """
    r = img[:, :, 0].astype(float)
    g = img[:, :, 1].astype(float)
    b = img[:, :, 2].astype(float)
    darkness = 255 - (r + g + b) / 3
    return (b - r).clip(0) + darkness * 0.3


def background_correct(
    signal: FloatArray, params: DetectionParams
) -> FloatArray:
    """Subtract a fraction of a Gaussian-blurred background estimate."""
    background = gaussian_filter(signal, sigma=params.bg_sigma)
    return (signal - background * params.bg_subtract_frac).clip(0)


def binarize(
    corrected: FloatArray, dish_mask: BoolArray, params: DetectionParams
) -> BoolArray:
    """Threshold and morphologically clean the corrected signal."""
    binary: BoolArray = (corrected > params.threshold) & dish_mask
    binary = morphology.opening(binary, morphology.disk(1))
    binary = morphology.closing(binary, morphology.disk(4))
    binary = morphology.remove_small_objects(binary, params.min_colony_px)
    binary = morphology.remove_small_holes(binary, 1500)
    return binary


def watershed_split(
    binary: BoolArray, smoothed: FloatArray, params: DetectionParams
) -> IntArray:
    """Split touching colonies using a distance + intensity watershed."""
    distance = distance_transform_edt(binary)
    combined = distance * smoothed
    coords = peak_local_max(
        combined, min_distance=params.watershed_dist, labels=binary
    )
    markers = np.zeros(distance.shape, dtype=bool)
    markers[tuple(coords.T)] = True
    markers = measure.label(markers)
    return segmentation.watershed(-combined, markers, mask=binary)


def measure_colonies(
    labels: IntArray,
    smoothed: FloatArray,
    dish_mask: BoolArray,
    params: DetectionParams,
) -> tuple[list[ColonyRecord], int, int]:
    """Build per-colony records, filtering objects below ``min_colony_px``.

    Returns:
        (colonies, dish_area_px, colony_area_px)
    """
    props = [
        p
        for p in measure.regionprops(labels, intensity_image=smoothed)
        if p.area >= params.min_colony_px
    ]

    dish_area_px = int(dish_mask.sum())
    colony_area_px = int(sum(p.area for p in props))

    masked_signal = smoothed[dish_mask]
    max_intensity = float(masked_signal.max()) if masked_signal.size else 1.0
    if max_intensity == 0:
        max_intensity = 1.0

    colonies: list[ColonyRecord] = []
    for i, p in enumerate(props):
        colonies.append(
            ColonyRecord(
                colony_id=i + 1,
                area_px=int(p.area),
                area_pct=round(100 * p.area / dish_area_px, 3),
                density=round((p.intensity_mean / max_intensity) * 100, 2),
                centroid_x=round(float(p.centroid[1]), 1),
                centroid_y=round(float(p.centroid[0]), 1),
            )
        )

    return colonies, dish_area_px, colony_area_px


def detect(
    image_path: Path, params: DetectionParams = DEFAULT_PARAMS
) -> DetectionResult:
    """Run the full detection pipeline on one image."""
    img = load_image(image_path)
    dish_mask = build_dish_mask(img.shape[:2], params.dish_radius_frac)

    signal = purple_signal(img)
    corrected = background_correct(signal, params) * dish_mask
    smoothed = gaussian_filter(corrected, sigma=params.peak_smooth_sigma)

    binary = binarize(corrected, dish_mask, params)
    labels = watershed_split(binary, smoothed, params)

    colonies, dish_area_px, colony_area_px = measure_colonies(
        labels, smoothed, dish_mask, params
    )

    colony_area_pct = (
        100 * colony_area_px / dish_area_px if dish_area_px else 0.0
    )
    densities = [c["density"] for c in colonies]
    mean_density = round(float(np.mean(densities)), 1) if densities else 0.0

    return DetectionResult(
        image=img,
        labels=labels,
        colonies=colonies,
        n_colonies=len(colonies),
        dish_area_px=dish_area_px,
        colony_area_px=colony_area_px,
        colony_area_pct=colony_area_pct,
        mean_density=mean_density,
    )
