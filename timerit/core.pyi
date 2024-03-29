from typing import Any
from typing import List
from typing import Dict
from _typeshed import Incomplete

default_counter: str


class Timer:
    label: str
    verbose: int | None
    newline: bool
    write: Incomplete
    flush: Incomplete

    def __init__(self,
                 label: str = '',
                 verbose: int | None = None,
                 newline: bool = True,
                 counter: str = 'auto') -> None:
        ...

    @property
    def tstart(self) -> float:
        ...

    @property
    def elapsed(self) -> float:
        ...

    def tic(self) -> Timer:
        ...

    def toc(self) -> float:
        ...

    def __enter__(self):
        ...

    def __exit__(self, ex_type, ex_value, trace):
        ...


class Timerit:
    measures: dict
    num: int | None
    label: str | None
    bestof: int
    unit: str | None
    verbose: int | None
    min_duration: float
    times: Incomplete
    total_time: int
    n_loops: Incomplete

    def __init__(self,
                 num: int | None = 1,
                 label: str | None = None,
                 bestof: int = 3,
                 unit: str | None = None,
                 verbose: int | None = None,
                 disable_gc: bool = True,
                 timer_cls: None | Any = None,
                 min_duration: float = 0.2) -> None:
        ...

    def reset(self,
              label: str | None = None,
              measures: bool = False) -> Timerit:
        ...

    def call(self, func, *args, **kwargs) -> Timerit:
        ...

    def __iter__(self) -> Timer:
        ...

    def robust_times(self) -> List[float]:
        ...

    @property
    def rankings(self) -> Dict[str, Dict[str, float]]:
        ...

    @property
    def consistency(self) -> float:
        ...

    def min(self) -> float:
        ...

    def mean(self) -> float:
        ...

    def std(self) -> float:
        ...

    def summary(self, stat: str = 'mean') -> str:
        ...

    def report(self, verbose: int = 1) -> str:
        ...

    def print(self, verbose: int = 1) -> None:
        ...


class _SetGCState:
    enable: Incomplete
    prev: Incomplete

    def __init__(self, enable) -> None:
        ...

    def __enter__(self) -> None:
        ...

    def __exit__(self, ex_type, ex_value, trace) -> None:
        ...


class _SetDisplayHook:

    def __enter__(self) -> None:
        ...

    def __exit__(self, ex_type, ex_value, trace) -> None:
        ...
