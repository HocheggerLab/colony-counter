# Development Roadmap — Next Steps

A guided to-do list for Georgios, designed to be worked through **with Claude
Code**. Each milestone is a self-contained learning exercise: it has a goal, the
concepts you'll learn, a concrete spec, and — crucially — the tests you should
write. Do them roughly in order; each builds on the last.

> **How to work through this:** Pick one milestone. Open Claude Code in the repo
> and say something like *"I want to work on Milestone 2 from docs/roadmap.md.
> Explain the approach first, then let's implement it test-first."* Don't let it
> just dump code on you — ask it to explain the *why* at each step. You're here
> to learn, not just to ship.

> **The golden workflow for every milestone:**
> 1. Make a branch: `git checkout -b feature/<name>`
> 2. Write (or ask Claude to help you write) a **failing test** first.
> 3. Implement until the test passes.
> 4. `uv run ruff format . && uv run ruff check . && uv run ty check && uv run pytest`
> 5. Commit with a conventional message: `uv run cz commit`
> 6. Open a pull request; ask Helfrid (or `/code-review`) to review.

---

## Milestone 1 — Tidy, typed data structures

**Goal:** Replace the loosely-typed dictionaries with explicit, self-documenting
data structures, and adopt the "tidy data" principle for outputs.

**Why it matters:** Right now a colony is a `TypedDict` accessed with string keys
(`c["area_px"]`). That works, but typos like `c["aera_px"]` aren't caught until
runtime, and you don't get editor autocomplete. A `dataclass` (or Pydantic
model) gives you `c.area_px`, autocomplete, and validation.

**Concepts you'll learn:** dataclasses vs `TypedDict` vs Pydantic; the "tidy
data" concept (each row = one observation, each column = one variable);
immutability with `frozen=True`.

**Spec:**
- Convert `ColonyRecord` in `detection.py` from a `TypedDict` to a `@dataclass`.
  Update `excel.py` and `visualization.py` to use attribute access (`c.area_px`).
- Read about **tidy data** (Hadley Wickham's principle): one colony per row, one
  variable per column, suitable for direct loading into pandas/R. Keep this in
  mind for Milestone 4.
- Consider a `frozen=True` dataclass so a colony record can't be mutated by
  accident.

**Tests to write:**
- Construct a `ColonyRecord`, assert its attributes.
- Assert that the existing `test_detection.py` still passes (you changed an
  internal representation but not behaviour — the tests prove that).

**Stretch:** Try a Pydantic model instead and add a validator (e.g. `density`
must be between 0 and 100). Discuss with Claude when Pydantic is worth the
dependency vs a plain dataclass.

---

## Milestone 2 — A richer CLI with `rich` and `typer`

**Goal:** Replace the hand-rolled `argparse` CLI with a modern, friendly one:
coloured output, a progress bar over the images, and a results table printed to
the terminal.

**Why it matters:** A good CLI is the difference between a tool a colleague
*enjoys* using and one they avoid. For a batch of 50 plates, a progress bar
that shows "23/50, ETA 40s" is the difference between "is it frozen?" and
confidence.

**Concepts you'll learn:** the `rich` library (progress bars, tables, coloured
logging); `typer` (builds CLIs from type hints — far less boilerplate than
argparse); how console scripts are wired up in `pyproject.toml`.

**Spec:**
- `uv add rich` (and optionally `uv add typer`).
- Add a `rich.progress` progress bar to `process_images()` in `cli.py`.
- Print the final per-image summary as a `rich.table.Table` instead of manual
  f-string columns.
- Use `rich`'s logging handler so log output is colour-coded by level.
- **Optional but recommended:** migrate the argument parsing to `typer`. Notice
  how it derives `--threshold` etc. directly from typed function parameters —
  the same philosophy as the rest of the codebase.
- Keep the `colony-counter` console-script entry point working (update
  `[project.scripts]` if you change the entry function).

**Tests to write:**
- `find_images()` and the exit-code behaviours (missing dir, no images) are
  already tested — keep them green.
- Progress bars and colours are hard to assert on directly. Instead, test the
  *logic* (which images get processed, what the table data is) separately from
  the *rendering*. This teaches an important lesson: **separate computation from
  presentation so the computation stays testable.**

**Stretch:** Add a `--quiet` flag and a `--dry-run` flag (lists what *would* be
processed without doing the work).

---

## Milestone 3 — Robustness: find the dish automatically

**Goal:** Stop assuming the petri dish is perfectly centred. Detect the dish's
real position and radius from the image.

**Why it matters:** This is the biggest *correctness* risk in the current code.
`build_dish_mask()` assumes the dish is dead-centre at exactly
`0.44 × min(h, w)`. A photo where the dish is off to one side, or shot at a
different zoom, will silently mask out real colonies near the edge — wrong
counts, no error message. This is the kind of bug that quietly corrupts data.

**Concepts you'll learn:** the Hough circle transform; defensive programming
(fail loudly when an assumption breaks); the difference between a parameter you
*set* and a property you *measure*.

**Spec:**
- Add a function `find_dish(img, ...) -> tuple[cx, cy, radius]` in a new
  `dish.py` module (one job per module!). Options, simplest first:
  1. Threshold the dish (it's usually a bright/coloured circle on a darker
     background) and fit a bounding circle to the largest region.
  2. Use `skimage.transform.hough_circle` + `hough_circle_peaks` for a proper
     circle fit.
- Make `detect()` *measure* the dish by default, but allow an explicit override
  via `DetectionParams` (so the old behaviour is still reachable). Backward
  compatibility matters once people depend on you.
- If no plausible dish is found, **raise a clear custom exception** (e.g.
  `DishNotFoundError`) rather than returning a garbage mask. Add a custom
  exceptions module — bare `Exception` is discouraged in this lab.

**Tests to write:**
- Synthetic images (extend `conftest.py`) with the dish deliberately *off-centre*
  and at *different sizes* — assert the detected `(cx, cy, radius)` is close to
  the truth.
- A blank/garbage image → asserts `DishNotFoundError` is raised.
- A regression test: the centred synthetic plate still gives the same colony
  count as before.

**Stretch:** Save a debug overlay (the detected dish circle drawn on the image)
so users can visually confirm the dish was found correctly.

---

## Milestone 4 — CSV outputs and tidy data for downstream analysis

**Goal:** Alongside the pretty Excel report, emit machine-readable **tidy CSV**
files that drop straight into pandas, R, or a stats pipeline.

**Why it matters:** Excel is great for humans, terrible for reproducible
analysis. A tidy CSV is the universal currency of data analysis. This milestone
is where the "tidy data" idea from Milestone 1 pays off.

**Concepts you'll learn:** the `csv` module (or pandas); tidy/long data format;
why separating "report for humans" from "data for machines" matters;
reproducibility metadata.

**Spec:**
- Add `csv_output.py` with two writers:
  1. `write_colonies_csv(reports, path)` → one **long-format** table:
     columns `image, colony_id, area_px, area_pct, density, centroid_x,
     centroid_y`. One colony per row, every image stacked together. This is the
     tidy format — perfectly suited to `pandas.read_csv` + `groupby("image")`.
  2. `write_summary_csv(reports, path)` → one row per image (count, area %, mean
     density, dish area).
- Wire a `--csv` flag into the CLI (default on, or a separate flag — your call;
  justify it).
- **Reproducibility:** also write a small `run_metadata.json` recording the
  `DetectionParams` used, the package `__version__`, the date, and the list of
  input files. Future-you will thank present-you when a reviewer asks "what
  settings produced Figure 3?"

**Tests to write:**
- Write CSVs from a couple of fake `DetectionResult`s, read them back, assert the
  rows/columns/values are exactly right.
- Assert the long-format file has `sum(n_colonies)` data rows.
- Assert `run_metadata.json` round-trips (write it, load it, check the params
  match).

**Stretch:** Add an optional pandas dependency and a `to_dataframe()` helper for
notebook users. Discuss with Claude the trade-off of adding pandas as a
dependency (it's heavy) vs keeping the core lean and offering it as an "extra".

---

## Milestone 5 — Parameter validation and a config file

**Goal:** Validate detection parameters, and let users supply them from a config
file instead of remembering CLI flags.

**Why it matters:** A `dish_radius_frac` of `5.0` (instead of `0.5`) is nonsense
but currently accepted silently. And different plate types need different
settings — re-typing six flags every run is error-prone.

**Concepts you'll learn:** input validation; Pydantic `BaseModel` /
`field_validator`; loading config from TOML/YAML; the principle of "fail early,
fail clearly."

**Spec:**
- Add validation to `DetectionParams` (Pydantic is a natural fit here, and it's
  in the lab's standard toolkit): `0 < dish_radius_frac <= 0.5`,
  `threshold >= 0`, `min_colony_px > 0`, etc.
- Support `--config plate_settings.toml` that loads a `DetectionParams`. CLI
  flags override file values; file values override defaults (document this
  precedence clearly).

**Tests to write:**
- Each invalid parameter raises a validation error (use
  `pytest.raises(...)`).
- Loading a config file produces the expected `DetectionParams`.
- CLI-flag-over-file precedence works as documented.

---

## Milestone 6 — Continuous Integration (CI) and publishing to PyPI

**Goal:** Make GitHub automatically run your checks on every push, then publish
the package to PyPI so anyone can `pip install colony-counter`.

**Why it matters:** This is the final step from "my project" to "real,
installable scientific software." CI means a broken commit is caught
*automatically* before it reaches `main`. Publishing means the whole community
can use (and cite) your tool.

**Concepts you'll learn:** GitHub Actions; the test matrix; build artifacts;
PyPI / TestPyPI; trusted publishing; semantic versioning with commitizen.

**Spec:**
- Add `.github/workflows/ci.yml` that, on every push and PR, runs:
  `uv sync`, `uv run ruff check .`, `uv run ty check`, `uv run pytest`.
- Add a `release.yml` that builds and uploads to PyPI when you push a version
  tag. Use **TestPyPI first** to rehearse without polluting the real index.
- Address the `scikit-image` `FutureWarning`s (the `remove_small_objects` /
  `remove_small_holes` API change) before release, so a future scikit-image
  doesn't break installs.
- Add a coverage badge (`pytest-cov`) and a CI badge to the README.
- Do a real `uv run cz bump` to cut `v0.2.0`, and walk through the release with
  Helfrid.

**Tests to write:** CI *runs* your existing tests — the "test" here is that the
green checkmark appears on GitHub. Add `pytest-cov` and aim to keep coverage
meaningful (don't chase 100% for its own sake; cover the logic that matters).

---

## A few habits worth internalising

1. **One branch per milestone, one PR per branch.** Small, reviewable changes.
2. **Test-first when you can.** Writing the test clarifies what "done" means.
3. **Commit messages are documentation.** `uv run cz commit` guides you through
   the Conventional Commits format (`feat:`, `fix:`, `docs:`...). These drive
   automatic versioning.
4. **Separate computation from presentation.** Science logic shouldn't know
   about colours, spreadsheets, or argparse. This keeps it testable and
   reusable — it's the theme running through every milestone above.
5. **Fail loudly, not silently.** A wrong number with no warning is the most
   dangerous bug in research software. Raise clear exceptions; validate inputs.
6. **Ask Claude to explain, not just to do.** The goal is that *you* could
   rebuild any of this from scratch. Use it as a tutor that happens to type
   fast.

---

## Suggested order & rough effort

| # | Milestone | Effort | Main skill |
|---|---|---|---|
| 1 | Tidy, typed data structures | ½ day | dataclasses, tidy data |
| 2 | Rich CLI | 1 day | rich/typer, separation of concerns |
| 3 | Auto-detect the dish | 1–2 days | image processing, robustness |
| 4 | CSV / tidy outputs | ½–1 day | data formats, reproducibility |
| 5 | Validation + config file | ½–1 day | Pydantic, validation |
| 6 | CI + PyPI release | 1 day | GitHub Actions, packaging |

Good luck, Georgios — by the end of this you'll have built and published a real
piece of research software, and you'll understand every layer of it. That's a
genuinely valuable skill set. 🧫
