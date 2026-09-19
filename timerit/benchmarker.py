"""Utilities for parameterized microbenchmarks built on :mod:`timerit`.

The :class:`Benchmarker` helper handles the repetitive bookkeeping involved in
benchmarking multiple implementations across a parameter grid.  Its core
measurement path only depends on the Python standard library and timerit.
Pandas and kwplot are imported lazily by the convenience reporting methods.
"""

from __future__ import annotations

import importlib
import inspect
import itertools as it
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Mapping
from collections.abc import Sequence
from typing import Any
from typing import overload

from timerit.core import Timerit


__all__ = ['Benchmarker']


BenchmarkFunc = Callable[..., Any]
AdapterFunc = Callable[..., Mapping[str, Any]]


def _coerce_labels(labels: str | Sequence[str] | None) -> list[str]:
    if labels is None:
        return []
    if isinstance(labels, str):
        return [labels]
    return list(labels)


def _named_product(basis: Mapping[str, Sequence[Any]]) -> Iterable[dict[str, Any]]:
    """Small dependency-free equivalent of ``ubelt.named_product``."""
    keys = list(basis)
    if not keys:
        yield {}
        return
    columns = [basis[key] for key in keys]
    for values in it.product(*columns):
        yield dict(zip(keys, values))


def _compatible_kwargs(params: Mapping[str, Any], func: Callable[..., Any]) -> dict[str, Any]:
    """Select the subset of ``params`` accepted as keyword arguments."""
    signature = inspect.signature(func)
    parameters = signature.parameters
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in parameters.values()):
        return dict(params)

    positional_only = [
        name for name, p in parameters.items()
        if p.kind == inspect.Parameter.POSITIONAL_ONLY and p.default is inspect.Parameter.empty
    ]
    if positional_only:
        raise TypeError(
            'Benchmarker only supplies keyword arguments, but '
            f'{func!r} has required positional-only parameters: {positional_only!r}'
        )

    accepted = {
        name
        for name, p in parameters.items()
        if p.kind in {
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }
    }
    return {key: value for key, value in params.items() if key in accepted}


def _format_params(params: Mapping[str, Any]) -> str:
    return ', '.join(f'{key}={value!r}' for key, value in params.items())


def _speedup(slowest: float, value: float) -> float:
    if value:
        return slowest / value
    return 1.0 if slowest == 0 else float('inf')


class Benchmarker:
    """Run several implementations over a shared parameter grid.

    Args:
        title:
            Human-readable title used by :meth:`plot`.
        num_trials:
            Number of timer iterations for each method / parameter combination.
            If ``None``, :class:`Timerit` uses ``min_duration`` instead.
        bestof:
            Passed to :class:`Timerit`.
        record_times:
            If true, retain each robust ``bestof`` sample in :attr:`rows`.
            If false, :attr:`rows` contains one summary row per benchmark case.
        verbose:
            Timerit verbosity for each benchmark case.
        min_duration:
            Passed to :class:`Timerit` when ``num_trials`` is ``None``.
        disable_gc:
            Passed to :class:`Timerit`.
        timer_cls:
            Optional custom Timer class, primarily useful for testing.

    Notes:
        Data adapters are setup hooks.  When registered, the selected adapter
        runs once immediately before *each* timed iteration and returns keyword
        arguments for the benchmarked method.  Adapter execution is not timed.
        This makes it possible to create fresh mutable inputs for every trial.

        Plotting and dataframe helpers are optional conveniences.  The core
        benchmark runner does not require pandas, kwplot, or ubelt.

    Example:
        >>> from timerit.benchmarker import Benchmarker
        >>> bm = Benchmarker(num_trials=3, bestof=1, verbose=0)
        >>> @bm.register
        >>> def list_comp(n):
        >>>     return [i for i in range(n)]
        >>> @bm.register
        >>> def append_loop(n):
        >>>     result = []
        >>>     for i in range(n):
        >>>         result.append(i)
        >>>     return result
        >>> bm.set_basis({'n': [1, 10]})
        >>> bm.set_plot_semantics(x='n')
        >>> _ = bm.run()
        >>> len(bm.stats) == 4
        True
    """

    def __init__(
        self,
        title: str = 'Benchmark',
        num_trials: int | None = 100,
        bestof: int = 10,
        record_times: bool = True,
        verbose: int = 1,
        min_duration: float = 0.2,
        disable_gc: bool = True,
        timer_cls: Any = None,
    ) -> None:
        self.method_lut: dict[str, BenchmarkFunc] = {}
        self.basis: dict[str, list[Any]] = {}
        self.plot_semantics: dict[str, str | list[str] | None] = {
            'x': None,
            'hue': [],
            'style': [],
            'size': [],
        }
        self.plot_labels: dict[str, str | None] = {
            'x': None,
            'y': 'Time',
            'title': title,
        }
        self.record_times = record_times
        self.ti = Timerit(
            num_trials,
            bestof=bestof,
            verbose=verbose,
            min_duration=min_duration,
            disable_gc=disable_gc,
            timer_cls=timer_cls,
        )
        self.data_adapters: dict[str, AdapterFunc] = {}
        self.global_data_adapter: AdapterFunc | None = None
        self.rows: list[dict[str, Any]] = []
        self.stats: list[dict[str, Any]] = []
        self.time_key = 'time' if record_times else 'min'

    @overload
    def register(
        self,
        func: None = None,
        *,
        name: str | None = None,
    ) -> Callable[[BenchmarkFunc], BenchmarkFunc]:
        ...

    @overload
    def register(
        self,
        func: BenchmarkFunc,
        *,
        name: str | None = None,
    ) -> BenchmarkFunc:
        ...

    def register(
        self,
        func: BenchmarkFunc | None = None,
        *,
        name: str | None = None,
    ) -> BenchmarkFunc | Callable[[BenchmarkFunc], BenchmarkFunc]:
        """Register a benchmark implementation, usually as a decorator."""
        if func is None:
            def decorator(inner: BenchmarkFunc) -> BenchmarkFunc:
                method_name = name or inner.__name__
                if method_name in self.method_lut:
                    raise KeyError(
                        f'A benchmark method named {method_name!r} is already registered')
                self.method_lut[method_name] = inner
                return inner
            return decorator

        method_name = name or func.__name__
        if method_name in self.method_lut:
            raise KeyError(f'A benchmark method named {method_name!r} is already registered')
        self.method_lut[method_name] = func
        return func

    @overload
    def register_data_adapter(
        self,
        func: None = None,
        *,
        for_method: str | None = None,
    ) -> Callable[[AdapterFunc], AdapterFunc]:
        ...

    @overload
    def register_data_adapter(
        self,
        func: AdapterFunc,
        *,
        for_method: str | None = None,
    ) -> AdapterFunc:
        ...

    def register_data_adapter(
        self,
        func: AdapterFunc | None = None,
        *,
        for_method: str | None = None,
    ) -> AdapterFunc | Callable[[AdapterFunc], AdapterFunc]:
        """Register an untimed setup hook that produces method keyword args.

        A method-specific adapter takes precedence over the global adapter.
        Only basis parameters accepted by the adapter are supplied to it.
        """
        if func is None:
            def decorator(inner: AdapterFunc) -> AdapterFunc:
                if for_method is None:
                    self.global_data_adapter = inner
                else:
                    self.data_adapters[for_method] = inner
                return inner
            return decorator

        if for_method is None:
            self.global_data_adapter = func
        else:
            self.data_adapters[for_method] = func
        return func

    def set_basis(self, basis: Mapping[str, Iterable[Any]]) -> None:
        """Set the non-method dimensions of the benchmark parameter grid."""
        if 'method' in basis:
            raise ValueError("'method' is reserved by Benchmarker")
        self.basis = {key: list(values) for key, values in basis.items()}

    def set_plot_semantics(
        self,
        x: str | None = None,
        hue: str | Sequence[str] | None = None,
        style: str | Sequence[str] | None = None,
        size: str | Sequence[str] | None = None,
    ) -> None:
        """Describe how benchmark dimensions map to seaborn plot semantics."""
        style_labels = _coerce_labels(style)
        size_labels = _coerce_labels(size)
        self.plot_semantics['x'] = x
        self.plot_semantics['style'] = style_labels
        self.plot_semantics['size'] = size_labels

        if hue is None:
            excluded = {x, *style_labels, *size_labels}
            hue_labels = [
                key for key in ['method', *self.basis]
                if key not in excluded
            ]
        else:
            hue_labels = _coerce_labels(hue)
        self.plot_semantics['hue'] = hue_labels

    def set_plot_labels(
        self,
        *,
        x: str | None = None,
        y: str | None = None,
        title: str | None = None,
    ) -> None:
        """Override display labels used by :meth:`plot`."""
        if x is not None:
            self.plot_labels['x'] = x
        if y is not None:
            self.plot_labels['y'] = y
        if title is not None:
            self.plot_labels['title'] = title

    def _adapter_for(self, method_name: str) -> AdapterFunc | None:
        return self.data_adapters.get(method_name, self.global_data_adapter)

    def _make_inputs(
        self,
        method_name: str,
        basis_params: Mapping[str, Any],
    ) -> dict[str, Any]:
        method = self.method_lut[method_name]
        adapter = self._adapter_for(method_name)
        if adapter is None:
            return _compatible_kwargs(basis_params, method)

        adapter_kwargs = _compatible_kwargs(basis_params, adapter)
        method_kwargs = adapter(**adapter_kwargs)
        if not isinstance(method_kwargs, Mapping):
            raise TypeError(
                f'Data adapter for {method_name!r} returned '
                f'{type(method_kwargs).__name__}, expected a mapping')
        return dict(method_kwargs)

    def _group_keys(self, params: Mapping[str, Any]) -> dict[str, str]:
        group_keys: dict[str, str] = {}
        for kind in ['hue', 'style', 'size']:
            labels = self.plot_semantics[kind]
            if labels:
                assert isinstance(labels, list)
                selected = {label: params[label] for label in labels}
                group_keys[f'{kind}_key'] = _format_params(selected)
        return group_keys

    def _compute_speedup_stats(self) -> None:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in self.stats:
            grouped.setdefault(row['case_key'], []).append(row)

        for variants in grouped.values():
            slowest_mean = max(row['mean'] for row in variants)
            slowest_min = max(row['min'] for row in variants)
            for row in variants:
                row['mean_speedup'] = _speedup(slowest_mean, row['mean'])
                row['min_speedup'] = _speedup(slowest_min, row['min'])

    def run(self) -> Benchmarker:
        """Execute every registered method over every point in the basis."""
        if not self.method_lut:
            raise RuntimeError('No benchmark methods are registered')

        rows: list[dict[str, Any]] = []
        stats: list[dict[str, Any]] = []
        for basis_params in _named_product(self.basis):
            case_key = _format_params(basis_params)
            for method_name, method in self.method_lut.items():
                params = {'method': method_name, **basis_params}
                key = _format_params(params)
                group_keys = self._group_keys(params)
                adapter = self._adapter_for(method_name)
                fixed_method_kwargs = None
                if adapter is None:
                    fixed_method_kwargs = self._make_inputs(method_name, basis_params)

                for timer in self.ti.reset(key):
                    if fixed_method_kwargs is None:
                        method_kwargs = self._make_inputs(method_name, basis_params)
                    else:
                        method_kwargs = fixed_method_kwargs
                    with timer:
                        method(**method_kwargs)

                stat_row = {
                    'mean': self.ti.mean(),
                    'min': self.ti.min(),
                    'key': key,
                    'case_key': case_key,
                    **params,
                    **group_keys,
                }
                stats.append(stat_row)

                if self.record_times:
                    for measured_time in self.ti.robust_times():
                        rows.append({
                            'time': measured_time,
                            'key': key,
                            'case_key': case_key,
                            **params,
                            **group_keys,
                        })
                else:
                    rows.append(dict(stat_row))

        self.rows = rows
        self.stats = stats
        self._compute_speedup_stats()
        return self

    def dataframe(self):
        """Return recorded observations as a pandas DataFrame."""
        try:
            pd: Any = importlib.import_module('pandas')
        except ImportError as ex:
            raise ImportError(
                'dataframe() requires pandas; install timerit[optional]') from ex
        return pd.DataFrame(self.rows).sort_values(self.time_key).reset_index(drop=True)

    def stats_dataframe(self):
        """Return one summary row per benchmark case as a pandas DataFrame."""
        try:
            pd: Any = importlib.import_module('pandas')
        except ImportError as ex:
            raise ImportError(
                'stats_dataframe() requires pandas; install timerit[optional]') from ex
        return pd.DataFrame(self.stats).sort_values('min').reset_index(drop=True)

    @property
    def df(self):
        """Alias for :meth:`dataframe` for interactive use."""
        return self.dataframe()

    @property
    def stats_data(self):
        """Alias for :meth:`stats_dataframe` for interactive use."""
        return self.stats_dataframe()

    def plot(self, show: bool = True):
        """Plot results using kwplot / seaborn.

        Requires the optional ``pandas`` and ``kwplot`` packages.
        """
        x = self.plot_semantics['x']
        if not x:
            raise RuntimeError('Specify an x dimension with set_plot_semantics(x=...)')
        if not self.rows:
            raise RuntimeError('Run the benchmark before plotting')

        try:
            kwplot: Any = importlib.import_module('kwplot')
        except ImportError as ex:
            raise ImportError(
                'plot() requires kwplot and pandas; install timerit[optional]') from ex

        sns = kwplot.autosns()
        plt = kwplot.autoplt()
        plotkw = {}
        for key in ['hue', 'style', 'size']:
            if self.plot_semantics[key]:
                plotkw[key] = key + '_key'

        ax = kwplot.figure(fnum=1, doclf=True).gca()
        sns.lineplot(
            data=self.dataframe(),
            x=x,
            y=self.time_key,
            marker='o',
            ax=ax,
            **plotkw,
        )
        ax.set_title(self.plot_labels['title'])
        ax.set_xlabel(self.plot_labels['x'] or x)
        ax.set_ylabel(self.plot_labels['y'])
        if show:
            plt.show()
        return ax
