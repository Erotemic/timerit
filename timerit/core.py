"""
First, :class:`Timer` is a context manager that times a block of indented
code. Also has `tic` and `toc` methods for a more matlab like feel.

Next, :class:`Timerit` is an alternative to the builtin timeit module. I think
its better at least, maybe Tim Peters can show me otherwise. Perhaps there's a
reason it has to work on strings and can't be placed around existing code like
a with statement.


Example:
    >>> # xdoc: +IGNORE_WANT
    >>> #
    >>> # The Timerit class allows for robust benchmarking based
    >>> # It can be used in normal scripts by simply adjusting the indentation
    >>> import math
    >>> from timerit import Timerit
    >>> for timer in Timerit(num=12, verbose=3):
    >>>     with timer:
    >>>         math.factorial(100)
    Timing for: 200 loops, best of 3
    Timed for: 200 loops, best of 3
        body took: 331.840 µs
        time per loop: best=1.569 µs, mean=1.615 ± 0.0 µs

    >>> # xdoc: +SKIP
    >>> # In Contrast, timeit is similar, but not having to worry about setup
    >>> # and inputing the program as a string, is nice.
    >>> import timeit
    >>> timeit.timeit(stmt='math.factorial(100)', setup='import math')
    1.12695...


Example:
    >>> # xdoc: +IGNORE_WANT
    >>> #
    >>> # The Timer class can also be useful for quick checks
    >>> #
    >>> import math
    >>> from timerit import Timer
    >>> timer = Timer('Timer demo!', verbose=1)
    >>> x = 100000  # the input for example output
    >>> x = 10      # the input for test speed considerations
    >>> with timer:
    >>>     math.factorial(x)
    tic('Timer demo!')
    ...toc('Timer demo!')=0.1959s
"""
import time
import sys
import itertools as it
from collections import defaultdict, OrderedDict

__all__ = ['Timer', 'Timerit']


# If sys.version >= 3.7, then use time.perf_counter_ns
if sys.version_info[0:2] >= (3, 7):
    if hasattr(time, 'perf_counter_ns'):
        default_counter = 'perf_counter_ns'
    else:
        default_counter = 'perf_counter'
else:
    default_counter = 'perf_counter'


class Timer:
    """
    Measures time elapsed between a start and end point.

    Can be used as a context manager, or using the MATLAB inspired tic/toc API
    [MathWorksTic]_.

    Attributes:

        tstart (float): Timestamp of the last "tic" in seconds.

        elapsed (float): Number of seconds measured at the last "toc".

    References:
        .. [MathWorksTic] https://www.mathworks.com/help/matlab/ref/tic.html

    Example:
        >>> # Create and start the timer using the context manager
        >>> import math
        >>> from timerit import Timer
        >>> timer = Timer('Timer test!', verbose=1)
        >>> with timer:
        >>>     math.factorial(10)
        >>> assert timer.elapsed > 0
        tic('Timer test!')
        ...toc('Timer test!')=...

    Example:
        >>> # Create and start the timer using the tic/toc interface
        >>> import timerit
        >>> timer = timerit.Timer().tic()
        >>> elapsed1 = timer.toc()
        >>> elapsed2 = timer.toc()
        >>> elapsed3 = timer.toc()
        >>> assert elapsed1 <= elapsed2
        >>> assert elapsed2 <= elapsed3

    Example:
        >>> import timerit
        >>> timer1 = timerit.Timer(counter='perf_counter').tic()
        >>> print(timer1.toc())
        >>> print(timer1.toc())
        >>> print(timer1._raw_toc())
        >>> print(timer1._raw_toc())
    """

    _default_counter = default_counter

    def __init__(self, label='', verbose=None, newline=True, counter='auto'):
        """
        Args:
            label (str):
                Identifier for printing. Default is ''.

            verbose (int | None):
                Verbosity level.  If unspecified, defaults to is 1 if label is
                given, otherwise 0.

            newline (bool):
                if False and verbose, print tic and toc on the same line.
                Defaults to True.

            counter (str):
                Can be 'auto', 'perf_counter', or 'perf_counter_ns' (if Python
                3.7+). Defaults to auto.
        """
        if verbose is None:
            verbose = bool(label)
        self.label = label
        self.verbose = verbose
        self.newline = newline
        # self.tstart = -1
        # self.elapsed = -1
        self._raw_elapsed = -1
        self._raw_tstart = -1
        self.write = sys.stdout.write
        self.flush = sys.stdout.flush

        if isinstance(counter, str):
            if counter == 'auto':
                counter = self._default_counter

        if isinstance(counter, str):
            if counter == 'perf_counter_ns':
                _time = time.perf_counter_ns
                _to_seconds = 1e-9
            elif counter == 'perf_counter':
                _time = time.perf_counter
                _to_seconds = 1
            else:
                raise KeyError(counter)
        else:
            _time = counter
            _to_seconds = 1

        self._to_seconds = _to_seconds
        self._time = _time

    @property
    def tstart(self):
        """
        Returns:
            float: The timestamp of the last tic in seconds.
        """
        return self._raw_tstart * self._to_seconds

    @property
    def elapsed(self):
        """
        Returns:
            float: The elapsed time duration in seconds
        """
        return self._raw_elapsed * self._to_seconds

    def _raw_tic(self):
        self._raw_tstart = self._time()

    def _raw_toc(self):
        self._raw_elapsed = raw_elapsed = self._time() - self._raw_tstart
        return raw_elapsed

    def tic(self):
        """
        Starts the timer.

        Returns:
            Timer: self
        """
        if self.verbose:
            self.flush()
            self.write('\ntic(%r)' % self.label)
            if self.newline:
                self.write('\n')
            self.flush()
        self._raw_tic()
        return self

    def toc(self):
        """
        Stops the timer.

        Returns:
            float: Amount of time that passed in seconds since the last tic.
        """
        self._raw_toc()
        elapsed = self.elapsed
        if self.verbose:
            self.write('...toc(%r)=%.4fs\n' % (self.label, elapsed))
            self.flush()
        return elapsed

    def __enter__(self):
        self.tic()
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.toc()
        if trace is not None:
            return False


class Timerit:
    """
    Reports the average time to run a block of code.

    Unlike ``timeit``, :class:`Timerit` can handle multiline blocks of code.
    It runs inline, and doesn't depend on magic or strings. Just indent your
    code and place in a Timerit block.

    Attributes:
        measures - Labeled measurements taken by this object
        rankings - Ranked measurements (useful if more than one measurement was taken)

    Example:
        >>> import math
        >>> import timerit
        >>> num = 3
        >>> t1 = timerit.Timerit(num, label='factorial', verbose=1)
        >>> for timer in t1:
        >>>     # <write untimed setup code here> this example has no setup
        >>>     with timer:
        >>>         # <write code to time here> for example...
        >>>         math.factorial(100)
        Timed best=..., mean=... for factorial
        >>> # <you can now access Timerit attributes>
        >>> assert t1.total_time > 0
        >>> assert t1.n_loops == t1.num
        >>> assert t1.n_loops == num

    Example:
        >>> # xdoc: +IGNORE_WANT
        >>> import math
        >>> import timerit
        >>> num = 10
        >>> # If the timer object is unused, time will still be recorded,
        >>> # but with less precision.
        >>> for _ in timerit.Timerit(num, 'concise', verbose=2):
        >>>     math.factorial(10000)
        Timed concise for: 10 loops, best of 3
            time per loop: best=4.954 ms, mean=4.972 ± 0.018 ms
        >>> # Using the timer object results in the most precise timings
        >>> for timer in timerit.Timerit(num, 'precise', verbose=3):
        >>>     with timer: math.factorial(10000)
        Timing precise for: 15 loops, best of 3
        Timed precise for: 15 loops, best of 3
            time per loop: best=2.474 ms, mean=2.54 ± 0.046 ms
    """

    _default_timer_cls = Timer
    _default_asciimode = None
    _default_precision = 3
    _default_precision_type = 'f'  # could also be reasonably be 'g' or ''

    def __init__(self, num=1, label=None, bestof=3, unit=None, verbose=None,
                 disable_gc=True, timer_cls=None):
        """
        Args:
            num (int):
                Number of times to run the loop. Defaults to 1.

            label (str | None):
                An identifier for printing and differentiating between
                different measurements. Can be changed by calling
                :func:`reset`. Defaults to None

            bestof (int):
                When computing statistics, groups measurements into chunks of
                this size and takes the minimum time within each group. This
                reduces the effective sample size, but improves robustness of
                the mean to noise in the measurements.

            unit (str | None):
                What units time is reported in. Can be 's', 'us', 'ms', or
                'ns'. If unspecified a reasonable value is chosen.

            verbose (int | None):
                Verbosity level. Higher is more verbose, distinct text is
                written at levels 1, 2, and 3. If unspecified, defaults to 1 if
                label is given and 0 otherwise.

            disable_gc (bool):
                If True, disables the garbage collector while timing, defaults to
                True.

            timer_cls (None | Any):
                If specified, replaces the default :class:`Timer` class with a
                customized one. Mainly useful for testing.
        """
        if verbose is None:
            verbose = bool(label)

        self.num = num
        self.label = label
        self.bestof = bestof
        self.unit = unit
        self.verbose = verbose

        self.times = []
        self.total_time = 0

        # self._raw_times = []
        # self._raw_total = None
        self.n_loops = None

        # Keep track of measures, does not change on reset by default
        self.measures = defaultdict(dict)

        # Internal variables
        self._timer_cls = self._default_timer_cls if timer_cls is None else timer_cls
        self._asciimode = self._default_asciimode
        self._precision = self._default_precision
        self._precision_type = self._default_precision_type

        # Create a foreground and background timer
        self._bg_timer = self._timer_cls(verbose=0)   # (ideally this is unused)
        self._fg_timer = self._timer_cls(verbose=0)   # (used directly by user)
        self._to_seconds = self._bg_timer._to_seconds
        # give the foreground timer a reference to this object, so the user can
        # access this object while still constructing the Timerit object inline
        # with the for loop.
        self._fg_timer.parent = self

    def reset(self, label=None, measures=False):
        """
        Clears all measurements, allowing the object to be reused

        Args:
            label (str | None) : Change the label if specified
            measures (bool, default=False): If True reset measures

        Returns:
            Timerit: self

        Example:
            >>> import math
            >>> from timerit import Timerit
            >>> ti = Timerit(num=10, unit='us', verbose=True)
            >>> _ = ti.reset(label='10!').call(math.factorial, 10)
            Timed best=...s, mean=...s for 10!
            >>> _ = ti.reset(label='20!').call(math.factorial, 20)
            Timed best=...s, mean=...s for 20!
            >>> _ = ti.reset().call(math.factorial, 20)
            Timed best=...s, mean=...s for 20!
            >>> _ = ti.reset(measures=True).call(math.factorial, 20)
        """
        if label:
            self.label = label
        if measures:
            self.measures = defaultdict(dict)
        self.times = []
        self.n_loops = None
        self.total_time = None
        return self

    # @property
    # def total_time(self):
    #     if self._raw_total is None:
    #         return None
    #     return self._raw_total / self._to_seconds

    # @property
    # def times(self):
    #     if self._raw_times is None:
    #         return None
    #     return [t * self._to_seconds for t in self._raw_times]

    def call(self, func, *args, **kwargs):
        """
        Alternative way to time a simple function call using condensed syntax.

        Returns:
            'Timerit': self :
                Use `min`, or `mean` to get a scalar. Use `print` to output a
                report to stdout.

        Returns:
            Timerit: self

        Example:
            >>> import math
            >>> from timerit import Timerit
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

        # TODO: if num is unspecified, can we just run for a set amount of time
        # and then stop?

        bg_timer = self._bg_timer
        fg_timer = self._fg_timer
        # disable the garbage collector while timing
        with _SetGCState(enable=False):
            # Core timing loop
            for _ in it.repeat(None, self.num):
                # Start background timer (in case the user doesn't use fg_timer)
                # Yield foreground timer to let the user run a block of code
                # When we return from yield the user code will have just finished
                # Then record background time + loop overhead
                bg_timer.tic()
                yield fg_timer
                bg_time = bg_timer.toc()
                # Check if the fg_timer object was used, but fallback on bg_timer
                if fg_timer.elapsed >= 0:
                    block_time = fg_timer.elapsed  # higher precision?
                else:
                    block_time = bg_time  # lower precision?
                # record timings
                self.times.append(block_time)
                self.total_time += block_time
                self.n_loops += 1
        # Timing complete, print results
        if len(self.times) != self.num:
            raise AssertionError(
                'incorrectly recorded times, need to reset timerit object')

        self._record_measurement()

        if self.verbose > 0:
            self.print(self.verbose)

    def _record_measurement(self):
        """
        Saves the current time measurements for the current labels.
        """
        measures = self.measures
        measures['mean'][self.label] = self.mean()
        measures['min'][self.label] = self.min()
        measures['mean-std'][self.label] = self.mean() - self.std()
        measures['mean+std'][self.label] = self.mean() + self.std()
        return measures

    def robust_times(self):
        """
        Returns a subset of `self.times` where outliers have been rejected.

        Returns:
            List[float]: The measured times reduced by bestof sampling.
        """
        chunk_iter = _chunks(self.times, self.bestof)
        times = list(map(min, chunk_iter))
        return times

    @property
    def rankings(self):
        """
        Orders each list of measurements by ascending time.

        Only useful if the same Timerit object was used to compare multiple
        code blocks using the reset method to give each a different label.

        Returns:
            Dict[str, Dict[str, float]]:
                A mapping from a statistics type to a mapping from label to
                values for that statistic.

        Example:
            >>> import math
            >>> from timerit import Timerit
            >>> ti = Timerit(num=1)
            >>> _ = ti.reset('a').call(math.factorial, 5)
            >>> _ = ti.reset('b').call(math.factorial, 10)
            >>> _ = ti.reset('c').call(math.factorial, 20)
            >>> _ = ti.reset('d').call(math.factorial, 1000)
            >>> _ = ti.reset('e').call(math.factorial, 100000)
            >>> # xdoctest: +REQUIRES(module:ubelt)
            >>> # xdoctest: +IGNORE_WANT
            >>> import ubelt as ub
            >>> print('ti.rankings = {}'.format(ub.repr2(ti.rankings, nl=2, precision=8)))
            >>> print('ti.consistency = {}'.format(ub.repr2(ti.consistency, nl=1, precision=8)))
            >>> print(ti.summary())
            ti.rankings = {
                'mean': {
                    'c': 0.00000055,
                    'b': 0.00000062,
                    'a': 0.00000173,
                    'd': 0.00002542,
                    'e': 0.07673144,
                },
                'mean+std': {
                    'c': 0.00000055,
                    'b': 0.00000062,
                    'a': 0.00000173,
                    'd': 0.00002542,
                    'e': 0.07673144,
                },
                'mean-std': {
                    'c': 0.00000055,
                    'b': 0.00000062,
                    'a': 0.00000173,
                    'd': 0.00002542,
                    'e': 0.07673144,
                },
                'min': {
                    'c': 0.00000055,
                    'b': 0.00000062,
                    'a': 0.00000173,
                    'd': 0.00002542,
                    'e': 0.07673144,
                },
            }
            ti.consistency = 1.00000000
            d is 99.97% faster than e
            a is 93.19% faster than d
            b is 64.05% faster than a
            c is 11.25% faster than b
        """
        rankings = {
            k: OrderedDict(sorted(d.items(), key=lambda kv: kv[1]))
            for k, d in self.measures.items()
        }
        return rankings

    @property
    def consistency(self):
        """"
        Take the hamming distance between the preference profiles to as a
        measure of consistency.

        Returns:
            float: Hamming distance
        """
        rankings = self.rankings

        if len(rankings) == 0:
            raise Exception('no measurements')

        hamming_sum = sum(
            k1 != k2
            for v1, v2 in it.combinations(rankings.values(), 2)
            for k1, k2 in zip(v1.keys(), v2.keys())
        )
        num_labels = len(list(rankings.values())[0])
        num_metrics = len(rankings)
        num_bits = (num_metrics * (num_metrics - 1) // 2) * num_labels
        hamming_ave = hamming_sum / num_bits
        score = 1.0 - hamming_ave
        return score

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
            float: Minimum measured seconds over all trials

        Example:
            >>> import math
            >>> from timerit import Timerit
            >>> self = Timerit(num=10, verbose=0)
            >>> self.call(math.factorial, 50)
            >>> assert self.min() > 0
        """
        return min(self.times)

    def mean(self):
        """
        The mean of the best results of each trial.

        Returns:
            float: Mean of measured seconds

        Note:
            This is typically less informative than simply looking at the min.
            It is recommended to use min as the expectation value rather than
            mean in most cases.

        Example:
            >>> import math
            >>> from timerit import Timerit
            >>> self = Timerit(num=10, verbose=0)
            >>> self.call(math.factorial, 50)
            >>> assert self.mean() > 0
        """
        times = self.robust_times()
        mean = sum(times) / len(times)
        return mean

    def std(self):
        """
        The standard deviation of the best results of each trial.

        Returns:
            float: Standard deviation of measured seconds

        Note:
            As mentioned in the timeit source code, the standard deviation is
            not often useful. Typically the minimum value is most informative.

        Example:
            >>> import math
            >>> from timerit import Timerit
            >>> self = Timerit(num=10, verbose=1)
            >>> self.call(math.factorial, 50)
            >>> assert self.std() >= 0
        """
        import math
        times = self.robust_times()
        mean = sum(times) / len(times)
        std = math.sqrt(sum((t - mean) ** 2 for t in times) / len(times))
        return std

    def _seconds_str(self):
        """
        Returns:
            str: Human readable text

        Example:
            >>> from timerit import Timerit
            >>> self = Timerit(num=100, bestof=10, verbose=0)
            >>> self.call(lambda : sum(range(100)))
            >>> print(self._seconds_str())  # xdoctest: +IGNORE_WANT
            'best=3.423 µs, ave=3.451 ± 0.027 µs'
        """
        mean = self.mean()
        unit, mag = _choose_unit(mean, self.unit, self._asciimode)

        unit_min = self.min() / mag
        unit_mean = mean / mag

        # Is showing the std useful? It probably doesn't hurt.
        std = self.std()
        unit_std = std / mag
        pm = _trychar('±', '+-', self._asciimode)
        fmtstr = ('best={min:.{pr1}{t}} {unit}, '
                  'mean={mean:.{pr1}{t}} {pm} {std:.{pr2}{t}} {unit}')
        pr1 = pr2 = self._precision
        if isinstance(self._precision, int):  # pragma: nobranch
            pr2 = max(self._precision - 2, 1)
        unit_str = fmtstr.format(min=unit_min, unit=unit, mean=unit_mean,
                                 t=self._precision_type, pm=pm, std=unit_std,
                                 pr1=pr1, pr2=pr2)
        return unit_str

    def _status_line(self, tense='past'):
        """
        Text indicating what has been / is being done.

        Args:
            tense (str): Either 'past' or 'present'

        Returns:
            str:

        Example:
            >>> from timerit import Timer
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

    def summary(self, stat='mean'):
        """
        Summarize a timerit session.

        Only useful if multiple measurements are made with different labels
        using the reset method.

        Args:
            stat (str): Can be mean or min.

        Returns:
            str:
                Summary text describing relative change between different
                labeled measurements.

        Example:
            >>> import math
            >>> from timerit import Timerit
            >>> ti = Timerit(num=1)
            >>> x = 32
            >>> ti.reset('mul').call(lambda x: x * x, x)
            >>> ti.reset('pow').call(lambda x: x ** 2, x)
            >>> ti.reset('sum').call(lambda x: sum(x for _ in range(int(x))), x)
            >>> print(ti.summary())  # xdoc: +IGNORE_WANT
            mul is 48.69% faster than sum
            pow is 36.45% faster than mul

        """
        from timerit.relative import Relative
        lines = []
        # TODO: hook up comparisons in an intuitive manner
        method_to_value = self.rankings['mean']
        prev_key = None
        prev_val = None
        for key, val in list(method_to_value.items())[::-1]:
            if prev_key:
                pcnt = Relative.percent_faster(val, prev_val)
                lines.append('{} is {:0.2f}% faster than {}'.format(key, pcnt, prev_key))
            prev_key = key
            prev_val = val
        return '\n'.join(lines)

    def report(self, verbose=1):
        """
        Creates a human readable report

        Args:
            verbose (int): Verbosity level. Either 1, 2, or 3.

        Returns:
            str: The report text summarizing the most recent measurement.

        SeeAlso:
            :func:`Timerit.print`

        Example:
            >>> import math
            >>> from timerit import Timerit
            >>> ti = Timerit(num=1).call(math.factorial, 5)
            >>> print(ti.report(verbose=3))  # xdoctest: +IGNORE_WANT
            Timed for: 1 loops, best of 1
                body took: 1.742 µs
                time per loop: best=1.742 µs, mean=1.742 ± 0.0 µs
        """
        # ti = self
        # print(ti.report())

        lines = []
        if verbose >= 2:
            # use a multi-line format for high verbosity
            lines.append(self._status_line(tense='past'))
            if verbose >= 3:
                unit, mag = _choose_unit(self.total_time, self.unit,
                                         self._asciimode)
                lines.append('    body took: {total:.{pr}{t}} {unit}'.format(
                    total=self.total_time / mag,
                    t=self._precision_type,
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
            verbose (int): Verbosity level

        SeeAlso:
            :func:`Timerit.report`

        Example:
            >>> import math
            >>> from timerit import Timer
            >>> Timerit(num=10).call(math.factorial, 50).print(verbose=1)
            >>> Timerit(num=10).call(math.factorial, 50).print(verbose=2)
            >>> Timerit(num=10).call(math.factorial, 50).print(verbose=3)
            Timed best=...s, mean=...s
            Timed for: 10 loops, best of 3
                time per loop: best=...s, mean=...s
            Timed for: 10 loops, best of 3
                body took: ...
                time per loop: best=...s, mean=...s
        """
        print(self.report(verbose=verbose))


class _SetGCState(object):
    """
    Context manager to disable garbage collection.

    Set the state and then returns to previous state after context exists.

    Args:
        enable (bool): Set the gc to this state.

    Example:
        >>> import gc
        >>> prev = gc.isenabled()
        >>> with _SetGCState(False):
        >>>     assert not gc.isenabled()
        >>>     with _SetGCState(True):
        >>>         assert gc.isenabled()
        >>>     assert not gc.isenabled()
        >>> assert gc.isenabled() == prev
    """
    def __init__(self, enable):
        self.enable = enable
        self.prev = None

    def __enter__(self):
        import gc
        self.prev = gc.isenabled()
        if self.enable:
            gc.enable()
        else:
            gc.disable()

    def __exit__(self, ex_type, ex_value, trace):
        import gc
        if self.prev:
            gc.enable()
        else:
            gc.disable()


def _chunks(seq, size):
    """ simple (lighter?) two-line alternative to :func:`ubelt.chunks` """
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def _choose_unit(value, unit=None, asciimode=None):
    """
    Finds a good unit to print seconds in.

    Args:
        value (float): Measured value in seconds
        unit (str): If specified, overrides heuristic decision
        asciimode (bool): If True, forces ascii for microseconds

    Returns:
        tuple[(str, float)]: suffix, mag:
            string suffix and conversion factor

    Example:
        >>> from timerit.core import _choose_unit
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
    Logic from IPython timeit to handle terminals that can't show mu.

    Args:
        char (str): A character, typically unicode, to try to use
        fallback (str): ASCII character to use if stdout cannot encode char
        asciimode (bool): If True, always use fallback

    Example:
        >>> from timerit.core import _trychar
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
