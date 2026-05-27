# colony-counter

Quantify colonies in crystal-violet-stained petri dish images.

`colony-counter` counts colonies and measures stained area from
photographs of crystal-violet-stained colony survival assay plates. It
handles dense **and** faint colonies via rolling-ball background
correction and uses an intensity-peak watershed to split overlapping
colonies.

![version](https://img.shields.io/badge/version-0.1.0-blue)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Features

- Robust to faint and very dense colonies (rolling-ball background
  correction in the purple/darkness channel).
- Splits overlapping colonies using a distance + intensity watershed.
- Per-image annotated mask figure (original + labelled colonies).
- Styled Excel report: a summary sheet plus one sheet per image with
  per-colony measurements (area, area %, density, centroid).
- Configurable via CLI flags or programmatically via `DetectionParams`.

## Installation

```bash
# from PyPI (once published)
pip install colony-counter

# from source
git clone https://github.com/hh65/colony-counter.git
cd colony-counter
uv sync
```

The package targets Python 3.13+.

## Usage

### Command line

```bash
colony-counter path/to/images --output path/to/results
```

This will:

1. Process every `.tif`, `.tiff`, `.png`, `.jpg`, `.jpeg` file in
   `path/to/images`.
2. Write an annotated mask PNG for each image to
   `path/to/results/masks/`.
3. Write `path/to/results/colony_results.xlsx` containing a summary
   sheet and a per-image detail sheet.

Tunable detection parameters:

| Flag | Default | Description |
|------|---------|-------------|
| `--threshold` | `5.0` | Pixel-intensity threshold on the corrected signal. |
| `--min-colony-px` | `200` | Minimum colony area in pixels. |
| `--watershed-dist` | `10` | Minimum distance (px) between watershed peaks. |
| `--dish-radius-frac` | `0.44` | Dish radius as a fraction of `min(height, width)`. |
| `-v / --verbose` | off | Enable debug logging. |

### Library

```python
from pathlib import Path

from colony_counter import (
    DetectionParams,
    detect,
    save_mask_figure,
    write_workbook,
    ImageReport,
)

params = DetectionParams(threshold=8.0, min_colony_px=150)
result = detect(Path("plate_01.tif"), params)

print(result.n_colonies, result.colony_area_pct, result.mean_density)

save_mask_figure(result, Path("plate_01_mask.png"))
write_workbook(
    [ImageReport(name="plate_01.tif", result=result)],
    Path("colony_results.xlsx"),
)
```

## Output

```
results/
├── colony_results.xlsx
└── masks/
    ├── plate_01_mask.png
    └── plate_02_mask.png
```

- **Summary sheet** — per-image colony count, total colony area %, mean
  density, dish area in pixels.
- **Per-image sheet** — per-colony `id`, `area_px`, `area_pct`,
  `density (0-100)`, `centroid_x`, `centroid_y`.

## How it works

1. **Dish mask** — a circular mask centred on the image isolates the
   petri-dish region.
2. **Purple signal** — combines blue-minus-red with overall darkness to
   highlight crystal-violet stain across both faint and dense colonies.
3. **Background correction** — subtracts a Gaussian-blurred estimate of
   the slowly-varying background.
4. **Binarization** — thresholding plus morphological opening, closing,
   small-object and small-hole removal.
5. **Watershed splitting** — peaks of `distance_transform * smoothed
   signal` seed a watershed that separates touching colonies.
6. **Measurement** — `skimage.measure.regionprops` extracts area,
   intensity, and centroid; density is normalised to the brightest
   colony in the dish.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format .
```

This project uses [Conventional Commits](https://www.conventionalcommits.org/)
and [Semantic Versioning](https://semver.org/). Bump versions with
commitizen:

```bash
uv run cz bump
```

## License

MIT — see [LICENSE](LICENSE).

## Authors

Created by Georgios Kallogiannis @HocheggerLab (G.Kalogiannis@sussex.ac.uk).
