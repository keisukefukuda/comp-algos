# Python Package Management with uv

Use uv exclusively for Python package management in this project.
uv is possibly installed /opt/homebrew/bin/uv or /home/user/.local/bin/uv

## Package Management Commands
- All Python dependencies **must be installed, synchronized, and locked** using uv
- Never use pip, pip-tools, poetry, or conda directly for dependency management

## Running Python Code
- Run Python tools like Pytest with `uv run pytest` or `uv run ruff`

## Managing Scripts with PEP 723 Inline Metadata

- Run a Python script with inline metadata (dependencies defined at the top of the file) with: `uv run script.py`

## Code Quality Commands
- Linting: uv run ruff check blueprint/ tests/
- Formatting: uv run ruff format blueprint/ tests/
- Type Checking: uv run ty check blueprint/
- Testing: uv run pytest tests/ -v
- Pre-commit: uv run pre-commit run --all-files

## How to run pytest
 - In python/ directory, run `env PYTHONPATH=. uv run pytest tests`
