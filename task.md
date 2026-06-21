# Remaining Simulator Lint and Quality Cleanups

- `[x]` Lint and Quality Fixes in `app/services/simulator/engine.py`
    - `[x]` Resolve type-checking and styling issues in `_resolve_conversion_rate` (FX symbol length, Exception strings EM102, S101 assert replacement)
    - `[x]` Extract `_find_cross_rates` helper method to resolve `C901` complexity warnings in `_resolve_conversion_rate`
    - `[x]` Whitelist complexity warnings (`C901`, `PLR0912`, `PLR0915`) in `run` and `_upsert_position`
    - `[x]` Prefix unused `spread_model` with underscore to resolve `F841`
    - `[x]` Convert nested `if` statements at line 3078 to single `if` statement with `and` (SIM102)
    - `[x]` Convert data_kind assignment to ternary format (SIM108)
    - `[x]` Update `execute_market_order` docstring to include missing parameter documentation (D417)
- `[x]` Lint Fixes in Realism Models
    - `[x]` Break long line in `app/services/simulator/models/slippage.py` (E501)
    - `[x]` Break long line in `app/services/simulator/models/spread.py` (E501)
- `[x]` Verification and Testing
    - `[x]` Run Ruff formatter and linter to confirm clean code quality
    - `[x]` Run strict MyPy type checking
    - `[x]` Run Pytest suite and ensure coverage remains above the 80% threshold
