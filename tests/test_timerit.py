from xdoctest.utils import CaptureStdout
from timerit import Timer, Timerit
from functools import partial
from typing import Any

import gc
import timerit
import random


def _captured_text(cap: CaptureStdout) -> str:
    text = cap.text
    assert text is not None
    return text


def _timer_parent(timer: Timer) -> Timerit:
    parent = timer.parent
    assert parent is not None
    return parent


class HackedTime(object):
    """
    Time object that only ever measures increments and not absolute time

    Args:
        inc (float): number of seconds to ellapse between each call
    """
    def __init__(self, inc=1.0, noise=0, rng=None):
        if rng is None:
            self.rng = random
        else:
            self.rng = random.Random(rng)
        self.time = 1000000000.000
        self.inc = inc
        self.noise = noise
    def __call__(self):
        self.time += abs(self.inc + self.rng.normalvariate(0, self.noise))
        return self.time


class HackedTimer(Timer):
    """ Creates a Timer object where timings are known for testing """
    def __init__(self, *args, **kw):
        inc = kw.pop('inc', 42)
        super(HackedTimer, self).__init__(*args, **kw)
        self._time = HackedTime(inc=inc, rng=593513329100)
        self._to_seconds = 1
        self.inc = inc


class HackedTimerit(Timerit):
    """ Creates a Timerit object where timings are known for testing """
    def __init__(self, *args, **kw):
        inc = kw.pop('inc', 42)
        kw['timer_cls'] = partial(HackedTimer, inc=inc)
        super(HackedTimerit, self).__init__(*args, **kw)
        self.inc = inc
        self._asciimode = True  # a hacked timer will always return ascii


def test_timer_nonewline():
    with CaptureStdout() as cap:
        timer = Timer(newline=False, verbose=1)
        timer.tic()
        timer.toc()
    assert _captured_text(cap).replace('u', '').startswith("\ntic('')...toc('')")


def test_timerit_verbose():
    with CaptureStdout() as cap:
        Timerit(3, label='foo', verbose=0).call(lambda: None)
    assert _captured_text(cap) == ''

    with CaptureStdout() as cap:
        Timerit(3, label='foo', verbose=1).call(lambda: None)
    assert _captured_text(cap).count('\n') == 1
    assert _captured_text(cap).count('foo') == 1

    with CaptureStdout() as cap:
        Timerit(3, label='foo', verbose=2).call(lambda: None)
    assert _captured_text(cap).count('\n') == 2
    assert _captured_text(cap).count('foo') == 1

    with CaptureStdout() as cap:
        Timerit(3, label='foo', verbose=3).call(lambda: None)
    assert _captured_text(cap).count('\n') == 4
    assert _captured_text(cap).count('foo') == 2

    with CaptureStdout() as cap:
        Timerit(3, label='foo', verbose=4).call(lambda: None)
    assert _captured_text(cap).count('\n') == 4
    assert _captured_text(cap).count('foo') == 2


def test_timerit_verbose_via_package():
    timerit_module: Any = timerit

    with CaptureStdout() as cap:
        for _ in timerit_module:
            pass
    assert _captured_text(cap).count('\n') == 2

    with CaptureStdout() as cap:
        timerit_module().call(lambda: None)
    assert _captured_text(cap).count('\n') == 2

    with CaptureStdout() as cap:
        timerit_module(3).call(lambda: None)
    assert _captured_text(cap).count('\n') == 2
    assert _captured_text(cap).count('3 loops, best of 3') == 1

    with CaptureStdout() as cap:
        timerit_module(num=3).call(lambda: None)
    assert _captured_text(cap).count('\n') == 2
    assert _captured_text(cap).count('3 loops, best of 3') == 1

    with CaptureStdout() as cap:
        timerit_module(3, label='foo', verbose=0).call(lambda: None)
    assert _captured_text(cap) == ''

    with CaptureStdout() as cap:
        timerit_module(3, label='foo', verbose=1).call(lambda: None)
    assert _captured_text(cap).count('\n') == 1
    assert _captured_text(cap).count('foo') == 1

    with CaptureStdout() as cap:
        timerit_module(3, label='foo', verbose=2).call(lambda: None)
    assert _captured_text(cap).count('\n') == 2
    assert _captured_text(cap).count('foo') == 1
    assert _captured_text(cap).count('3 loops, best of 3') == 1

    with CaptureStdout() as cap:
        timerit_module(3, label='foo', verbose=3).call(lambda: None)
    assert _captured_text(cap).count('\n') == 4
    assert _captured_text(cap).count('foo') == 2
    assert _captured_text(cap).count('3 loops, best of 3') == 2

    with CaptureStdout() as cap:
        timerit_module(3, label='foo', verbose=4).call(lambda: None)
    assert _captured_text(cap).count('\n') == 4
    assert _captured_text(cap).count('foo') == 2
    assert _captured_text(cap).count('3 loops, best of 3') == 2


def test_hacked_timerit_verbose():
    import textwrap
    with CaptureStdout(suppress=False) as cap:
        HackedTimerit(3, label='foo', verbose=0).call(lambda: None)
    assert _captured_text(cap).strip() == textwrap.dedent(
        '''
        ''').strip()

    with CaptureStdout(suppress=False) as cap:
        HackedTimerit(3, label='foo', verbose=1).call(lambda: None)
    assert _captured_text(cap).strip() == textwrap.dedent(
        '''
        Timed best=42.000 s, mean=42.000 +- 0.0 s for foo
        ''').strip()

    with CaptureStdout(suppress=False) as cap:
        HackedTimerit(3, label='foo', verbose=2).call(lambda: None)
    assert _captured_text(cap).strip() == textwrap.dedent(
        '''
        Timed foo for: 3 loops, best of 3
            time per loop: best=42.000 s, mean=42.000 +- 0.0 s
        ''').strip()

    with CaptureStdout(suppress=False) as cap:
        HackedTimerit(3, label='foo', verbose=3).call(lambda: None)
    assert _captured_text(cap).strip() == textwrap.dedent(
        '''
        Timing foo for: 3 loops, best of 3
        Timed foo for: 3 loops, best of 3
            body took: 126.000 s
            time per loop: best=42.000 s, mean=42.000 +- 0.0 s
        ''').strip()

    with CaptureStdout(suppress=False) as cap:
        HackedTimerit(num=None, label='foo', verbose=0, min_duration=100).call(lambda: None)
    assert _captured_text(cap).strip() == textwrap.dedent(
        '''
        ''').strip()

    with CaptureStdout(suppress=False) as cap:
        HackedTimerit(num=None, label='foo', verbose=1, min_duration=100).call(lambda: None)
    assert _captured_text(cap).strip() == textwrap.dedent(
        '''
        Timed best=42.000 s, mean=42.000 +- 0.0 s for foo
        ''').strip()

    with CaptureStdout(suppress=False) as cap:
        HackedTimerit(num=None, label='foo', verbose=2, min_duration=100).call(lambda: None)
    assert _captured_text(cap).strip() == textwrap.dedent(
        '''
        Timed foo for: 3 loops, best of 3
            time per loop: best=42.000 s, mean=42.000 +- 0.0 s
        ''').strip()

    with CaptureStdout(suppress=False) as cap:
        HackedTimerit(num=None, label='foo', verbose=3, min_duration=100).call(lambda: None)
    assert _captured_text(cap).strip() == textwrap.dedent(
        '''
        Timing foo for: 100.000s
        Timed foo for: 3 loops, best of 3
            body took: 126.000 s
            time per loop: best=42.000 s, mean=42.000 +- 0.0 s
        ''').strip()


def test_timer_default_verbosity():

    with CaptureStdout() as cap:
        Timer('').tic().toc()
    assert _captured_text(cap) == '', 'should be quiet by default when label is not given'

    with CaptureStdout() as cap:
        Timer('a label').tic().toc()
    assert _captured_text(cap) != '', 'should be verbose by default when label is given'


def test_timerit_default_verbosity():
    with CaptureStdout() as cap:
        Timerit(10, '').call(lambda: None)
    assert _captured_text(cap) == '', 'should be quiet by default when label is not given'

    with CaptureStdout() as cap:
        Timerit(10, 'alabel').call(lambda: None)
    assert _captured_text(cap) != '', 'should be verbose by default when label is given'


def test_timer_error():
    try:
        with Timer() as timer:
            raise Exception()
    except Exception:
        pass
    assert timer.elapsed > 0


def test_verbose_report():
    t = Timerit(10, 'alabel').call(lambda: None)
    t.report()


def test_nonstandard_timer():
    timer = HackedTimer()
    with timer:
        pass
    # We know exactly how much time should be measured here
    assert timer.elapsed == timer.inc
    assert timer.toc() == timer.inc * 2
    assert timer.toc() == timer.inc * 3


def test_nonstandard_timerit_precise():
    ti = HackedTimerit()
    for timer in ti:
        with timer:
            pass
    assert ti.mean() == ti.inc
    assert ti.min() == ti.inc
    assert ti.std() == 0


def test_nonstandard_timerit_concise():
    ti = HackedTimerit()
    for timer in ti:
        pass
    assert ti.mean() == ti.inc
    assert ti.min() == ti.inc
    assert ti.std() == 0


def test_timer_context():

    class ManualTime(object):
        """
        Time object that only measures time when you manually tick it
        """
        def __init__(self):
            self.time = 0

        def tic(self, n=1):
            self.time += n

        def __call__(self):
            return self.time

    manual_time = ManualTime()

    class ManualTimer(Timer):
        _default_counter = manual_time

    class ManualTimerit(Timerit):
        _default_timer_cls = ManualTimer
        _default_asciimode = True

    # Test that manual timer works as expected
    t = ManualTimer()
    print('t.elapsed = {!r}'.format(t.elapsed))
    with t:
        pass
    print('t.elapsed = {!r}'.format(t.elapsed))
    assert t.elapsed == 0
    with ManualTimer() as t:
        pass
    print('t.elapsed = {!r}'.format(t.elapsed))
    assert t.elapsed == 0
    with ManualTimer() as t:
        manual_time.tic(n=3)
    assert t.elapsed == 3

    # Test that timerit works without a context manager
    for timer in ManualTimerit(num=100, bestof=10, verbose=2):
        pass
    assert _timer_parent(timer).total_time == 0
    assert _timer_parent(timer).min() == 0

    for timer in ManualTimerit(num=100, bestof=10, verbose=2):
        manual_time.tic()
    assert _timer_parent(timer).total_time == 100
    assert _timer_parent(timer).min() == 1

    for timer in ManualTimerit(num=100, bestof=10, verbose=2):
        manual_time.tic(2)
    assert _timer_parent(timer).total_time == 200
    assert _timer_parent(timer).min() == 2

    # Test that timerit only records time in a context manager when given
    for timer in ManualTimerit(num=100, bestof=10, verbose=2):
        manual_time.tic()
        with timer:
            pass
    assert _timer_parent(timer).total_time == 0
    assert _timer_parent(timer).min() == 0

    for timer in ManualTimerit(num=100, bestof=10, verbose=2):
        manual_time.tic()
        with timer:
            manual_time.tic(2)
    assert _timer_parent(timer).total_time == 200
    assert _timer_parent(timer).min() == 2


def test_timerit_disable_gc_option():
    """The disable_gc constructor option must actually control loop GC state."""
    initial_state = gc.isenabled()
    try:
        gc.enable()
        states = []
        for _ in Timerit(num=1, disable_gc=True, verbose=0):
            states.append(gc.isenabled())
        assert states == [False]
        assert gc.isenabled()

        states = []
        for _ in Timerit(num=1, disable_gc=False, verbose=0):
            states.append(gc.isenabled())
        assert states == [True]
        assert gc.isenabled()
    finally:
        if initial_state:
            gc.enable()
        else:
            gc.disable()


def test_timerit_does_not_reuse_foreground_time():
    """A foreground timing must not leak into later concise iterations."""
    class ManualTime:
        def __init__(self):
            self.time = 0

        def tic(self, n=1):
            self.time += n

        def __call__(self):
            return self.time

    manual_time = ManualTime()

    class ManualTimer(Timer):
        _default_counter = manual_time

    ti = Timerit(num=1, bestof=1, verbose=0, timer_cls=ManualTimer)
    for timer in ti:
        with timer:
            manual_time.tic(2)
    assert ti.times == [2]

    ti.reset()
    for _ in ti:
        manual_time.tic(5)
    assert ti.times == [5]


def test_timerit_mixed_foreground_and_background_iterations():
    """Foreground-use detection is per iteration, not per Timerit object."""
    class ManualTime:
        def __init__(self):
            self.time = 0

        def tic(self, n=1):
            self.time += n

        def __call__(self):
            return self.time

    manual_time = ManualTime()

    class ManualTimer(Timer):
        _default_counter = manual_time

    ti = Timerit(num=2, bestof=1, verbose=0, timer_cls=ManualTimer)
    for index, timer in enumerate(ti):
        if index == 0:
            with timer:
                manual_time.tic(2)
        else:
            manual_time.tic(5)
    assert ti.times == [2, 5]


def test_timerit_summary_honors_stat_argument():
    ti = Timerit(num=1, verbose=0)
    ti.measures = {
        'mean': {'a': 1.0, 'b': 2.0},
        'min': {'a': 4.0, 'b': 2.0},
    }
    mean_summary = ti.summary('mean')
    min_summary = ti.summary('min')
    assert mean_summary != min_summary
    assert 'a is 50.00% faster than b' in mean_summary
    assert 'b is 50.00% faster than a' in min_summary


if __name__ == '__main__':
    r"""
    CommandLine:
        python test_timerit.py test_timer_nonewline
    """
    import xdoctest
    xdoctest.doctest_module(__file__)
