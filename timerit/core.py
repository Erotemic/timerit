# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import time
import math
import sys
import gc
import itertools as it
from collections import OrderedDict

__all__ = ['Timer', 'Timerit']

if sys.version_info.major == 2:  # nocover
    default_time = time.clock if sys.platform.startswith('win32') else time.time
else:
    # TODO: If sys.version >= 3.7, then use time.perf_counter_ns
    default_time = time.perf_counter


class Timer(object):
    """
    Measures time elapsed between a start and end point. Can be used as a
    with-statement context manager, or using the tic/toc api.

    Args:
        label (str): identifier for printing, defaults to ''
        verbose (int): verbosity flag, defaults to True if label is given
        newline (bool): if False and verbose, print tic and toc on the same
            line, defaults to True

    Attributes:
        elapsed (float): number of seconds measured by the context manager
        tstart (float): time of last `tic` reported by `self._time()`

    CommandLine:
        python -m timerit.core Timer

    Example:
        >>> # Create and start the timer using the context manager
        >>> timer = Timer('Timer test!', verbose=1)
        >>> with timer:
        >>>     math.factorial(10000)
        >>> assert timer.elapsed > 0
        tic('Timer test!')
        ...toc('Timer test!')=...

    Example:
        >>> # Create and start the timer using the tic/toc interface
        >>> timer = Timer().tic()
        >>> elapsed1 = timer.toc()
        >>> elapsed2 = timer.toc()
        >>> elapsed3 = timer.toc()
        >>> assert elapsed1 <= elapsed2
        >>> assert elapsed2 <= elapsed3
    """
    def __init__(self, label='', verbose=None, newline=True):
        if verbose is None:
            verbose = bool(label)
        self.label = label
        self.verbose = verbose
        self.newline = newline
        self.tstart = -1
        self.elapsed = -1
        self.write = sys.stdout.write
        self.flush = sys.stdout.flush
        self._time = default_time

    def tic(self):
        """ starts the timer """
        if self.verbose:
            self.flush()
            self.write('\ntic(%r)' % self.label)
            if self.newline:
                self.write('\n')
            self.flush()
        self.tstart = self._time()
        return self

    def toc(self):
        """ stops the timer """
        elapsed = self._time() - self.tstart
        if self.verbose:
            self.write('...toc(%r)=%.4fs\n' % (self.label, elapsed))
            self.flush()
        return elapsed

    def __enter__(self):
        self.tic()
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.elapsed = self.toc()
        if trace is not None:
            return False


def chunks(seq, size):
    """ simple two-line alternative to `ubelt.chunks` """
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


class Timerit(object):
    """
    Reports the average time to run a block of code.

    Unlike `timeit`, `Timerit` can handle multiline blocks of code

    Args:
        num (int): number of times to run the loop
        label (str): identifier for printing
        bestof (int): takes the max over this number of trials
        verbose (int): verbosity flag, defaults to True if label is given

    CommandLine:
        python -m timerit.core Timerit:0

    Example:
        >>> num = 15
        >>> t1 = Timerit(num, label='factorial', verbose=1)
        >>> for timer in t1:
        >>>     # <write untimed setup code here> this example has no setup
        >>>     with timer:
        >>>         # <write code to time here> for example...
        >>>         math.factorial(10000)
        Timed best=..., mean=... for factorial
        >>> # <you can now access Timerit attributes>
        >>> assert t1.total_time > 0
        >>> assert t1.n_loops == t1.num
        >>> assert t1.n_loops == num

    Example:
        >>> # xdoc: +IGNORE_WANT
        >>> num = 10
        >>> # If the timer object is unused, time will still be recorded,
        >>> # but with less precision.
        >>> for _ in Timerit(num, 'concise', verbose=2):
        >>>     math.factorial(10000)
        Timed concise for: 10 loops, best of 3
            time per loop: best=4.954 ms, mean=4.972 ± 0.018 ms
        >>> # Using the timer object results in the most precise timings
        >>> for timer in Timerit(num, 'precise', verbose=3):
        >>>     with timer: math.factorial(10000)
        Timing precise for: 15 loops, best of 3
        Timed precise for: 15 loops, best of 3
            time per loop: best=2.474 ms, mean=2.54 ± 0.046 ms
    """
    def __init__(self, num=1, label=None, bestof=3, unit=None, verbose=None):
        if verbose is None:
            verbose = bool(label)
        self.num = num
        self.label = label
        self.times = []
        self.verbose = verbose
        self.total_time = None
        self.n_loops = None
        self.bestof = bestof
        self.unit = unit
        self._timer_cls = Timer
        self._precision = 4
        self._asciimode = None

    def call(self, func, *args, **kwargs):
        """
        Alternative way to time a simple function call using condensed syntax.

        Returns:
            self (Timerit): Use `min`, or `mean` to get a scalar. Use `print`
                to output a report to stdout.

        Example:
            >>> time = Timerit(num=10).call(math.factorial, 50).min()
            >>> assert time > 0
        """
        for timer in self:
            with timer:
                func(*args, **kwargs)
        return self

    def __iter__(self):
        if self.verbose >= 3:
            print(self._status_line(tense='present'))

        self.n_loops = 0
        self.total_time = 0
        # Create a foreground and background timer
        bg_timer = self._timer_cls(verbose=0)   # (ideally this is unused)
        fg_timer = self._timer_cls(verbose=0)   # (used directly by user)
        # give the forground timer a reference to this object, so the user can
        # access this object while still constructing the timerit object inline
        # with the for loop.
        fg_timer.parent = self
        # disable the garbage collector while timing
        with ToggleGC(False):
            # Core timing loop
            for i in it.repeat(None, self.num):
                # Start background timer (in case the user doesn't use fg_timer)
                # Yield foreground timer to let the user run a block of code
                # When we return from yield the user code will have just finished
                # Then record background time + loop overhead
                bg_timer.tic()
                yield fg_timer
                bg_time = bg_timer.toc()
                # Check if the fg_timer object was used, but fallback on bg_timer
                if fg_timer.elapsed >= 0:
                    block_time = fg_timer.elapsed  # higher precision
                else:
                    block_time = bg_time  # low precision
                # record timings
                self.times.append(block_time)
                self.total_time += block_time
                self.n_loops += 1
        # Timing complete, print results
        assert len(self.times) == self.num, 'incorrectly recorded times'
        if self.verbose > 0:
            self.print(self.verbose)

    def min(self):
        """
        The best time overall.

        This is typically the best metric to consider when evaluating the
        execution time of a function. To understand why consider this quote
        from the docs of the original timeit module:

        '''
        In a typical case, the lowest value gives a lower bound for how fast
        your machine can run the given code snippet; higher values in the
        result vector are typically not caused by variability in Python's
        speed, but by other processes interfering with your timing accuracy.
        So the min() of the result is probably the only number you should be
        interested in.
        '''

        Returns:
            float: minimum measured seconds over all trials

        Example:
            >>> self = Timerit(num=10, verbose=0)
            >>> self.call(math.factorial, 50)
            >>> assert self.min() > 0
        """
        return min(self.times)

    def mean(self):
        """
        The mean of the best results of each trial.

        Returns:
            float: mean of measured seconds

        Note:
            This is typically less informative than simply looking at the min.
            It is recommended to use min as the expectation value rather than
            mean in most cases.

        Example:
            >>> self = Timerit(num=10, verbose=0)
            >>> self.call(math.factorial, 50)
            >>> assert self.mean() > 0
        """
        chunk_iter = chunks(self.times, self.bestof)
        times = list(map(min, chunk_iter))
        mean = sum(times) / len(times)
        return mean

    def std(self):
        """
        The standard deviation of the best results of each trial.

        Returns:
            float: standard deviation of measured seconds

        Note:
            As mentioned in the timeit source code, the standard deviation is
            not often useful. Typically the minimum value is most informative.

        Example:
            >>> self = Timerit(num=10, verbose=1)
            >>> self.call(math.factorial, 50)
            >>> assert self.std() >= 0
        """
        chunk_iter = chunks(self.times, self.bestof)
        times = list(map(min, chunk_iter))
        mean = sum(times) / len(times)
        std = math.sqrt(sum((t - mean) ** 2 for t in times) / len(times))
        return std

    def _seconds_str(self):
        """
        Returns:
            str: human readable text

        Example:
            >>> self = Timerit(num=100, bestof=10, verbose=0)
            >>> self.call(lambda : sum(range(100)))
            >>> print(self._seconds_str())
            ... 'best=3.423 µs, ave=3.451 ± 0.027 µs'
        """
        mean = self.mean()
        unit, mag = _choose_unit(mean, self.unit, self._asciimode)

        unit_min = self.min() / mag
        unit_mean = mean / mag

        # Is showing the std useful? It probably doesn't hurt.
        std = self.std()
        unit_std = std / mag
        pm = _trychar('±', '+-', self._asciimode)
        fmtstr = ('best={min:.{pr1}} {unit}, '
                  'mean={mean:.{pr1}} {pm} {std:.{pr2}} {unit}')
        pr1 = self._precision
        pr2 = max(self._precision - 2, 1)
        unit_str = fmtstr.format(min=unit_min, unit=unit, mean=unit_mean,
                                 pm=pm, std=unit_std, pr1=pr1, pr2=pr2)
        return unit_str

    def _status_line(self, tense='past'):
        """
        Text indicating what has been / is being done.

        Doctest:
            >>> print(Timerit()._status_line(tense='past'))
            Timed for: 1 loops, best of 1
            >>> print(Timerit()._status_line(tense='present'))
            Timing for: 1 loops, best of 1
        """
        action = {'past': 'Timed',  'present': 'Timing'}[tense]
        line = '{action} {label}for: {num:d} loops, best of {bestof:d}'.format(
            label=self.label + ' ' if self.label else '',
            action=action, num=self.num, bestof=min(self.bestof, self.num))
        return line

    def report(self, verbose=1):
        """
        Creates a human readable report

        Args:
            verbose (int): verbosity level. Either 1, 2, or 3.

        Returns:
            str: the report

        SeeAlso:
            Timerit.print

        Example:
            >>> ti = Timerit(num=1).call(math.factorial, 5)
            >>> print(ti.report(verbose=1))
            Timed best=...s, mean=...s
        """
        lines = []
        if verbose >= 2:
            # use a multi-line format for high verbosity
            lines.append(self._status_line(tense='past'))
            if verbose >= 3:
                unit, mag = _choose_unit(self.total_time, self.unit,
                                         self._asciimode)
                lines.append('    body took: {total:.{pr}} {unit}'.format(
                    total=self.total_time / mag,
                    pr=self._precision, unit=unit))
            lines.append('    time per loop: {}'.format(self._seconds_str()))
        else:
            # use a single-line format for low verbosity
            line = 'Timed ' + self._seconds_str()
            if self.label:
                line += ' for ' + self.label
            lines.append(line)
        text = '\n'.join(lines)
        return text

    def print(self, verbose=1):
        """
        Prints human readable report using the print function

        Args:
            verbose (int): verbosity level

        SeeAlso:
            Timerit.report

        Example:
            >>> Timerit(num=10).call(math.factorial, 50).print(verbose=1)
            Timed best=...s, mean=...s
            >>> Timerit(num=10).call(math.factorial, 50).print(verbose=2)
            Timed for: 10 loops, best of 3
                time per loop: best=...s, mean=...s
            >>> Timerit(num=10).call(math.factorial, 50).print(verbose=3)
            Timed for: 10 loops, best of 3
                body took: ...
                time per loop: best=...s, mean=...s
        """
        print(self.report(verbose=verbose))


class ToggleGC(object):
    """
    Context manager to disable garbage collection.

    Example:
        >>> import gc
        >>> prev = gc.isenabled()
        >>> with ToggleGC(False):
        >>>     assert not gc.isenabled()
        >>>     with ToggleGC(True):
        >>>         assert gc.isenabled()
        >>>     assert not gc.isenabled()
        >>> assert gc.isenabled() == prev
    """
    def __init__(self, flag):
        self.flag = flag
        self.prev = None

    def __enter__(self):
        self.prev = gc.isenabled()
        if self.flag:
            gc.enable()
        else:
            gc.disable()

    def __exit__(self, ex_type, ex_value, trace):
        if self.prev:
            gc.enable()
        else:
            gc.disable()


def _choose_unit(value, unit=None, asciimode=None):
    """
    Finds a good unit to print seconds in

    Args:
        value (float): measured value in seconds
        unit (str): if specified, overrides heuristic decision
        asciimode (bool): if True, forces ascii for microseconds

    Returns:
        tuple[(str, float)]: suffix, mag:
            string suffix and conversion factor

    Example:
        >>> assert _choose_unit(1.1, unit=None)[0] == 's'
        >>> assert _choose_unit(1e-2, unit=None)[0] == 'ms'
        >>> assert _choose_unit(1e-4, unit=None, asciimode=True)[0] == 'us'
        >>> assert _choose_unit(1.1, unit='ns')[0] == 'ns'
    """
    micro = _trychar('µs', 'us', asciimode)
    units = OrderedDict([
        ('s', ('s', 1e0)),
        ('ms', ('ms', 1e-3)),
        ('us', (micro, 1e-6)),
        ('ns', ('ns', 1e-9)),
    ])
    if unit is None:
        for suffix, mag in units.values():  # pragma: nobranch
            if value > mag:
                break
    else:
        suffix, mag = units[unit]
    return suffix, mag


def _trychar(char, fallback, asciimode=None):  # nocover
    """
    Logic from IPython timeit to handle terminals that cant show mu

    Args:
        char (str): character, typically unicode, to try to use
        fallback (str): ascii character to use if stdout cannot encode char
        asciimode (bool): if True, always use fallback

    Example:
        >>> char = _trychar('µs', 'us')
        >>> print('char = {}'.format(char))
        >>> assert _trychar('µs', 'us', asciimode=True) == 'us'

    """
    if asciimode is True:
        # If we request ascii mode simply return it
        return fallback
    if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:  # pragma: nobranch
        try:
            char.encode(sys.stdout.encoding)
        except Exception:  # nocover
            pass
        else:
            return char
    return fallback  # nocover


if __name__ == '__main__':
    """
    CommandLine:
        python -m timerit.core all
    """
    import xdoctest as xdoc
    xdoc.doctest_module(__file__)
