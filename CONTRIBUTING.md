# Contributing to steamlayer 🛠️

First off, thanks for taking the time to contribute! It's people like you that make `steamlayer` better for everyone.

## 🚀 Getting Started
This project uses [uv](https://github.com/astral-sh/uv) for dependency management and tooling.

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/steamlayer.git
   cd steamlayer
   ```

3. **Setup the enviroment:**
    ```bash
    uv sync --all-groups
    ```

## ✅ Code Quality Standards
We maintain high standards to keep the project resilient. Before submitting a PR, please ensure your code passes these checks:
- Linting & Formating: we use [ruff](https://github.com/astral-sh/ruff).
  ```bash
  uv run ruff check .
  uv run ruff format .
  ```

- Type Checking: we use [mypy](https://github.com/python/mypy).
  ```bash
  uv run mypy steamlayer --explicit-package-base --ignore-missing-imports
  ```

- Testing: We use [pytest](https://github.com/pytest-dev/pytest).
  ```bash
  uv run pytest
  ```

## 📬 Pull Request Process
1. Create a new branch for your feature or bugfix: `git checkout -b feat/cool-new-thing.`
2. Commit your changes with descriptive messages.
3. Push to your fork and submit a Pull Request.
4. Ensure the CI pipeline passes on your PR.

## ⚖️ License
By contributing, you agree that your contributions will be licensed under the project's MIT License.