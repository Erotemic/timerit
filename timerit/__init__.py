# -*- coding: utf-8 -*-
"""
Timerit is a powerful multiline alternative to Python's builtin ``timeit`` module.

Easily do robust timings on existing blocks of code by simply indenting
them. There is no need to refactor into a string representation or
convert to a single line.

This is a standalone version of a utility distributed with
`ubelt <https://github.com/Erotemic/ubelt>`__.


Timerit makes it easy to benchmark complex blocks of code in either scripted or
interactive sessions (e.g. Jupyter notebooks). The following example only times
a single line, but including more is trivial.

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
        time per loop: best=2.064 ms, mean=2.115 +- 0.05 ms
    t1.total_time = 0.4427177629695507


Mkinit:
    mkinit timerit --nomods --relative
    # TODO: get sphinx to ignore these mkinit-blocks
"""
from __future__ import unicode_literals

__version__ = '0.3.0'

from .core import (Timer, Timerit,)
__all__ = ['Timer', 'Timerit']
