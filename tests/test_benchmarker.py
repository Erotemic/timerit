from timerit.benchmarker import Benchmarker


def test_benchmarker_heterogeneous_signatures_and_adapters():
    calls = []
    adapter_calls = []

    bm = Benchmarker(num_trials=2, bestof=1, record_samples=False, verbose=0)

    @bm.register
    def direct(x):
        calls.append(('direct', x))

    @bm.register
    def adapted(value):
        calls.append(('adapted', value))

    @bm.register_data_adapter(for_method='adapted')
    def adapt(x):
        adapter_calls.append(x)
        return {'value': x + 10}

    bm.set_basis({'x': [1, 2]})
    bm.run()

    assert calls.count(('direct', 1)) == 2
    assert calls.count(('direct', 2)) == 2
    assert calls.count(('adapted', 11)) == 2
    assert calls.count(('adapted', 12)) == 2
    assert adapter_calls == [1, 1, 2, 2]
    assert len(bm.stats) == 4
    assert len(bm.rows) == 4


def test_benchmarker_records_robust_samples():
    bm = Benchmarker(num_trials=4, bestof=2, record_samples=True, verbose=0)

    @bm.register
    def method1(n):
        return n + 1

    @bm.register
    def method2(n):
        return n * 2

    bm.set_basis({'n': [1, 2]})
    bm.run()

    # 2 methods * 2 parameter values * (4 trials / bestof 2)
    assert len(bm.rows) == 8
    assert len(bm.stats) == 4
    assert all('time' in row for row in bm.rows)
    assert all(row['mean_speedup_vs_slowest'] >= 1 for row in bm.stats)
    assert all(row['min_speedup_vs_slowest'] >= 1 for row in bm.stats)


def test_benchmarker_allows_method_only_benchmark():
    bm = Benchmarker(num_trials=1, bestof=1, record_samples=False, verbose=0)

    @bm.register
    def first():
        pass

    @bm.register
    def second():
        pass

    bm.set_basis({})
    bm.run()

    assert {row['method'] for row in bm.stats} == {'first', 'second'}
    assert len(bm.stats) == 2


def test_benchmarker_run_does_not_require_plot_configuration():
    bm = Benchmarker(num_trials=1, bestof=1, verbose=0)

    @bm.register
    def method(n):
        return n

    bm.set_basis({'n': [1]})
    result = bm.run()
    assert result is bm


def test_benchmarker_rejects_reserved_basis_name():
    bm = Benchmarker(verbose=0)
    try:
        bm.set_basis({'method': ['foo']})
    except ValueError:
        pass
    else:
        raise AssertionError('expected method basis name to be reserved')


def test_benchmarker_callable_object_requires_or_accepts_name():
    class CallableMethod:
        def __call__(self, n):
            return n

    bm = Benchmarker(num_trials=1, bestof=1, verbose=0)
    method = CallableMethod()

    try:
        bm.register(method)
    except TypeError:
        pass
    else:
        raise AssertionError('unnamed callable object should require name=')

    bm.register(method, name='callable_method')
    bm.set_basis({'n': [1]})
    bm.run()
    assert bm.stats[0]['method'] == 'callable_method'


def test_benchmarker_rejects_adapter_for_unknown_method():
    bm = Benchmarker(num_trials=1, bestof=1, verbose=0)

    @bm.register
    def known(n):
        return n

    @bm.register_data_adapter(for_method='typo')
    def adapter(n):
        return {'n': n}

    bm.set_basis({'n': [1]})
    try:
        bm.run()
    except KeyError as ex:
        assert 'typo' in str(ex)
    else:
        raise AssertionError('unknown adapter target should be rejected')


def test_benchmarker_plot_configuration_can_change_after_run():
    bm = Benchmarker(num_trials=1, bestof=1, verbose=0)

    @bm.register
    def first(n):
        return n

    @bm.register
    def second(n):
        return n

    bm.set_basis({'n': [1, 2]})
    bm.run()
    bm.set_plot_semantics(x='n', hue='method')

    # Plot metadata is derived from stored statistics after measurement rather
    # than being baked into the timing rows during run(). This helper requires
    # pandas, so only check the independence at the plain-data level here.
    assert all('hue_key' not in row for row in bm.rows)
    assert all('hue_key' not in row for row in bm.stats)

def test_benchmarker_is_not_top_level_api():
    import timerit

    assert 'Benchmarker' not in timerit.__all__
    assert not hasattr(timerit, 'Benchmarker')

