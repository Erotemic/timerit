
|GithubActions| |Appveyor| |Codecov| |Pypi| |Downloads| |ReadTheDocs| 

.. .. |CircleCI| 

Timerit
=======

A powerful multiline alternative to Python's builtin ``timeit`` module.

Docs are published at https://timerit.readthedocs.io/en/latest/ but this README
and code comments contain a walkthrough.

Description
-----------

Easily do robust timings on existing blocks of code by simply indenting
them. There is no need to refactor into a string representation or
convert to a single line.

Installation
------------

::

    pip install timerit


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
to incorporate a setup phase that is not timed. You can also access
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
synax is available. 

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
        ax.set_title('Benchmark')
        ax.set_xlabel('A better x-variable description')
        ax.set_ylabel('A better y-variable description')


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
