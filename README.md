# App

Initial Python project setup.

## Setup

```bash
python -m venv .venv
```

Activate the environment:

### Windows PowerShell

```bash
.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install pre-commit hooks:

```bash
pre-commit install
```

Run checks:

```bash
black --check src tests
isort --check-only src tests
flake8 src tests
mypy src
pytest
```
