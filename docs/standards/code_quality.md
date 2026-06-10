# Code Quality Standard

## 1. Tools

Here is the complete documentation of the code quality tools, settings, and rule groups configured in this project.

---

### 1.1 Execution Order (Pre-Commit Pipeline)

When running checks via pre-commit (`.venv\Scripts\pre-commit run --all-files`), they execute sequentially in this order as configured in `.pre-commit-config.yaml`

1. **`trailing-whitespace`**: Removes trailing whitespaces from all files.
2. **`end-of-file-fixer`**: Ensures files terminate with a single empty newline.
3. **`check-yaml`**: Validates YAML syntax.
4. **`check-toml`**: Validates TOML syntax.
5. **`check-added-large-files`**: Prevents tracking files larger than 500KB.
6. **`detect-secrets`**: Scans for credential leaks (API keys, passwords) against `.secrets.baseline`
7. **`ruff`**: Runs lint checks, import sorting, complexity checks, security scanning, and auto-fixes issues where possible.
8. **`ruff-format`**: Enforces strict code formatting.
9. **`mypy`**: Validates static type definitions.

---

### 1.2. Ruff Rule Configurations (By Category)

The following rule groups are enabled via `tool.ruff.lint.select` in `pyproject.toml`.

#### 1.2.1. Code Logic, Stability & Modernization

* **`F` (Pyflakes):** Catches logical errors, syntax errors, and basic mistakes (like executing invalid code).
* **`B` (Bugbear):** Detects design flaws, code smells, and tricky, hard-to-spot Python bugs.
* **`UP` (Pyupgrade):** Suggests modern Python syntax improvements automatically.
* **`YTT` (Flake8-2020):** Prevents bad code patterns when checking the current running Python version.
* **`ASYNC` (Flake8-async):** Checks for proper, non-blocking usage of `async` and `await`.
* **`BLE` (Flake8-blind-except):** Catches dangerous "bare" `except:` clauses that swallow all errors.
* **`FBT` (Flake8-boolean-trap):** Flags confusing function signatures that take raw `True`/`False` arguments without context.
* **`C4` (Flake8-comprehensions):** Optimizes how lists, dicts, and sets are constructed.
* **`PIE` (Flake8-pie):** Offers generic code improvements and linting tweaks.
* **`SIM` (Flake8-simplify):** Gives hints to refactor overly complex code into simple one-liners.
* **`FURB` (Refurb):** Modernizes old, clunky Python patterns into clean, idiom-accurate code.

#### 1.2.2. Styling, Naming & Structure

* **`E`, `W` (Pycodestyle):** Enforces standard PEP 8 formatting errors and warnings.
* **`I` (Isort):** Grouping and sorting rules for your `import` statements.
* **`N` (PEP8 Naming):** Enforces casing standards (e.g., `CamelCase` for classes, `snake_case` for variables).
* **`COM` (Flake8-commas):** Enforces consistent trailing comma usage.
* **`ISC` (Flake8-implicit-str-concat):** Flags implicitly split strings (like `"a" "b"`), which can cause sneaky bugs.
* **`ICN` (Flake8-import-conventions):** Ensures common libraries use standardized aliases (like `import pandas as pd`).
* **`Q` (Flake8-quotes):** Keeps single vs. double quote usage completely identical across files.
* **`SLOT` (Flake8-slots):** Optimizes memory footprint by prompting `__slots__` where useful.
* **`RUF` (Ruff internal):** Extra rules built by Ruff's creators to enforce clean architecture.

#### 1.2.3. Documentation & Cleanliness

* **`D` (Pydocstyle):** Enforces docstring syntax formatting rules.
* **`ANN` (Flake8-annotations):** Enforces explicit type annotations for function parameters and return types.
* **`INP` (Flake8-no-pep420):** Protects directory layout structures by requiring an `__init__.py` file in every folder.
* **`ARG` (Flake8-unused-arguments):** Flags any arguments defined in a function that the code never actually uses.
* **`TD`, `FIX` (Flake8-todos & Fixme):** Monitors, formats, and tracks `TODO` and `FIXME` text strings in comments.

#### 1.2.4. Security, Execution & Logging

* **`S` (Bandit):** Static security analysis tracking down vulnerabilities and weaknesses.
* **`EXE` (Flake8-executable):** Checks script execution permissions and shell shebang (`#!/usr/bin/env python`) headers.
* **`LOG`, `G` (Flake8-logging & formats):** Ensures logging configurations are optimal and safe from structural string corruption.
* **`DTZ` (Flake8-datetimez):** Blocks timezone-naive datetime objects to prevent time-calculation errors.
* **`T10` (Flake8-debugger):** Strictly blocks accidentally committing debugging tools like `breakpoint()` or `import pdb`.

#### 1.2.5. Control Flow & Language Specifics

* **`RSE`, `RET` (Flake8-raise & return):** Validates precise code control paths for cleaner outputs and exceptions.
* **`SLF` (Flake8-self):** Flags class method violations regarding `self`.
* **`FA` (Flake8-future-annotations):** Normalizes modern post-Python 3.7 styling for code type-hints.
* **`PYI` (Flake8-pyi):** Structural validation checks specifically for `.pyi` type stub files.
* **`TC` (Flake8-type-checking):** Moves imports around safely to reduce runtime overhead for pure typing variables.
* **`INT` (Flake8-gettext):** Tracks software translation or localization rules.
* **`PTH` (Flake8-use-pathlib):** Migrates legacy `os.path` methods over to modern object-oriented `pathlib`.
* **`TRY` (Tryceratops):** Enforces clean, anti-pattern free usage of `try/except` constructs.
* **`FLY` (Flynt):** Prompts conversion of legacy `%` formatting or `.format()` strings to modern f-strings.

#### 1.2.6. External Libraries & Ecosystems

* **`PT` (Flake8-pytest-style):** Validates clean and modern Pytest testing architecture.
* **`PD` (Pandas-vet):** Curates code correctness bugs specific to working with Pandas DataFrames.
* **`NPY` (NumPy rules):** Catches syntax optimization errors for NumPy data matrices.
* **`DJ` (Flake8-django):** Framework-specific validations for Django code structures.
* **`FAST`, `AIR` (FastAPI & Airflow):** Ecosystem-specific linting validations for web-routing and pipeline frameworks.
* **`PERF` (Perflint):** Highlights slow, anti-performant patterns (like slow loops).
* **`PL` (Pylint):** Integrates standard refactoring and convention suggestions inherited from classic Pylint.
* **`PGH` (Pygrep-hooks):** Custom regex rules checking for generic anti-patterns (like un-targeted `# noqa` suppressions).

### 1.3. Explicit Ignore Rules

The following rules are ignored globally in `tool.ruff.lint.ignore` to resolve tool conflicts:

* **`FBT003`**: Flags boolean position values in function calls.
* **`D203` / `D212` / `D400` / `D401` / `D415`**: Docstring styles ignored to conform cleanly to Google style conventions.
* **`S311`**: Permits pseudo-random number generators (critical for non-cryptographic quant simulation models).
* **`PERF401`**: Disables performance checks converting loop formats to list comprehensions.
* **`RET504`**: Allows assignments right before returning (aids readability/debugging).
* **`FA102`**: Allows missing future annotations import when syntax PEP 604 is present.
* **`TRY003`**: Permits long exception messages outside custom error wrapper classes.
* **`EM101`**: Permits raw string literals directly inside exception constructors.
* **`TC002` / `TC003`**: Relaxes typing-import positions to avoid circular dependency bugs.
* **`COM812` / `ISC001`**: Formatter-conflict rules disabled to support clean `ruff-format` actions.

### 1.4. Test Environment Scope (`per-file-ignores`)

For files matching `test_*.py`, `*_test.py`, and `conftest.py`, standard rule enforcement is relaxed:

* **Ignored rules**: `["S101", "S105", "S106", "S107", "PLR2004", "SLF001", "D", "ARG001", "PLC0415", "EM102", "ANN"]` (allows `assert` statements, hardcoded mock values, skips mandatory docstrings/annotations inside test functions).

### 1.5. Other Tools Configuration

#### 1.5.1. `pytest` (Testing Environment)

* **`pythonpath = ["src"]`**: Ensures package imports resolve correctly.
* **`addopts`**: Runs coverage check automatically over `src/app`, outputting to HTML and terminal. Fails build if total branch-trace coverage drops below **80%**.

#### 1.5.2. `mypy` (Type Verification)

* **`strict = true`**: Enforces strict typing logic globally.
* **`warn_redundant_casts = true`**: Warns when casting types redundantly.
* **`disallow_untyped_defs = true`**: Generates build errors if function definitions lack annotations.

### 1.6. Required Commands

```bash
ruff check
mypy api tools scripts
pytest
```

### 1.7. Coverage Gate

Coverage must never fall below 80% for both individual file and package level.

```bash
pytest --cov=tools --cov=api --cov=scripts --cov-fail-under=80
```

## 2. Production Code Standard

When writting code, keep the result clear, safe, testable, and maintainable without adding unnecessary complexity.

File must include:

- A clear module-level docstring.
- Clear class and function docstrings.
- Type hints for all public functions and methods.
- Input validation where appropriate.
- Output validation where appropriate.
- Structured logging for important runtime events.
- Safe error handling with explicit, helpful exceptions.
- No unnecessary hardcoded values.
- Clean function and class organization.
- Small, focused functions.
- Separation of business logic from I/O where possible.
- Deterministic behavior where required.
- Production-friendly defaults.
- Compatibility with future unit testing.
- Compatibility with future agent or tool usage where relevant.
- Clear naming conventions.
- Minimal but useful comments.
- No unnecessary complexity.

### 2.1. Logging Standard

Every production Python file should define a module logger:

```python
from tools.utils import logger
```

Use logging for important events, warnings, validation failures, and recoverable
errors.

Avoid using `print()` in production code. Use `print()` only in simple examples,
CLI entry points, or scripts where stdout is the intended interface.

### 2.2. Error Handling Standard

Use explicit exceptions with helpful error messages.

Avoid silent failures. If a failure is recoverable, log enough context for a
future maintainer or agent to understand what happened.

Avoid broad `except Exception` blocks unless there is a clear reason. When a
broad exception handler is necessary, always log, re-raise, or convert the error
to a more specific domain exception.

### 2.3. Documentation Standard

Each public function or method should explain:

- What it does.
- Parameters.
- Return value.
- Raised exceptions, where relevant.

Docstrings should be useful to humans, tests, and future agent/tool workflows.
Avoid restating obvious implementation details.

### 2.4. Testing Standard

After rewriting the main file, also create or update a unit test file.

The test file should include:

- Normal expected usage tests.
- Edge case tests.
- Invalid input tests.
- Error handling tests.
- Regression-style tests where appropriate.
- Mocking where external systems are involved.
- Clear test names.

Tests should verify behavior, not implementation details, unless the
implementation detail is part of the contract.

### 2.5. Usage Example Standard

After rewriting the main file, also create or update a usage example file that
shows how the file should be used in a realistic HaruQuant workflow.

The example should be:

- Simple.
- Runnable.
- Easy to understand.
- Focused on the intended workflow rather than exhaustive coverage.

### 2.6. Write Output Format

When providing rewritten code, return separate files using filename headers:

```text
# filename: path/to/file.py
```

Then provide the full code for that file.

Create at least:

- The standardized production file.
- The unit test file.
- The usage example file.

Add supporting files only when they are truly necessary.

### 2.7. Production-Readiness Checklist

At the end of a write, provide a checklist confirming:

- Module, class, and public function docstrings are present.
- Public functions and methods have type hints.
- Inputs and outputs are validated where appropriate.
- Logging follows the module logger standard.
- Errors are explicit, helpful, and not silently swallowed.
- Business logic is separated from I/O where practical.
- Functions and classes are small and focused.
- Hardcoded values are avoided unless justified.
- Defaults are deterministic and production-friendly.
- Unit tests cover normal usage, edge cases, invalid input, and errors.
- External systems are mocked in tests.
- A realistic usage example is included.
- The implementation avoids unnecessary complexity.
