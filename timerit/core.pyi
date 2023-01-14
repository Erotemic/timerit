from typing import Union
from typing import Any
from typing import List
from typing import Dict
from _typeshed import Incomplete
from typing import Any

default_counter: str


class Timer:
    label: str
    verbose: Union[int, None]
    newline: bool
    write: Incomplete
    flush: Incomplete

    def __init__(self,
                 label: str = '',
                 verbose: Union[int, None] = None,
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
    num: int
    label: Union[str, None]
    bestof: int
    unit: Union[str, None]
    verbose: Union[int, None]
    times: Incomplete
    total_time: int
    n_loops: Incomplete
    measures: Incomplete

    def __init__(self,
                 num: int = 1,
                 label: Union[str, None] = None,
                 bestof: int = 3,
                 unit: Union[str, None] = None,
                 verbose: Union[int, None] = None,
                 disable_gc: bool = True,
                 timer_cls: Union[None, Any] = None) -> None:
        ...

    def reset(self,
              label: Union[str, None] = None,
              measures: bool = False) -> Timerit:
        ...

    def call(self, func, *args, **kwargs) -> Timerit:
        ...

    def __iter__(self):
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
