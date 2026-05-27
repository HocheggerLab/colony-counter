"""Tests for the params module."""

from __future__ import annotations

import pytest

from colony_counter.params import DEFAULT_PARAMS, DetectionParams


def test_defaults_match_documented_values() -> None:
    assert DEFAULT_PARAMS.threshold == 5.0
    assert DEFAULT_PARAMS.min_colony_px == 200
    assert DEFAULT_PARAMS.watershed_dist == 10
    assert DEFAULT_PARAMS.dish_radius_frac == pytest.approx(0.44)


def test_params_are_frozen() -> None:
    from dataclasses import FrozenInstanceError

    params = DetectionParams()
    with pytest.raises(FrozenInstanceError):
        params.threshold = 99.0  # ty: ignore[invalid-assignment]


def test_override_fields() -> None:
    params = DetectionParams(threshold=12.0, min_colony_px=50)
    assert params.threshold == 12.0
    assert params.min_colony_px == 50
    # Untouched fields keep their defaults
    assert params.watershed_dist == DEFAULT_PARAMS.watershed_dist
