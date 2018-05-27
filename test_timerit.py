# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from xdoctest.utils import CaptureStdout
from timerit import Timer, Timerit


def test_timer_nonewline():
    with CaptureStdout() as cap:
        timer = Timer(newline=False, verbose=1)
        timer.tic()
        timer.toc()
    assert cap.text.replace('u', '').startswith("\ntic('')...toc('')")


def test_timerit_verbose():
    with CaptureStdout() as cap:
        Timerit(3, label='foo', verbose=0).call(lambda: None)
    assert cap.text == ''

    with CaptureStdout() as cap:
        Timerit(3, label='foo', verbose=1).call(lambda: None)
    assert cap.text.count('\n') == 2
    assert cap.text.count('foo') == 1

    with CaptureStdout() as cap:
        Timerit(3, label='foo', verbose=2).call(lambda: None)
    assert cap.text.count('\n') == 3
    assert cap.text.count('foo') == 2

    with CaptureStdout() as cap:
        Timerit(3, label='foo', verbose=3).call(lambda: None)
    assert cap.text.count('\n') == 4
    assert cap.text.count('foo') == 2

    with CaptureStdout() as cap:
        Timerit(3, label='foo', verbose=4).call(lambda: None)
    assert cap.text.count('\n') == 4
    assert cap.text.count('foo') == 2


def test_timer_default_verbosity():

    with CaptureStdout() as cap:
        Timer('').tic().toc()
    assert cap.text == '', 'should be quiet by default when label is not given'

    with CaptureStdout() as cap:
        Timer('a label').tic().toc()
    assert cap.text != '', 'should be verbose by default when label is given'


def test_timerit_default_verbosity():
    with CaptureStdout() as cap:
        Timerit(10, '').call(lambda: None)
    assert cap.text == '', 'should be quiet by default when label is not given'

    with CaptureStdout() as cap:
        Timerit(10, 'alabel').call(lambda: None)
    assert cap.text != '', 'should be verbose by default when label is given'


def test_timer_error():
    try:
        with Timer() as timer:
            raise Exception()
    except Exception as ex:
        pass
    assert timer.elapsed > 0


def test_verbose_report():
    t = Timerit(10, 'alabel').call(lambda: None)
    t.report()

if __name__ == '__main__':
    r"""
    CommandLine:
        python ubelt/tests/test_time.py test_timer_nonewline
    """
    import xdoctest
    xdoctest.doctest_module(__file__)
