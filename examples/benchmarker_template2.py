"""A compact parameterized benchmark using :class:`timerit.benchmarker.Benchmarker`.

This is the higher-level counterpart to ``benchmark_template.py``. The older
example shows dataframe / plotting bookkeeping explicitly; this example uses
the reusable helper that factors that bookkeeping out.
"""


def benchmarker_template2():
    from timerit.benchmarker import Benchmarker

    bm = Benchmarker(
        title='Benchmark Example',
        num_trials=100,
        bestof=10,
        record_samples=True,
        verbose=1,
    )

    # Register implementations that should compute equivalent results.
    @bm.register
    def list_comp(n):
        return [i for i in range(n)]

    @bm.register
    def append_loop(data_size):
        result = []
        for i in range(data_size):
            result.append(i)
        return result

    # A method-specific adapter lets a method use a different call signature.
    # It runs before each timed iteration, so setup is excluded from the timing.
    @bm.register_data_adapter(for_method='append_loop')
    def adapt_append_loop(n):
        return {'data_size': n}

    bm.set_basis({
        'n': [0, 10, 100, 1_000, 10_000],
    })
    bm.run()

    print('Statistics:')
    print(bm.stats_df)

    # Plot configuration is independent of measurement and may be selected
    # after run(). Requires the optional pandas / kwplot dependencies.
    bm.set_plot_semantics(x='n')
    bm.set_plot_labels(x='List size', y='Time (seconds)')
    bm.plot(stat='mean')
    return bm


if __name__ == '__main__':
    r"""
    CommandLine:
        python examples/benchmarker_template2.py
    """
    benchmarker_template2()
