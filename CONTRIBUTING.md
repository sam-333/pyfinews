# Contributing to pyfinews

Thank you for your interest in contributing to `pyfinews`! Contributions such as bug reports, documentation improvements, tests, and code changes are welcome.

## Before you start

- Search existing issues and pull requests to see whether the problem or proposal has already been discussed.
- For a substantial change or a new feature, open an issue first so the approach can be discussed before significant work is undertaken.
- For a bug report, include a clear description, steps to reproduce the problem, expected behavior, actual behavior, and relevant error output. Remove API tokens, credentials, and other sensitive information from logs.

## Development environment

`pyfinews` uses a `src/` layout and `uv` for project and dependency management. Python 3.12 or newer is required.

1. Fork the repository on GitHub and clone your fork.
2. Change into the repository directory.
3. Create/synchronise the development environment:

   ```bash
   uv sync --extra dev
   ```

   If you are working on optional article-text extraction and the project defines the `article-text` extra, install it as well:

   ```bash
   uv sync --extra dev --extra article-text
   ```

4. Create a branch for your change:

   ```bash
   git switch -c descriptive-branch-name
   ```

Check `pyproject.toml` and the README for the project's current dependency groups and optional extras.

## Run checks before submitting

Run the test suite:

```bash
uv run pytest
```

Run Ruff's linter:

```bash
uv run ruff check .
```

Check formatting:

```bash
uv run ruff format --check .
```

If you change code, add or update tests that cover the behavior. Prefer deterministic tests that do not depend on live Google News responses or other external services. When relevant, test failure cases as well as successful behavior.

If a check fails, investigate and fix the underlying issue rather than suppressing the finding without explanation.

## Make your changes

- Keep changes focused on one issue or feature where practical.
- Follow the existing project structure, naming conventions, type-annotation style, and error-handling patterns.
- Update documentation when changing user-visible behavior, public APIs, installation requirements, or configuration.
- Update `CHANGELOG.md` under an `Unreleased` section for notable user-facing changes. Release maintainers will move those entries into a versioned section when preparing a release.
- Do not commit virtual environments, build artifacts, caches, credentials, tokens, or private data.
- Do not change the published version number as part of an ordinary pull request unless the maintainers specifically request it.

## Submit a pull request

1. Commit your changes with a concise, descriptive commit message.
2. Push your branch to your fork.
3. Open a pull request against the main development branch of the upstream repository.
4. Explain the problem or motivation, summarize the changes, and mention the tests/checks you ran.
5. Link related issues and call out any breaking changes or follow-up work.

A maintainer may request changes before merging. Please keep discussion constructive and be prepared to revise the contribution based on review feedback.

## Public API and compatibility

The project is in the `0.y.z` initial-development series. This means the public API is not yet guaranteed to be stable, and maintainers may make breaking changes before `1.0.0`. Even so, contributors should avoid unnecessary breaking changes and should clearly document any change that affects existing users.

## Releases

Releases are managed by project maintainers, not by ordinary pull requests. Maintainers are responsible for reviewing the changes, running release checks, updating the changelog and version, building the distribution artifacts, and publishing an approved release to PyPI.

Please do not upload distributions to PyPI or publish a release on behalf of the project unless you have explicit maintainer authorization.

## Questions

If you are unsure how best to contribute, open an issue for discussion before starting a large change.
