"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image


def _synthetic_plate(
    size: int = 400,
    colony_centres: list[tuple[int, int, int]] | None = None,
) -> np.ndarray:
    """Render a synthetic crystal-violet plate with circular colonies.

    Args:
        size: Square image side in pixels.
        colony_centres: List of ``(cx, cy, radius)`` tuples in pixel
            coordinates relative to the image. If omitted, three
            well-separated colonies near the centre are drawn.

    Returns:
        ``(size, size, 3)`` uint8 array (RGB) with purple colonies on a
        light cream background.
    """
    img = np.full((size, size, 3), 235, dtype=np.uint8)
    if colony_centres is None:
        c = size // 2
        colony_centres = [
            (c - 40, c - 40, 14),
            (c + 30, c - 20, 12),
            (c, c + 40, 16),
        ]

    yy, xx = np.ogrid[:size, :size]
    for cx, cy, radius in colony_centres:
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius**2
        img[mask] = (95, 50, 130)  # purple
    return img


@pytest.fixture
def synthetic_plate_path(tmp_path: Path) -> Path:
    """Write a synthetic plate as a .tif and return its path."""
    img = _synthetic_plate()
    path = tmp_path / "plate.tif"
    Image.fromarray(img).save(path)
    return path


@pytest.fixture
def blank_plate_path(tmp_path: Path) -> Path:
    """A plate with no colonies."""
    img = np.full((400, 400, 3), 235, dtype=np.uint8)
    path = tmp_path / "blank.tif"
    Image.fromarray(img).save(path)
    return path
