"""Rendering of annotated mask images."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from skimage.color import label2rgb  # noqa: E402

from .detection import DetectionResult  # noqa: E402


def save_mask_figure(result: DetectionResult, output_path: Path) -> None:
    """Save a side-by-side figure: original image vs labelled colonies."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.5), facecolor="#1a1a1a")

    axes[0].imshow(result.image)
    axes[0].set_title("Original image", fontsize=13, color="white", pad=10)
    axes[0].axis("off")

    colored = label2rgb(
        result.labels, image=result.image, bg_label=0, alpha=0.45
    )
    axes[1].imshow(colored)
    for c in result.colonies:
        axes[1].annotate(
            str(c["colony_id"]),
            (c["centroid_x"], c["centroid_y"]),
            color="white",
            fontsize=5.5,
            ha="center",
            va="center",
            fontweight="bold",
        )
    axes[1].set_title(
        f"Colonies: {result.n_colonies}  |  "
        f"Area: {result.colony_area_pct:.1f}%  |  "
        f"Density: {result.mean_density:.1f}/100",
        fontsize=12,
        color="white",
        pad=10,
    )
    axes[1].axis("off")

    plt.tight_layout(pad=1.5)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=160, bbox_inches="tight", facecolor="#1a1a1a")
    plt.close(fig)
