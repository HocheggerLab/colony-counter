# CLAUDE.md — colony-counter

Project context for Claude Code. Read this first.

## What this is

`colony-counter` counts colonies and measures stained area from photographs of
crystal-violet-stained colony survival assay plates. Originally a single script
by Georgios Kallogiannis (@HocheggerLab); refactored into an installable,
tested package being prepared for a PyPI release.

**Audience note:** Georgios is learning research software engineering. When
working with him, *explain the why before the how* — favour teaching over just
emitting code. The two docs below are the curriculum.

- `docs/project-structure.md` — layout, uv, src/, `__init__.py`, packaging, testing.
- `docs/roadmap.md` — the milestone-by-milestone plan for what to build next.

## Architecture (one job per module)

```
src/colony_counter/
├── params.py        # DetectionParams dataclass (the tunable numbers)
├── detection.py     # image → measurements (the science). depends on: params
├── visualization.py # measurements → annotated PNG.       depends on: detection
├── excel.py         # measurements → styled Excel report. depends on: detection
├── cli.py           # glue: args → detect → outputs.       depends on: all
├── config.py        # logging + env configuration
└── __init__.py      # public API + __version__
```

**Dependency direction is one-way:** `detection.py` must stay ignorant of Excel,
plotting, and the CLI, so the science is reusable from a notebook. Keep
**computation separate from presentation** — it's the theme of the whole repo.

## Commands (always via `uv`, never bare `pip`)

```bash
uv sync                 # set up / update the environment (run after cloning)
uv run colony-counter <input_dir> -o <output_dir>   # run the tool
uv run pytest           # tests
uv run ruff format .    # format
uv run ruff check .     # lint
uv run ty check         # type check
uv run cz commit        # conventional commit (drives versioning)
uv run cz bump          # bump version + changelog
```

Run format + lint + type + tests before every commit. Pre-commit enforces this;
don't bypass it with `--no-verify` — fix the underlying issue.

## Conventions

- **Python 3.13+**, `uv` exclusively, `ruff` (line length 79), `ty` for types.
- **Type hints on every function signature.** Google-style docstrings.
- NumPy array aliases live in `detection.py` (`FloatArray`, `BoolArray`, ...).
- Custom exceptions over bare `Exception`; `logging`, not `print`.
- Tests mirror source: `src/.../foo.py` → `tests/test_foo.py`. Use the
  `synthetic_plate_path` / `blank_plate_path` fixtures in `conftest.py` to make
  inputs with known answers rather than relying on real microscope images.
- **Fail loudly, not silently** — a wrong number with no warning is the worst
  bug class in research software.

## Workflow

One branch per task, one PR per branch. Test-first where practical: write a
failing test, implement until green, then lint/type/format. Commit messages use
Conventional Commits (`feat:`, `fix:`, `docs:`...).

## Enhancement ideas (see docs/roadmap.md for full specs + tests)

1. **Tidy, typed data** — `ColonyRecord` from `TypedDict` → `dataclass`.
2. **Rich CLI** — `rich`/`typer`: progress bar, results table, coloured logs.
3. **Robustness: auto-detect the dish** — biggest correctness risk. Stop
   assuming the dish is centred at `0.44 × min(h,w)`; measure it (Hough circle).
   Raise `DishNotFoundError` on failure.
4. **CSV / tidy outputs** — long-format `colonies.csv` + `summary.csv` for
   pandas/R, plus a `run_metadata.json` (params + version + inputs) for
   reproducibility.
5. **Validation + config file** — validate `DetectionParams` (Pydantic);
   support `--config plate_settings.toml`.
6. **CI + PyPI** — GitHub Actions running the checks; publish via TestPyPI then
   PyPI. Also fix the scikit-image `remove_small_objects`/`remove_small_holes`
   `FutureWarning`s before release.

## Known issues

- scikit-image emits `FutureWarning`s for `remove_small_objects` /
  `remove_small_holes` (`min_size`/`area_threshold` → `max_size` rename in 0.26;
  semantics differ slightly). Address before the PyPI release.
