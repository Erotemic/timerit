[![Travis](https://img.shields.io/travis/Erotemic/timerit/master.svg?label=Travis%20CI)](https://travis-ci.org/Erotemic/timerit)
[![Codecov](https://codecov.io/github/Erotemic/timerit/badge.svg?branch=master&service=github)](https://codecov.io/github/Erotemic/timerit?branch=master)
[![Appveyor](https://ci.appveyor.com/api/projects/status/github/Erotemic/timerit?svg=True)](https://ci.appveyor.com/project/Erotemic/timerit/branch/master)
[![Pypi](https://img.shields.io/pypi/v/timerit.svg)](https://pypi.python.org/pypi/timerit)


# Timerit

A powerful multiline alternative to Python's builtin `timeit` module.

## Description

Easily do robust timings on existing blocks of code by simply indenting them.
There is no need to refactor into a string representation or convert to a
single line. 

This is the standalone version of a utility currently in [ubelt](https://github.com/Erotemic/ubelt).

## Installation

#### From pypi:
```
pip install timerit
```

#### From github:
```
pip install git+https://github.com/Erotemic/timerit.git
```

## Examples

The quick and dirty way just requires one indent.
```python
>>> import math
>>> from timerit import Timerit
>>> for _ in Timerit(num=200, verbose=2):
>>>     math.factorial(10000)
Timing for 200 loops
Timed for: 200 loops, best of 3
    time per loop: best=2.469 ms, mean=2.49 ± 0.037 ms
```


Use the loop variable as a context manager for more accurate timings or to
incorporate an setup phase that is not timed.  You can also access properties
of the `Timerit` class to programmatically use results.
```python
>>> import math
>>> from timerit import Timerit
>>> t1 = Timerit(num=200, verbose=2)
>>> for timer in t1:
>>>     setup_vars = 10000
>>>     with timer:
>>>         math.factorial(setup_vars)
>>> print('t1.total_time = %r' % (t1.total_time,))
Timing for 200 loops
Timed for: 200 loops, best of 3
    time per loop: best=2.064 ms, mean=2.115 ± 0.05 ms
t1.total_time = 0.4427177629695507
```


There is also a simple one-liner that is comparable to IPython magic:

Compare the timeit version:

```python
>>> %timeit math.factorial(100)
564 ns ± 5.46 ns per loop (mean ± std. dev. of 7 runs, 1000000 loops each)
```

With the Timerit version:

```python
>>> Timerit(100000).call(math.factorial, 100).print()
Timed for: 1 loops, best of 1
    time per loop: best=4.828 µs, mean=4.828 ± 0.0 µs
```
