"""Tests for the detection pipeline."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from colony_counter.detection import (
    DetectionResult,
    build_dish_mask,
    detect,
    load_image,
    purple_signal,
)
from colony_counter.params import DetectionParams


def test_build_dish_mask_is_circular_and_centred() -> None:
    mask = build_dish_mask((100, 100), radius_frac=0.5)
    assert mask.shape == (100, 100)
    # Centre pixel is inside the mask
    assert mask[50, 50]
    # Corners are outside
    assert not mask[0, 0]
    assert not mask[99, 99]
    # Area roughly matches pi * r^2
    expected_area = np.pi * (100 * 0.5) ** 2
    assert abs(mask.sum() - expected_area) / expected_area < 0.05


def test_purple_signal_is_high_for_purple_pixels() -> None:
    img = np.zeros((4, 4, 3), dtype=np.uint8)
    img[:, :] = (95, 50, 130)  # purple
    signal = purple_signal(img)
    assert signal.shape == (4, 4)
    assert (signal > 0).all()


def test_purple_signal_is_zero_for_white_pixels() -> None:
    img = np.full((4, 4, 3), 255, dtype=np.uint8)
    signal = purple_signal(img)
    # b - r == 0, darkness == 0
    assert (signal == 0).all()


def test_load_image_returns_rgb_uint8(synthetic_plate_path: Path) -> None:
    img = load_image(synthetic_plate_path)
    assert img.dtype == np.uint8
    assert img.shape[2] == 3


def test_detect_finds_synthetic_colonies(
    synthetic_plate_path: Path,
) -> None:
    # Tune min_colony_px and dish_radius_frac for the small test image.
    params = DetectionParams(
        threshold=3.0,
        min_colony_px=50,
        watershed_dist=8,
        dish_radius_frac=0.45,
    )
    result = detect(synthetic_plate_path, params)

    assert isinstance(result, DetectionResult)
    assert result.n_colonies == 3
    assert result.dish_area_px > 0
    assert result.colony_area_px > 0
    assert 0 < result.colony_area_pct < 100
    assert len(result.colonies) == 3

    for c in result.colonies:
        assert c["area_px"] >= params.min_colony_px
        assert c["area_pct"] > 0
        assert 0 <= c["density"] <= 100


def test_detect_on_blank_plate_returns_zero_colonies(
    blank_plate_path: Path,
) -> None:
    params = DetectionParams(
        threshold=3.0, min_colony_px=50, dish_radius_frac=0.45
    )
    result = detect(blank_plate_path, params)
    assert result.n_colonies == 0
    assert result.colony_area_px == 0
    assert result.colony_area_pct == 0.0
    assert result.mean_density == 0.0
    assert result.colonies == []
