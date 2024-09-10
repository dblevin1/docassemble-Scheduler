# Changelog

<!-- insertion marker -->
## [0.2.1](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/0.2.1) - 2024-09-09

<small>[Compare with 0.2.0](https://github.com/dblevin1/docassemble-Scheduler/compare/0.2.0...0.2.1)</small>

### Fixed

- fix setting request context to False, causing non-scheduler log messages to not include user uid or interview name ([3054eac](https://github.com/dblevin1/docassemble-Scheduler/commit/3054eac4060c4a0ca320a3d8bf0dab3f53d18eff) by Daniel Blevins).

## [0.2.0](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/0.2.0) - 2024-08-15

<small>[Compare with 0.1.15](https://github.com/dblevin1/docassemble-Scheduler/compare/0.1.15...0.2.0)</small>

### Changed

- change to uwsgi signal based system ([72573f7](https://github.com/dblevin1/docassemble-Scheduler/commit/72573f763f8a2bcddb9e75966a79b1d6fcf6c79f) by Daniel Blevins).

## [0.1.15](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/0.1.15) - 2024-07-26

<small>[Compare with 0.1.14](https://github.com/dblevin1/docassemble-Scheduler/compare/0.1.14...0.1.15)</small>

### Added

- add job name to logger ([dab6f74](https://github.com/dblevin1/docassemble-Scheduler/commit/dab6f7402188876267a1ce26f4cdd8513f082e6a) by Daniel Blevins).

### Removed

- remove hardcoded db_host ([9a6514c](https://github.com/dblevin1/docassemble-Scheduler/commit/9a6514c45f1de181be089632c7d7aabcfe2d02e6) by Daniel Blevins).

## [0.1.14](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/0.1.14) - 2024-04-01

<small>[Compare with V0.1.13](https://github.com/dblevin1/docassemble-Scheduler/compare/V0.1.13...0.1.14)</small>

### Fixed

- fix error log message on setup ([80936ef](https://github.com/dblevin1/docassemble-Scheduler/commit/80936ef3b85e504714070d27a8943f91c1b214c4) by Daniel Blevins).

## [V0.1.13](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/V0.1.13) - 2024-04-01

<small>[Compare with V0.1.12](https://github.com/dblevin1/docassemble-Scheduler/compare/V0.1.12...V0.1.13)</small>

### Fixed

- fix incorrect logging lvl check ([867cd36](https://github.com/dblevin1/docassemble-Scheduler/commit/867cd36d05fac5d4028f895e0eabd49dfcca6d97) by Daniel Blevins).

## [V0.1.12](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/V0.1.12) - 2024-02-27

<small>[Compare with V0.1.11](https://github.com/dblevin1/docassemble-Scheduler/compare/V0.1.11...V0.1.12)</small>

### Fixed

- fix logger not using level before being setup ([eb7b65a](https://github.com/dblevin1/docassemble-Scheduler/commit/eb7b65ae32b7e21ca3e75de83075635ce71de244) by Daniel Blevins).

### Changed

- change setup checks to prioritize in_cron and in_celery ([d8dcce1](https://github.com/dblevin1/docassemble-Scheduler/commit/d8dcce102a6dfc5481e61ee286a65d4f04d026db) by Daniel Blevins).

## [V0.1.11](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/V0.1.11) - 2023-11-30

<small>[Compare with V0.1.10](https://github.com/dblevin1/docassemble-Scheduler/compare/V0.1.10...V0.1.11)</small>

### Added

- add better detection if started by a docassemble server ([b2d4eab](https://github.com/dblevin1/docassemble-Scheduler/commit/b2d4eab12a80545a08c81e7cb6176c604910db85) by Daniel Blevins).
- add better install and configuration instructions ([309c8b4](https://github.com/dblevin1/docassemble-Scheduler/commit/309c8b4067adda133d863a20378c35877b956aeb) by Daniel Blevins).

## [V0.1.10](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/V0.1.10) - 2023-05-23

<small>[Compare with V0.1.9](https://github.com/dblevin1/docassemble-Scheduler/compare/V0.1.9...V0.1.10)</small>

### Added

- add do not preload to the test SchedulerContext class ([cb706b6](https://github.com/dblevin1/docassemble-Scheduler/commit/cb706b62a1a64eb229dbd093685c51f77afdf975) by Daniel Blevins).

### Fixed

- fixed scheduler being started in cron and celery ([8f8941c](https://github.com/dblevin1/docassemble-Scheduler/commit/8f8941c553eb62a631ecb32100a83315f222f24d) by Daniel Blevins).

## [V0.1.9](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/V0.1.9) - 2023-05-19

<small>[Compare with V0.1.8](https://github.com/dblevin1/docassemble-Scheduler/compare/V0.1.8...V0.1.9)</small>

### Fixed

- fix undefined table error on first run using the sql jobstore ([f78f426](https://github.com/dblevin1/docassemble-Scheduler/commit/f78f426c65caaa55836aabe41de7782fa7500bdf) by Daniel Blevins).

## [V0.1.8](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/V0.1.8) - 2023-05-17

<small>[Compare with V0.1.7](https://github.com/dblevin1/docassemble-Scheduler/compare/V0.1.7...V0.1.8)</small>

## [V0.1.7](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/V0.1.7) - 2023-05-17

<small>[Compare with V0.1.6](https://github.com/dblevin1/docassemble-Scheduler/compare/V0.1.6...V0.1.7)</small>

### Changed

- change postgre_db_backup tar function to not use gzip ([7952185](https://github.com/dblevin1/docassemble-Scheduler/commit/7952185b339bb02ea41cc17d499896445b120ce7) by Daniel Blevins).

## [V0.1.6](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/V0.1.6) - 2023-05-14

<small>[Compare with V0.1.5](https://github.com/dblevin1/docassemble-Scheduler/compare/V0.1.5...V0.1.6)</small>

### Added

- added jobstore with configuration value and event missed listener logger ([8ad5cd1](https://github.com/dblevin1/docassemble-Scheduler/commit/8ad5cd1add8c3bcb59800371768b758aa76a1aed) by Daniel Blevins).

### Changed

- changed apscheduler required version to 3.10.1 ([64a6a38](https://github.com/dblevin1/docassemble-Scheduler/commit/64a6a3893c3c42874d58622e62887c872b166919) by Daniel Blevins).

### Removed

- remove unused code that was setting up the logger erroneously ([9f5f9c0](https://github.com/dblevin1/docassemble-Scheduler/commit/9f5f9c05c39c916f0373cf79a7240fca70119bc6) by Daniel Blevins).

## [V0.1.5](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/V0.1.5) - 2023-05-14

<small>[Compare with V0.1.4](https://github.com/dblevin1/docassemble-Scheduler/compare/V0.1.4...V0.1.5)</small>

### Fixed

- fix tempfile dir cleanup ([c78853d](https://github.com/dblevin1/docassemble-Scheduler/commit/c78853dae2c4d34b5205659b538a5793b5e41ef5) by Daniel Blevins).
- fix pargs ([c77d6cd](https://github.com/dblevin1/docassemble-Scheduler/commit/c77d6cd3e7d00dc99a9aaa7e276379fabc350950) by Daniel Blevins).

## [V0.1.4](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/V0.1.4) - 2023-05-13

<small>[Compare with V0.1.3](https://github.com/dblevin1/docassemble-Scheduler/compare/V0.1.3...V0.1.4)</small>

### Added

- add same function calling ([1ea4fae](https://github.com/dblevin1/docassemble-Scheduler/commit/1ea4faebc572df7edd105efc0ba30b2ab830f57c) by Daniel Blevins).

### Removed

- remove unused function ([c719050](https://github.com/dblevin1/docassemble-Scheduler/commit/c719050a35e700825ae7b1c75792290878de150a) by Daniel Blevins).

## [V0.1.3](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/V0.1.3) - 2023-05-13

<small>[Compare with V0.1.2](https://github.com/dblevin1/docassemble-Scheduler/compare/V0.1.2...V0.1.3)</small>

### Removed

- remove zip backups, fix tar backups ([03a0dbd](https://github.com/dblevin1/docassemble-Scheduler/commit/03a0dbd75650cc9f7fb4747191f54e4c35f83e9d) by Daniel Blevins).

## [V0.1.2](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/V0.1.2) - 2023-05-13

<small>[Compare with V0.1.1](https://github.com/dblevin1/docassemble-Scheduler/compare/V0.1.1...V0.1.2)</small>

## [V0.1.1](https://github.com/dblevin1/docassemble-Scheduler/releases/tag/V0.1.1) - 2023-05-13

<small>[Compare with first commit](https://github.com/dblevin1/docassemble-Scheduler/compare/eba18a912d2de72f2e748d82122b3504e661a2da...V0.1.1)</small>

### Added

- add postgre db backup task ([bf92abb](https://github.com/dblevin1/docassemble-Scheduler/commit/bf92abbe45f7b6b5edebc75992efb94a0a62271a) by Daniel Blevins).
- add custom context ([3be14a0](https://github.com/dblevin1/docassemble-Scheduler/commit/3be14a0a4b8a85ebafda2fa9ad2b735664d17243) by Daniel Blevins).
- add exception message ([3c74411](https://github.com/dblevin1/docassemble-Scheduler/commit/3c74411c01f3b8f372891f1fcd129e2254594f4e) by Daniel Blevins).
- added args, package calling, log levels ([f38ee57](https://github.com/dblevin1/docassemble-Scheduler/commit/f38ee57f1e71857e8912441f003e7aa30025bcf3) by Daniel Blevins).

### Changed

- change log level of job status message ([09bf412](https://github.com/dblevin1/docassemble-Scheduler/commit/09bf4124c853bafe592fd66ca635407410bc49cf) by Daniel Blevins).

### Removed

- remove ubused imports ([67d60a8](https://github.com/dblevin1/docassemble-Scheduler/commit/67d60a8bf8dff7da18e20678b9407c44b3876c75) by Daniel Blevins).
- remove comments ([031078d](https://github.com/dblevin1/docassemble-Scheduler/commit/031078d0201bad9677a1161dec6d36bc9dab3b10) by Daniel Blevins).
