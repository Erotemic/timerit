
|GithubActions| |Appveyor| |Codecov| |Pypi| |Downloads| |ReadTheDocs|


Timerit
=======

A powerful multiline alternative to Python's builtin ``timeit`` module.

Docs are published at https://timerit.readthedocs.io/en/latest/ but this README
and code comments contain a walkthrough.

+---------------+--------------------------------------------+
| Github        | https://github.com/Erotemic/timerit        |
+---------------+--------------------------------------------+
| Pypi          | https://pypi.org/project/timerit           |
+---------------+--------------------------------------------+
| ReadTheDocs   | https://timerit.readthedocs.io/en/latest/  |
+---------------+--------------------------------------------+

Description
-----------

Easily do robust timings on existing blocks of code by simply indenting
them. There is no need to refactor into a string representation or
convert to a single line.

Installation
------------

.. code:: bash

    pip install timerit


Interactive Use
---------------

The ``timerit`` library provides a succinct API for interactive use:

.. code:: python

    >>> import timerit
    >>> for _ in timerit:
    ...     sum(range(100000))
    Timed for: 288 loops, best of 5
        time per loop: best=616.740 µs, mean=668.933 ± 124.2 µs

Compare to ``timeit``:

.. code:: bash

    $ python -m timeit 'sum(range(100000))'
    500 loops, best of 5: 721 usec per loop

By default, any code within the loop will be repeatedly executed until at least
200 ms have elapsed.  The timing results are then printed out.

Here's what each of the numbers means:

- "288 loops": The code in the loop was run 288 times before the time limit was
  reached.

- "best of 5": Consider only the fastest of every 5 measured times, when
  calculating the mean and standard deviation.  The reason for doing this is
  that you can get slow times if the something in the background is consuming
  resources, so you're generally only interested in the fastest times.  This
  idea is also described in the
  `timeit <https://docs.python.org/3/library/timeit.html#timeit.Timer.repeat>`_ docs.

- "best=616.740 µs": How long the fastest iteration took to run.  For the reasons
  described above, this is usually the most consistent number, and the primary
  number you should focus on.

- "mean=668.933 ± 124.2 µs": The mean and the standard deviation of the "best of 5"
  iterations.  This statistic is usually not as robust or useful as the fastest
  time, but sometimes its helpful to know if there's high variance.

The loop variable can be used as a context manager to only time a part of each
loop (e.g. to make the timings more accurate, or to incorporate a setup phase
that is not timed):

.. code:: python

    >>> for timer in timerit:
    ...     n = 100 * 1000
    ...     with timer:
    ...         sum(range(n))
    Timed for: 318 loops, best of 5
        time per loop: best=616.673 µs, mean=617.545 ± 0.9 µs

It is also possible to provide arguments controlling how the timing
measurements are made.  See the online documentation for more information on
these arguments, but the snippet below runs for exactly 100 iterations, instead
of however many fit in 200 ms.

.. code:: python

    >>> for _ in timerit(num=100):
    ...     sum(range(100000))
    Timed for: 100 loops, best of 5
        time per loop: best=616.866 µs, mean=619.120 ± 5.3 µs


Automatic Import
~~~~~~~~~~~~~~~~
If you want to make ``timerit`` even easier to use interactively, you can move
the import to the PYTHONSTARTUP_ file.  If defined, this environment variable
gives the path to a python script that will be executed just before every
interactive session.  For example:

.. code:: bash

    $ export PYTHONSTARTUP=~/.pythonrc
    $ cat $PYTHONSTARTUP
    import timerit
    $ python
    >>> for _ in timerit:
    ...     sum(range(100000))
    ...
    Timed for: 59 loops, best of 3
        time per loop: best=2.532 ms, mean=3.309 ± 1.0 ms


Programmatic Use
----------------

The timerit library also provides a ``Timerit`` class that can be used
programmatically.

.. code:: python

    >>> import math, timerit
    >>> for timer in timerit:
    >>>     setup_vars = 10000
    >>>     with timer:
    >>>         math.factorial(setup_vars)
    >>> print('t1.total_time = %r' % (t1.total_time,))
    Timing for 200 loops
    Timed for: 200 loops, best of 3
        time per loop: best=2.064 ms, mean=2.115 ± 0.05 ms
    t1.total_time = 0.4427177629695507

A common pattern is to create a single ``Timerit`` instance, then to repeatedly
"reset" it with different labels to test a number of different algorithms.  The
labels assigned in this way will be incorporated into the report strings that
the ``Timerit`` instance produces.  The "Benchmark Recipe" below shows an example
of this pattern.  So do all of the scripts in the ``examples/`` directory.

There is also a simple one-liner that is comparable to ``timeit``'s IPython magic:

Compare the timeit version:

.. code:: python

    >>> %timeit math.factorial(100)
    564 ns ± 5.46 ns per loop (mean ± std. dev. of 7 runs, 1000000 loops each)

With the Timerit version:

.. code:: python

    >>> Timerit(100000).call(math.factorial, 100).print()
    Timed for: 1 loops, best of 1
        time per loop: best=4.828 µs, mean=4.828 ± 0.0 µs


How it works
------------

The timerit module defines ``timerit.Timerit``, which is an iterable object
that yields ``timerit.Timer`` context managers.

.. code:: python

    >>> import math
    >>> from timerit import Timerit
    >>> for timer in Timerit(num=200, verbose=2):
    >>>     with timer:
    >>>         math.factorial(10000)

The timer context manager measures how much time the body of it takes by
"tic"-ing on ``__enter__`` and "toc"-ing on ``__exit__``. The parent
``Timerit`` object has access to the context manager, so it is able to read its
measurement. These measurements are stored and then we compute some statistics
on them. Notably the minimum, mean, and standard-deviation of grouped (batched)
running times.

Using the with statement inside the loop is nice because you can run untimed
setup code before you enter the context manager.

In the case where no setup code is required, a more concise version of the
syntax is available.

.. code:: python

    >>> import math
    >>> from timerit import Timerit
    >>> for _ in Timerit(num=200, verbose=2):
    >>>     math.factorial(10000)

If the context manager is never called, the ``Timerit`` object detects this and
the measurement is made in the ``__iter__`` method in the ``Timerit`` object
itself. I believe that this concise method contains slightly more overhead than
the with-statement version. (I have seen evidence that this might actually be
more accurate, but it needs further testing).

Benchmark Recipe
----------------

.. code:: python

    import ubelt as ub
    import pandas as pd
    import timerit

    def method1(x):
        ret = []
        for i in range(x):
            ret.append(i)
        return ret

    def method2(x):
        ret = [i for i in range(x)]
        return ret

    method_lut = locals()  # can populate this some other way

    ti = timerit.Timerit(100, bestof=10, verbose=2)

    basis = {
        'method': ['method1', 'method2'],
        'x': list(range(7)),
        # 'param_name': [param values],
    }
    grid_iter = ub.named_product(basis)

    # For each variation of your experiment, create a row.
    rows = []
    for params in grid_iter:
        key = ub.repr2(params, compact=1, si=1)
        kwargs = params.copy()
        method_key = kwargs.pop('method')
        method = method_lut[method_key]
        # Timerit will run some user-specified number of loops.
        # and compute time stats with similar methodology to timeit
        for timer in ti.reset(key):
            # Put any setup logic you dont want to time here.
            # ...
            with timer:
                # Put the logic you want to time here
                method(**kwargs)
        row = {
            'mean': ti.mean(),
            'min': ti.min(),
            'key': key,
            **params,
        }
        rows.append(row)

    # The rows define a long-form pandas data array.
    # Data in long-form makes it very easy to use seaborn.
    data = pd.DataFrame(rows)
    print(data)

    plot = True
    if plot:
        # import seaborn as sns
        # kwplot autosns works well for IPython and script execution.
        # not sure about notebooks.
        import kwplot
        sns = kwplot.autosns()

        # Your variables may change
        ax = kwplot.figure(fnum=1, doclf=True).gca()
        sns.lineplot(data=data, x='x', y='min', hue='method', marker='o', ax=ax)
        ax.set_title('Benchmark Name')
        ax.set_xlabel('x-variable description')
        ax.set_ylabel('y-variable description')


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
.. |GithubActions| image:: https://github.com/Erotemic/timerit/actions/workflows/tests.yml/badge.svg?branch=main
    :target: https://github.com/Erotemic/timerit/actions?query=branch%3Amain

.. _PYTHONSTARTUP: https://docs.python.org/3/using/cmdline.html?highlight=pythonstartup#envvar-PYTHONSTARTUP

