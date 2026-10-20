# Changelog

All notable changes to `pyfinews` are documented in this file.

This project uses a simplified version of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Version numbers follow the principles of [Semantic Versioning](https://semver.org/), with the understanding that `0.y.z` releases are initial development releases and the public API may change.

## [0.1.2] - 2026-10-20

### Changed
- Updated the test suite for article-text extraction and Google News URL resolution to reflect the current implementations.
- Improved test coverage for success cases, error handling, input validation, and batch processing.

### Documentation
- Refined the README installation instructions and usage examples.
- Updated documentation to reflect the current dependency configuration and feature availability.

## [0.1.1] - 2026-10-20

### Changed
- Made article-text extraction and Google News URL resolution dependencies part of the standard installation, removing the need to install separate feature extras.
- Updated the README installation instructions, feature documentation, and usage examples.

### Fixed
- Corrected errors and outdated instructions in the README documentation.

## [0.1.0] - 2026-10-20

### Added
- Initial public release of `pyfinews`.
- Financial news headline discovery through Google News RSS.
- A high-level client API for searching news.
- Query-building, article models, filtering, and deduplication functionality.
- Configurable taxonomy and publisher data used by financial news queries.
- Optional article-page text extraction functionality when the relevant optional dependency is installed.

### Notes
- This is an initial development release. The public API may change in future `0.y.z` releases.
- See the README and package documentation for installation instructions, supported options, and usage examples.

[0.1.2]: https://github.com/sam-333/pyfinews/releases/tag/v0.1.2
[0.1.1]: https://github.com/sam-333/pyfinews/releases/tag/v0.1.1
[0.1.0]: https://github.com/sam-333/pyfinews/releases/tag/v0.1.0
