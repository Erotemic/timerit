from typing import Union
from typing import Any

default_counter: str


class Timer:
    label: Any
    verbose: Any
    newline: Any
    write: Any
    flush: Any

    def __init__(self,
                 label: str = ...,
                 verbose: Any | None = ...,
                 newline: bool = ...,
                 counter: str = ...) -> None:
        ...

    @property
    def tstart(self):
        ...

    @property
    def elapsed(self):
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
    num: Any
    label: Any
    bestof: Any
    unit: Any
    verbose: Any
    times: Any
    total_time: int
    n_loops: Any
    measures: Any

    def __init__(self,
                 num: int = ...,
                 label: Any | None = ...,
                 bestof: int = ...,
                 unit: Any | None = ...,
                 verbose: Any | None = ...,
                 disable_gc: bool = ...,
                 counter: str = ...) -> None:
        ...

    def reset(self,
              label: Union[str, None] = ...,
              measures: bool = ...) -> Timerit:
        ...

    def call(self, func, *args, **kwargs) -> Timerit:
        ...

    def __iter__(self):
        ...

    def robust_times(self):
        ...

    @property
    def rankings(self):
        ...

    @property
    def consistency(self):
        ...

    def min(self) -> float:
        ...

    def mean(self) -> float:
        ...

    def std(self) -> float:
        ...

    def report(self, verbose: int = ...) -> str:
        ...

    def print(self, verbose: int = ...) -> None:
        ...


class _SetGCState:
    enable: Any
    prev: Any

    def __init__(self, enable) -> None:
        ...

    def __enter__(self) -> None:
        ...

    def __exit__(self, ex_type, ex_value, trace) -> None:
        ...
