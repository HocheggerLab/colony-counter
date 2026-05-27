"""Tests for the CLI."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from colony_counter.cli import find_images, main


def test_find_images_filters_and_sorts(tmp_path: Path) -> None:
    (tmp_path / "b.tif").write_bytes(b"")
    (tmp_path / "a.png").write_bytes(b"")
    (tmp_path / "notes.txt").write_text("ignore me")
    (tmp_path / "c.jpeg").write_bytes(b"")

    found = find_images(tmp_path)
    names = [p.name for p in found]
    assert names == sorted(names)
    assert "notes.txt" not in names
    assert set(names) == {"a.png", "b.tif", "c.jpeg"}


def test_main_returns_nonzero_when_input_missing(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist"
    assert main([str(missing)]) == 1


def test_main_returns_nonzero_when_no_images(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    assert main([str(empty)]) == 1


def test_main_runs_end_to_end(
    tmp_path: Path, synthetic_plate_path: Path
) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    # Move synthetic plate into input dir
    target = input_dir / synthetic_plate_path.name
    Image.open(synthetic_plate_path).save(target)

    output_dir = tmp_path / "out"
    exit_code = main(
        [
            str(input_dir),
            "--output",
            str(output_dir),
            "--threshold",
            "3.0",
            "--min-colony-px",
            "50",
            "--watershed-dist",
            "8",
            "--dish-radius-frac",
            "0.45",
        ]
    )
    assert exit_code == 0
    assert (output_dir / "colony_results.xlsx").exists()
    mask_files = list((output_dir / "masks").glob("*_mask.png"))
    assert len(mask_files) == 1
