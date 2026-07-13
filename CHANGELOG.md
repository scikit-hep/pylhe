# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-07-13

### Added

- Support LHEH5 HDF5 files for reading and writing, including `LHEHDF5Format`, `HDF5_FORMAT`, and `HDF5_GZ_FORMAT`.
- CHANGELOG.md file to track updates relevant to library consumers.
- New dataclass `LHEHeader` for `<header>` block.
- Added `<scales>` to `LHEEvent`.
- New `LesHouchesEvents` is a synonym for `LHEFile`.
- New `LHEGenerator` dataclass to represent the `<generator>` block in the `<init>`.
- New `LHEInitRWGT`, `LHEInitRWGTWeightGroup` and `LHEInitRWGTWeight` dataclasses.
- Benchmarking of write performance.
- `LHEOutputFormat` class to replace the `rwgt` and `weights` bool.
- New `LHEEvent.mother_indices()` and `LHEEvent.mothers(particle)` helpers.
- `to_awkward()` now accepts an `LHEFile` / `LesHouchesEvents` object directly.
- `LHEXMLFormat` now has a `version` attribute to select the LHE version for output (V1, V3).

### Changed

- `write()`, `tolhe()`, and `tofile()` now use format objects (`LHEXMLFormat` / `LHEHDF5Format`) and `LHEWeightFormat` instead of the old `rwgt`, `weights`, and `gz` booleans.
- `LHE*` dataclasses are now slotted, meaning no `__dict__` is created, dict-style compatibility is gone, and undefined attributes can no longer be added dynamically.
- Weights and weightgroups are now no longer stored in `LHEInit.weightgroup` but in `LHEHeader.initrwgt.entries`. They are thus part of the `<header>` instead of `<init>` as demanded by LHE specification.
- `LHEInit` no longer has `LHEVersion`. Instead, the version is stored in `LesHouchesEvents.version`.
- LHE data block formats can now be modified as part of `LHEOutputFormat`.
- `tofile()` now accepts path-like objects. Compression and file-format autodetection only use the filename suffix when no explicit output format is provided.

### Removed

- Circular references `LHEParticle.event` and `LHEParticle._event` are removed.
- `LHEParticle.mothers()` is removed in favour of `LHEEvent.mothers(particle)`.
- The following old deprecated functions were removed: `read_lhe_file`, `read_lhe_init`, `read_lhe`, `read_lhe_with_attributes`, `read_num_events`, `write_lhe_file_string`, `write_lhe_string`, `write_lhe_file_path`, `write_lhe_file`.
- `DictCompatibility` is removed and thereby also `fieldnames`.
- `LHEWeightGroup` and `LHEWeightInfo` are removed.
- Support for Python 3.9.

### Fixed

- Round-tripping now preserves the root LHE version, event attributes, and `#` comment lines.
- Event graphs now connect mother particles correctly and no longer embed full particle/event representations in node attributes.
- Parsing now raises a clearer `ValueError` when an event `<weights>` block has more entries than declared in `<initrwgt>`.

## [1.0.4] - 2026-05-15

## [1.0.3] - 2026-05-15

### Changed

- Raise an error when weight format is requested to be both `rwgt` and `weights` simultaneously.

[unreleased]: https://github.com/scikit-hep/pylhe/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/scikit-hep/pylhe/compare/v1.0.4...v2.0.0
[1.0.4]: https://github.com/scikit-hep/pylhe/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/scikit-hep/pylhe/compare/v1.0.2...v1.0.3
