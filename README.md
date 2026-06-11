# HaruQuantAI

Modular, AI-assisted quantitative trading platform designed for safe service-tool boundaries, governed trading, reproducible research, and strict risk controls.

---

## Project Structure

This repository is structured as a modular monolith containing a Python backend and a Next.js frontend:

*   `/api`: FastAPI backend gateways, routing, and middlewares.
*   `/ui`: Next.js frontend workspace (TypeScript, Tailwind CSS, Radix UI).
*   `/tools`: Core quantitative and trading logic modules (data, indicators, risk, simulation, etc.).
*   `/agentic`: AI Agent configuration, runtimes, security policies, and schemas.
*   `/docs`: System architecture design, standard definitions, and requirements.

For design details, module boundaries, and implementation invariants, see [docs/ARCHITECTURE.md](file:///c:/Users/rharu/Documents/MyApplications/Quant/docs/ARCHITECTURE.md).

---

## Getting Started

### 1. Backend Setup (Python)

Ensure you have Python 3.9+ installed.

1.  **Create and activate virtual environment**:
    ```bash
    # Create environment
    python -m venv .venv

    # Activate (Windows PowerShell)
    .venv\Scripts\Activate.ps1

    # Activate (macOS / Linux)
    source .venv/bin/activate
    ```

2.  **Install dependencies**:
    ```bash
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    ```

3.  **Install pre-commit hooks**:
    ```bash
    pre-commit install
    ```

### 2. Frontend Setup (Next.js)

Ensure you have Node.js 18+ and npm installed.

1.  **Navigate to the UI directory & install dependencies**:
    ```bash
    cd ui
    npm install
    ```

2.  **Run the local development server**:
    ```bash
    npm run dev
    ```

---

## Verifying the Project

To run code formatters, type checks, and backend test suites locally:

```bash
# Code formatting and lint check
ruff check src tests
ruff format --check src tests

# Static type checking
mypy src

# Run pytest unit tests
pytest
```
