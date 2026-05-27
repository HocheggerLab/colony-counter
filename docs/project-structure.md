# Understanding the Project Structure

A guide for Georgios — how this project is laid out, why research software is
organised this way, and what each piece does. Read this once end-to-end, then
keep it open as a reference while you work.

> **The big idea:** A script is something *you* run on *your* machine. A
> *package* is something *anyone* can install and reuse. Turning a working
> script into a maintainable package is most of what "research software
> engineering" actually is. This document explains the scaffolding that makes
> that possible.

---

## 1. The bird's-eye view

```
colony-counter/
├── pyproject.toml          ← the single source of truth for the project
├── uv.lock                 ← exact versions of every dependency (auto-managed)
├── .python-version         ← which Python version this project uses
├── README.md               ← the front page: what it is, how to use it
├── LICENSE                 ← legal terms (MIT here)
├── .gitignore              ← files git should never track (caches, venvs)
├── .pre-commit-config.yaml ← automatic checks before each commit
│
├── src/
│   └── colony_counter/     ← THE ACTUAL PACKAGE (the importable code)
│       ├── __init__.py     ← marks the folder as a package; defines the public API
│       ├── params.py       ← tunable parameters (one dataclass)
│       ├── detection.py    ← the image-analysis pipeline
│       ├── excel.py        ← writes the Excel report
│       ├── visualization.py← draws the annotated mask figures
│       ├── cli.py          ← the command-line interface
│       ├── config.py       ← logging + environment configuration
│       └── py.typed        ← signals "this package ships type hints"
│
├── tests/                  ← automated tests (mirror the src/ layout)
│   ├── conftest.py         ← shared test fixtures
│   ├── test_params.py
│   ├── test_detection.py
│   ├── test_excel.py
│   └── test_cli.py
│
└── docs/                   ← documentation (you are here)
```

The rule of thumb: **everything that gets installed lives in `src/`,
everything that checks the code lives in `tests/`, and everything that
configures the project lives in the root.**

---

## 2. The virtual environment, and why `uv`

### The problem virtual environments solve

Your laptop has one system Python. If project A needs `numpy 1.26` and project
B needs `numpy 2.4`, installing both globally is a fight nobody wins. A
**virtual environment** is a private, per-project folder containing its own
Python and its own copy of every dependency. Activate it, and `python` means
*this project's* Python.

You can see it in this repo: the `.venv/` folder. It's git-ignored — it's
built from the lockfile, never committed.

### Why `uv` specifically

`uv` is a modern, extremely fast replacement for `pip` + `venv` +
`virtualenv` + `pip-tools`, all in one tool. In this lab we use `uv`
**exclusively** — never `pip` directly. The commands you actually need:

| Command | What it does |
|---|---|
| `uv sync` | Create the `.venv` (if needed) and install everything from the lockfile. **Run this first after cloning.** |
| `uv add scipy` | Add a new runtime dependency and update `pyproject.toml` + lockfile. |
| `uv add --dev pytest` | Add a *development-only* dependency (test/lint tools). |
| `uv run pytest` | Run a command *inside* the venv without manually activating it. |
| `uv run colony-counter ...` | Run our CLI inside the venv. |

> **Key habit:** prefix project commands with `uv run`. That guarantees you're
> using the project's environment, not your system Python. `uv run pytest` is
> safer than `pytest`.

### The lockfile (`uv.lock`)

When you `uv add` something, you ask for e.g. "numpy 2.x". But numpy itself
depends on other things, which depend on other things... The **lockfile**
records the *exact* version of every package in the whole tree, so that the
environment is reproducible: you, Helfrid, and a CI server all get byte-for-byte
the same dependencies. **Commit the lockfile. Never edit it by hand.**

---

## 3. `pyproject.toml` — the control centre

This one file replaces the old jumble of `setup.py`, `requirements.txt`,
`setup.cfg`, and tool-specific config files. It has a few key sections:

```toml
[project]                    # metadata: name, version, description, authors
dependencies = [...]         # what users need to RUN the package
requires-python = ">=3.13"

[project.scripts]            # this line is what creates the `colony-counter` command!
colony-counter = "colony_counter.cli:main"

[build-system]               # how to BUILD the package for distribution
[dependency-groups]          # dev = [...] tools only developers need
[tool.ruff]                  # config for the linter/formatter
[tool.pytest.ini_options]    # config for the test runner
[tool.commitizen]            # config for version bumping
```

Two things worth dwelling on:

- **`dependencies` vs `dependency-groups.dev`.** A user installing
  `colony-counter` to count colonies needs numpy and scikit-image (runtime
  dependencies). They do *not* need pytest or ruff — those are *development*
  tools. Keeping them separate means users install less and your package is
  lighter.

- **`[project.scripts]`.** The line `colony-counter = "colony_counter.cli:main"`
  means: "when this package is installed, create a terminal command called
  `colony-counter` that runs the `main` function in `colony_counter/cli.py`."
  That's the magic that turns `python some_script.py` into a real installed
  tool.

---

## 4. The `src/` layout — and why not just put code in the root?

You'll see two layouts in the wild:

- **Flat layout:** `colony_counter/` sits directly in the project root.
- **`src/` layout:** the package lives in `src/colony_counter/`. ← we use this.

The `src/` layout has one decisive advantage for research code: it forces you
to test the **installed** package, not the loose files lying around. With a flat
layout, Python can accidentally import your code straight from the working
directory, which can hide bugs ("works on my machine" because of a file that
never actually ships). With `src/`, your code must be properly installed
(`uv sync` does this in *editable* mode) before it can be imported — so your
tests exercise exactly what your users get. It's the small discipline that
prevents a whole class of packaging surprises.

---

## 5. `__init__.py` — what makes a folder a package

Any directory containing an `__init__.py` file is a Python **package** — a
thing you can `import`. The file can be empty (its mere presence is enough), but
it usually does two jobs:

```python
# src/colony_counter/__init__.py  (abridged)

from .config import set_env_vars
from .detection import ColonyRecord, DetectionResult, detect
from .excel import ImageReport, write_workbook
from .params import DEFAULT_PARAMS, DetectionParams
from .visualization import save_mask_figure

__version__ = "0.1.0"

set_env_vars()

__all__ = ["detect", "DetectionParams", "DetectionResult", ...]
```

What's going on here:

1. **It defines the public API.** By importing `detect`, `DetectionParams`,
   etc. up into the top level, a user can write the clean
   `from colony_counter import detect` instead of the verbose
   `from colony_counter.detection import detect`. You decide what's "public"
   by what you surface here.

2. **`__version__`** is the conventional place to record the package version
   (commitizen keeps it in sync with `pyproject.toml` automatically).

3. **`__all__`** is a list of names that `from colony_counter import *` will
   expose. More usefully, it documents intent: "these are the things I promise
   to keep stable."

4. The `.` in `from .detection import ...` means "relative to *this* package."
   It's how modules inside the same package refer to each other.

> **Mental model:** `__init__.py` is the package's reception desk. It decides
> what visitors see first and routes them to the right room.

### Modules vs packages

- A **module** is a single `.py` file (e.g. `detection.py`).
- A **package** is a folder of modules with an `__init__.py`
  (e.g. `colony_counter/`).

Splitting one big script into modules (as we did — `detection`, `excel`,
`visualization`, `cli`) is the heart of making code maintainable: each file has
**one job**, is short enough to hold in your head, and can be tested in
isolation.

---

## 6. Why we split the original script into modules

The original `count_colonies.py` was ~320 lines doing everything: loading
images, analysing them, drawing figures, writing Excel, and parsing the command
line. That works, but it's hard to test, hard to reuse, and hard to change
without fear. We split it by **responsibility**:

| Module | Single responsibility | Depends on |
|---|---|---|
| `params.py` | Hold the tunable numbers in one typed place | nothing |
| `detection.py` | Image → measurements (the science) | params |
| `visualization.py` | Measurements → annotated PNG | detection |
| `excel.py` | Measurements → Excel report | detection |
| `cli.py` | Glue: read args, call the above, report progress | all of them |

Notice the **dependency direction**: `detection.py` knows nothing about Excel
or the command line. That means you can `from colony_counter import detect` in a
Jupyter notebook and use the science without dragging in CLI or spreadsheet
code. This is *separation of concerns*, and it's the single most important habit
in writing reusable scientific code.

---

## 7. What is testing about? (the short version)

A test is just code that runs your code and **checks the answer is right** —
automatically, every time, so you never have to manually re-verify by eye.

### Why it matters for *research* software

If your colony counts feed into a figure in a paper, a silent bug isn't an
inconvenience — it's a wrong scientific result. Tests are how you build (and
keep) confidence that the numbers mean what you think they mean. They also let
you **refactor fearlessly**: change the internals, re-run the tests, and if
they still pass, you know you didn't break the behaviour.

### What a test looks like

A test follows the **Arrange → Act → Assert** pattern:

```python
def test_purple_signal_is_zero_for_white_pixels() -> None:
    img = np.full((4, 4, 3), 255, dtype=np.uint8)  # Arrange: a white image
    signal = purple_signal(img)                     # Act: run the function
    assert (signal == 0).all()                      # Assert: white → no signal
```

`assert` says "this must be true; if it isn't, fail loudly." Run the whole
suite with:

```bash
uv run pytest
```

### Key concepts you'll meet in our `tests/` folder

- **Fixtures** (`conftest.py`): reusable setup. Our `synthetic_plate_path`
  fixture *generates a fake plate image with known colonies* so we can assert
  "the detector should find exactly 3." You don't need real microscope images
  to test — you can manufacture inputs whose answers you already know.
- **`tmp_path`**: a pytest-provided temporary folder, fresh per test. We write
  Excel files and masks there so tests never pollute your real disk.
- **Edge cases**: we test the *blank plate* (zero colonies) and *empty input*
  (no images) on purpose. Bugs love edge cases.
- **Unit vs integration**: `test_purple_signal_*` tests one tiny function (a
  *unit* test). `test_main_runs_end_to_end` runs the whole CLI from arguments to
  output files (an *integration* test). You want both.

> **Rule of thumb for new code:** every time you add a function, ask "what's a
> simple input where I already know the right answer?" — and write that as a
> test. If a bug ever slips through, add a test that reproduces it *before* you
> fix it, so it can never come back.

---

## 8. The supporting cast (root-level files)

- **`.gitignore`** — lists files git should ignore: the `.venv/`, `__pycache__/`
  caches, `.ruff_cache/`, results folders. Rule: never commit generated files
  or anything machine-specific.
- **`.pre-commit-config.yaml`** — runs ruff (format + lint) and the type checker
  automatically *before* each commit, so badly-formatted code never makes it
  into history. Install once with `uv run pre-commit install`.
- **`.python-version`** — tells `uv` (and `pyenv`) which Python this project
  targets, so everyone uses the same one.
- **`LICENSE`** — without it, others legally cannot reuse your code. MIT is a
  common, permissive choice for academic tools.

---

## 9. The quality toolchain (memorise these four commands)

| Tool | Command | What it gives you |
|---|---|---|
| **ruff** (format) | `uv run ruff format .` | Consistent layout — no more arguing about spaces. |
| **ruff** (lint) | `uv run ruff check .` | Catches likely bugs, unused imports, bad patterns. |
| **ty** (types) | `uv run ty check` | Verifies type hints are consistent (catches whole bug classes). |
| **pytest** | `uv run pytest` | Runs the tests. |

Run all four before you commit. Pre-commit will nag you if you forget. Don't
bypass the hooks with `--no-verify` — fix the underlying issue instead.

---

## 10. The mental model to take away

```
        you write & edit                 the tooling protects you
   ┌──────────────────────┐          ┌──────────────────────────────┐
   │  src/colony_counter/  │          │  ruff   → style & lint        │
   │  (one job per module) │ ───────► │  ty     → type correctness    │
   │                       │          │  pytest → behaviour is right  │
   │  tests/ (prove it)    │          │  uv     → reproducible env    │
   └──────────────────────┘          └──────────────────────────────┘
                │                                   │
                └──────────► pyproject.toml ◄───────┘
                        (the single control centre)
```

Get comfortable with this skeleton and you can build *any* Python research tool.
The science changes; the scaffolding stays the same.

---

### Further reading

- The official Python Packaging guide: <https://packaging.python.org/>
- `uv` docs: <https://docs.astral.sh/uv/>
- `pytest` getting started: <https://docs.pytest.org/en/stable/getting-started.html>
- Ruff: <https://docs.astral.sh/ruff/>

When in doubt, ask Claude Code to explain any file in this repo line by line —
that's exactly what it's good at.
