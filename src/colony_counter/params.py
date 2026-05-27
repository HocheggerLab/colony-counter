"""Tunable parameters for the colony counting pipeline."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DetectionParams:
    """Parameters controlling colony detection.

    Attributes:
        threshold: Pixel intensity threshold (background-corrected purple
            signal) above which a pixel is considered part of a colony.
        min_colony_px: Minimum area in pixels for a region to be retained
            as a colony.
        watershed_dist: Minimum distance (px) between watershed peaks.
            Smaller values split overlapping colonies more aggressively.
        dish_radius_frac: Petri-dish radius as a fraction of
            ``min(height, width)``. Used to mask out the area outside the
            dish.
        bg_sigma: Gaussian sigma (px) for the rolling-ball-like background
            estimation.
        bg_subtract_frac: Fraction of the estimated background that is
            subtracted from the signal.
        peak_smooth_sigma: Gaussian sigma applied to the corrected signal
            before peak detection.
    """

    threshold: float = 5.0
    min_colony_px: int = 200
    watershed_dist: int = 10
    dish_radius_frac: float = 0.44
    bg_sigma: float = 40.0
    bg_subtract_frac: float = 0.85
    peak_smooth_sigma: float = 2.0


DEFAULT_PARAMS = DetectionParams()
