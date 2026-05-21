# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- CHANGELOG.md file to track updates relevant to library consumers
- new dataclass LHEHeader
- LHEEvent now also contains `<scales>`
- LesHouchesEvents is a synonym for LHEFile now

### Changed

- weights and weightgroups are now no longer stored in LHEInit.weightgroup but in LHEHeader.initrwgt.entities. They are thus part of the `<header>` instead of `<init>` as demanded by LHE specification.
- `LHEInit` no longer has `LHEVersion`. Instead the version is stored `LesHoucheEvents.version`.

### Removed

- The following old deprecated functions were removed: `read_lhe_file`, `read_lhe_init`, `read_lhe`, `read_lhe_with_attributes`, `read_num_events`, `write_lhe_file_string`, `write_lhe_string`, `write_lhe_file_path`, `write_lhe_file`

## [1.0.4] - 2026-05-15

## [1.0.3] - 2026-05-15

### Added

- error handling for rwgt and weights parameters

[unreleased]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.0.4...HEAD
[1.0.4]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.0.2...v1.0.3
