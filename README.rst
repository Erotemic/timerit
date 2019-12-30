|CircleCI| |Travis| |Appveyor| |Codecov| |Pypi| |Downloads| |ReadTheDocs| |CodeQuality|

Timerit
=======

A powerful multiline alternative to Python's builtin ``timeit`` module.

Docs are being written at https://timerit.readthedocs.io/en/latest/

Description
-----------

Easily do robust timings on existing blocks of code by simply indenting
them. There is no need to refactor into a string representation or
convert to a single line.

This is a standalone version of a utility distributed with 
`ubelt <https://github.com/Erotemic/ubelt>`__.

Installation
------------

From pypi:
^^^^^^^^^^

::

    pip install timerit

From github:
^^^^^^^^^^^^

::

    pip install git+https://github.com/Erotemic/timerit.git

Examples
--------

The quick and dirty way just requires one indent.

.. code:: python

    >>> import math
    >>> from timerit import Timerit
    >>> for _ in Timerit(num=200, verbose=2):
    >>>     math.factorial(10000)
    Timing for 200 loops
    Timed for: 200 loops, best of 3
        time per loop: best=2.469 ms, mean=2.49 ± 0.037 ms

Use the loop variable as a context manager for more accurate timings or
to incorporate an setup phase that is not timed. You can also access
properties of the ``Timerit`` class to programmatically use results.

.. code:: python

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

There is also a simple one-liner that is comparable to IPython magic:

Compare the timeit version:

.. code:: python

    >>> %timeit math.factorial(100)
    564 ns ± 5.46 ns per loop (mean ± std. dev. of 7 runs, 1000000 loops each)

With the Timerit version:

.. code:: python

    >>> Timerit(100000).call(math.factorial, 100).print()
    Timed for: 1 loops, best of 1
        time per loop: best=4.828 µs, mean=4.828 ± 0.0 µs

.. |Travis| image:: https://img.shields.io/travis/Erotemic/timerit/master.svg?label=Travis%20CI
   :target: https://travis-ci.org/Erotemic/timerit?branch=master
.. |Codecov| image:: https://codecov.io/github/Erotemic/timerit/badge.svg?branch=master&service=github
   :target: https://codecov.io/github/Erotemic/timerit?branch=master
.. |Appveyor| image:: https://ci.appveyor.com/api/projects/status/github/Erotemic/timerit?branch=master&svg=True
   :target: https://ci.appveyor.com/project/Erotemic/timerit/branch/master
.. |Pypi| image:: https://img.shields.io/pypi/v/timerit.svg
   :target: https://pypi.python.org/pypi/timerit
.. |Downloads| image:: https://img.shields.io/pypi/dm/timerit.svg
   :target: https://pypistats.org/packages/timerit
.. |CircleCI| image:: https://circleci.com/gh/Erotemic/timerit.svg?style=svg
    :target: https://circleci.com/gh/Erotemic/timerit
.. |ReadTheDocs| image:: https://readthedocs.org/projects/timerit/badge/?version=latest
    :target: http://timerit.readthedocs.io/en/latest/
.. |CodeQuality| image:: https://api.codacy.com/project/badge/Grade/fdcedca723f24ec4be9c7067d91cb43b 
    :target: https://www.codacy.com/manual/Erotemic/timerit?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Erotemic/timerit&amp;utm_campaign=Badge_Grade
