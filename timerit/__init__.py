"""
Timerit is a powerful multiline alternative to Python's builtin ``timeit`` module.

Easily do robust timings on existing blocks of code by simply indenting
them. There is no need to refactor into a string representation or
convert to a single line.

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
    >>> # xdoctest: +IGNORE_WANT
    >>> print('t1.total_time = %r' % (t1.total_time,))
    Timing for 200 loops
    Timed for: 200 loops, best of 3
        time per loop: best=2.064 ms, mean=2.115 +- 0.05 ms
    t1.total_time = 0.4427177629695507
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

__version__ = '1.2.0'

import sys
from .core import (Timer, Timerit,)

__all__ = ['Timer', 'Timerit']


# The following code follows [SO1060796]_ to enrich a module with `__call__()`
# and `__iter__()` methods. Type checking is ignored on the dynamic module
# base class because static analyzers cannot model this module-class swap.
#
# References:
#     .. [SO1060796] https://stackoverflow.com/questions/1060796/callable-modules


class TimeritModule(sys.modules[__name__].__class__):  # type: ignore

    def __iter__(self) -> Iterator[Timer]:
        """
        Yields:
            Timer
        """
        yield from self()

    def __call__(self, *args: Any, **kwargs: Any) -> Timerit:
        """
        Module-level call to create a Timerit instance with interactive defaults.

        Args:
            *args : passed to :class:`timerit.Timerit`
            **kwargs : passed to :class:`timerit.Timerit`

        Returns:
            Timerit

        Example:
            >>> import math
            >>> import timerit
            >>> for _ in timerit:
            >>>     math.factorial(100)
        """
        from inspect import signature
        sig = signature(Timerit).bind(*args, **kwargs)
        call_kwargs: dict[str, Any] = {
            'num': None,
            'verbose': 2,
            'bestof': 5,
        }
        call_kwargs.update(sig.arguments)
        return Timerit(**call_kwargs)

sys.modules[__name__].__class__ = TimeritModule
del sys, TimeritModule
