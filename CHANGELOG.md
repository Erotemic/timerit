# Changelog

We are currently working on porting this changelog to the specifications in
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Version 1.0.0] - Unreleased

### Changed
* Documentation improvements
* Better type stubs


## [Version 1.0.0] - Released 2022-04-18

### Added
* `robust_times` method
* `summary` method
* relative module

### Changed
* Removed Python 2.7, 3.4 and 3.5 support
* Python 3.7+ now uses `perf_counter_ns` by default if available


## [Version 0.3.0] - Released 2019-12-29

### Added
* Add rankings and consistency properties
* Timerit now remembers results from previous runs


## [Version 0.2.1] - Released 2019-03-03


## [Version 0.1.1]

### Added
* added `Timerit.reset`
* Timer and Timerit now have class-level default objects and instance specific
  instances which can be overwritten for tests / custom purposes. 
* Tweaked precision formatting in reports


## [Version 0.1.0] - Released 2018-07-06

### Added
* added `Timerit.reset`


## [Version 0.0.2] 

### Added
* Added unit keyword arg to Timerit. This forces a Timerit objects to report
  time per loop in a particular unit. The default of None chooses a unit.
* The timer returned by Timerit.__iter__ now contains an attribute 
  called `parent` that references the original timer object.
* Renamed global private attribute `default_timer` to `default_time`
* Timer now uses a `self._time` instead of globally calling `default_time`.
  This is mainly to make testing easier.
* Timerit now uses `self._timer_cls` instead of `Timer` for internal timers,
  again mainly for testing reasons.
* Add internals to force ascii chars for tests


## [Version 0.0.1] - Released 2018-05-27 

### Added
* Initial port from ubelt
