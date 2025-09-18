# Copilot Instructions — Geralds_Helper

These are repository-level guidelines intended to instruct any AI assistant (including GitHub Copilot) and human contributors on the conventions and hard rules for code generated or added to this repository.

These rules are normative for all new code and pull requests. Automation (CI) will run a lightweight check that flags violations; use the guidance below to avoid false positives.

1. Python version

   - Target Python: 3.13.7. All generated code must be valid and idiomatic for Python 3.13.7.

2. Maintainability and style

   - Generate clean, readable, well-documented code. Favor clarity over cleverness.
   - Use type annotations for public APIs and functions where they help maintainability.
   - Keep functions small (single responsibility) and prefer composition over inheritance unless clearer.
   - Prefer standard library and well-maintained dependencies.

3. File size and project structure (hard rule)

   - No single source file should exceed 300 lines of code (LOC) excluding tests and generated docs.
   - If a file would exceed 300 LOC, split it into multiple modules or subpackages with a clear structure. Subpackages are preferred for logical grouping (e.g., `utils/`, `models/`, `services/`).
   - Use `__init__.py` to expose a minimal public surface for packages.

4. Tests and determinism (hard rule)

   - Every new feature or substantial change must include deterministic unit tests that cover the happy path and at least one edge case.
   - Tests must be deterministic: avoid reliance on wall-clock time, randomness, thread timing, or external services unless properly mocked. Use fixed seeds for RNG and mock external dependencies.
   - Prefer `pytest` with fixtures and simple assertions. Tests should be placed under `tests/` following the repository convention.

5. Performance and correctness

   - Prefer algorithms and data structures that are appropriate for the expected data size. Document complexity and trade-offs in comments or docstrings.

6. Documentation

   - Public functions, classes, and modules must include brief docstrings explaining purpose, arguments, return values, and exceptions.

7. CI enforcement and reviews

   - The repository includes a lightweight enforcement script and CI workflow which will flag:
     - Files >300 LOC.
     - New/changed source files without corresponding tests.
     - Tests that contain common non-deterministic patterns (e.g., calls to `random.random()` without `seed`, `time.sleep()` in tests, network calls without mocking).
   - If automation flags a false positive, add a short note in the PR describing why the exception is safe and add a comment in the code referencing the PR.

8. Exceptions

   - Exceptions to hard rules must be approved in code review with explicit reasoning and a documented mitigation strategy.

9. Example
   - If a single module `big_module.py` would become 800 LOC, split it into `big_module/__init__.py`, `big_module/core.py`, `big_module/helpers.py`, and add tests in `tests/test_big_module.py`.

By following these rules, Copilot and other contributors will produce maintainable, testable, and deterministic Python code suitable for long-term maintenance.

---

Notes for maintainers: See `scripts/check_copilot_guidelines.py` and `.github/workflows/copilot-guidelines.yml` for the enforcement implementation. The enforcement is intentionally conservative and meant to guide contributors rather than fully replace human review.
