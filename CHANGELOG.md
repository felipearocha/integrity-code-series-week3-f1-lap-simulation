# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- chore(meta): add CI matrix, Dependabot, and Integrity Code Series cross-links

### CI
- ci: drop Python 3.10 from matrix (modern scipy/numpy require >=3.11)
- ci: test failures now fail the job; bump checkout and setup-python to v7
- ci: Dependabot no longer raises floors in requirements.txt; action updates are grouped

### Fixed
- Traction ceiling uses weight plus downforce, not four times downforce
- Track closes: one net revolution and zero end gap (was 76.5 rad and 66.8 m)
- Corner widths and amplitudes are independent draws
- test_energy_conservation checks the SOC balance
- test_lap_time_physical floor comes from the power-limited top speed (38.0 s), not an unsourced 55 s

### Changed
- Default lap is now 51.94 s (was 56.32 s)
- "Six coupled ODEs" replaced: slip angle is algebraic, fuel is not fed back
- Grip window, lateral limit and fuel limitations stated in the README

### Added
- CITATION.cff
- .gitignore; tracked bytecode removed

### Removed
- ruff code-style badge (no ruff config or check exists in this repository)

## [0.0.1] - 2026-03-03

### Added
- Add files via upload

### Other
- Create README.md
- Initial commit

[0.0.1]: https://github.com/felipearocha/integrity-code-series-week3-f1-lap-simulation/releases/tag/v.0.0.1
