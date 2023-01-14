

def benchmark_nested_break():
    """
    There are several ways to do a nested break, but which one is best?

    https://twitter.com/nedbat/status/1515345787563220996
    """
    import ubelt as ub
    import pandas as pd
    import timerit
    import itertools as it

    def method1_itertools(iter1, iter2):
        for i, j in it.product(iter1, iter2):
            if i == 20 and j == 20:
                break

    def method2_except(iter1, iter2):
        class Found(Exception):
            pass
        try:
            for i in iter1:
                for j in iter2:
                    if i == 20 and j == 20:
                        raise Found
        except Found:
            pass

    class FoundPredef(Exception):
        pass

    def method2_5_except_predef(iter1, iter2):
        try:
            for i in iter1:
                for j in iter2:
                    if i == 20 and j == 20:
                        raise FoundPredef
        except FoundPredef:
            pass

    def method3_gendef(iter1, iter2):
        def genfunc():
            for i in iter1:
                for j in iter2:
                    yield i, j

        for i, j in genfunc():
            if i == 20 and j == 20:
                break

    def method4_genexp(iter1, iter2):
        genexpr = ((i, j) for i in iter1 for j in iter2)
        for i, j in genexpr:
            if i == 20 and j == 20:
                break

    method_lut = locals()  # can populate this some other way

    # Change params here to modify number of trials
    ti = timerit.Timerit(1000, bestof=10, verbose=1)

    # if True, record every trail run and show variance in seaborn
    # if False, use the standard timerit min/mean measures
    RECORD_ALL = True

    # These are the parameters that we benchmark over
    import numpy as np
    basis = {
        'method': ['method1_itertools', 'method2_except', 'method2_5_except_predef', 'method3_gendef', 'method4_genexp'],
        # 'n1': np.logspace(1, np.log2(100), 30, base=2).astype(int),
        # 'n2': np.logspace(1, np.log2(100), 30, base=2).astype(int),
        'size': np.logspace(1, np.log2(10000), 30, base=2).astype(int),
        'input_style': ['range', 'list', 'customized_iter'],
        # 'param_name': [param values],
    }
    xlabel = 'size'
    xinput_labels = ['n1', 'n2', 'size']

    # Set these to param labels that directly transfer to method kwargs
    kw_labels = []
    # Set these to empty lists if they are not used
    group_labels = {
        'style': ['input_style'],
        'size': [],
    }
    group_labels['hue'] = list(
        (ub.oset(basis) - {xlabel} - xinput_labels) - set.union(*map(set, group_labels.values())))
    grid_iter = list(ub.named_product(basis))

    def make_input(params):
        # Given the parameterization make the benchmark function input
        # n1 = params['n1']
        # n2 = params['n2']
        size = params['size']
        n1 = int(np.sqrt(size))
        n2 = int(np.sqrt(size))
        if params['input_style'] == 'list':
            iter1 = list(range(n1))
            iter2 = list(range(n1))
        elif params['input_style'] == 'range':
            iter1 = range(n1)
            iter2 = range(n2)
        elif params['input_style'] == 'customized_iter':
            import random
            def rando1():
                rng1 = random.Random(0)
                for _ in range(n1):
                    yield rng1.randint(0, n2)

            def rando2():
                rng2 = random.Random(1)
                for _ in range(n1):
                    yield rng2.randint(0, n2)

            iter1 = rando1()
            iter2 = rando2()
        else:
            raise KeyError
        return {'iter1': iter1, 'iter2': iter2}

    # For each variation of your experiment, create a row.
    rows = []
    for params in grid_iter:
        # size = params['n1'] * params['n2']
        # params['size'] = size
        group_keys = {}
        for gname, labels in group_labels.items():
            group_keys[gname + '_key'] = ub.repr2(
                ub.dict_isect(params, labels), compact=1, si=1)
        key = ub.repr2(params, compact=1, si=1)
        # Make any modifications you need to compute input kwargs for each
        # method here.
        kwargs = ub.dict_isect(params.copy(),  kw_labels)

        method = method_lut[params['method']]
        # Timerit will run some user-specified number of loops.
        # and compute time stats with similar methodology to timeit
        for timer in ti.reset(key):
            # Put any setup logic you dont want to time here.
            # ...
            kwargs.update(make_input(params))
            with timer:
                # Put the logic you want to time here
                method(**kwargs)

        if RECORD_ALL:
            # Seaborn will show the variance if this is enabled, otherwise
            # use the robust timerit mean / min times
            # chunk_iter = ub.chunks(ti.times, ti.bestof)
            # times = list(map(min, chunk_iter))  # TODO: timerit method for this
            times = ti.robust_times()
            for time in times:
                row = {
                    # 'mean': ti.mean(),
                    'time': time,
                    'key': key,
                    **group_keys,
                    **params,
                }
                rows.append(row)
        else:
            row = {
                'mean': ti.mean(),
                'min': ti.min(),
                'key': key,
                **group_keys,
                **params,
            }
            rows.append(row)

    time_key = 'time' if RECORD_ALL else 'min'

    # The rows define a long-form pandas data array.
    # Data in long-form makes it very easy to use seaborn.
    data = pd.DataFrame(rows)
    data = data.sort_values(time_key)

    if RECORD_ALL:
        # Show the min / mean if we record all
        min_times = data.groupby('key').min().rename({'time': 'min'}, axis=1)
        mean_times = data.groupby('key')[['time']].mean().rename({'time': 'mean'}, axis=1)
        stats_data = pd.concat([min_times, mean_times], axis=1)
        stats_data = stats_data.sort_values('min')
    else:
        stats_data = data

    USE_OPENSKILL = 0
    if USE_OPENSKILL:
        # Lets try a real ranking method
        # https://github.com/OpenDebates/openskill.py
        import openskill
        method_ratings = {m: openskill.Rating() for m in basis['method']}

    other_keys = sorted(set(stats_data.columns) - {'key', 'method', 'min', 'mean', 'hue_key', 'size_key', 'style_key'})
    for params, variants in stats_data.groupby(other_keys):
        variants = variants.sort_values('mean')
        ranking = variants['method'].reset_index(drop=True)

        mean_speedup = variants['mean'].max() / variants['mean']
        stats_data.loc[mean_speedup.index, 'mean_speedup'] = mean_speedup
        min_speedup = variants['min'].max() / variants['min']
        stats_data.loc[min_speedup.index, 'min_speedup'] = min_speedup

        if USE_OPENSKILL:
            # The idea is that each setting of parameters is a game, and each
            # "method" is a player. We rank the players by which is fastest,
            # and update their ranking according to the Weng-Lin Bayes ranking
            # model. This does not take the fact that some "games" (i.e.
            # parameter settings) are more important than others, but it should
            # be fairly robust on average.
            old_ratings = [[r] for r in ub.take(method_ratings, ranking)]
            new_values = openskill.rate(old_ratings)  # Not inplace
            new_ratings = [openskill.Rating(*new[0]) for new in new_values]
            method_ratings.update(ub.dzip(ranking, new_ratings))

    print('Statistics:')
    print(stats_data)

    if USE_OPENSKILL:
        from openskill import predict_win
        win_prob = predict_win([[r] for r in method_ratings.values()])
        skill_agg = pd.Series(ub.dzip(method_ratings.keys(), win_prob)).sort_values(ascending=False)
        print('method_ratings = {}'.format(ub.repr2(method_ratings, nl=1)))
        print('Aggregated Rankings =\n{}'.format(skill_agg))

    plot = True
    if plot:
        # import seaborn as sns
        # kwplot autosns works well for IPython and script execution.
        # not sure about notebooks.
        import kwplot
        sns = kwplot.autosns()
        plt = kwplot.autoplt()

        plotkw = {}
        for gname, labels in group_labels.items():
            if labels:
                plotkw[gname] = gname + '_key'

        # Your variables may change
        ax = kwplot.figure(fnum=1, doclf=True).gca()
        sns.lineplot(data=data, x=xlabel, y=time_key, marker='o', ax=ax, **plotkw)
        ax.set_title(f'Benchmark Nested Breaks: #Trials {ti.num}, bestof {ti.bestof}')
        ax.set_xlabel(f'{xlabel}')
        ax.set_ylabel('Time')
        ax.set_xscale('log')
        ax.set_yscale('log')

        try:
            __IPYTHON__
        except NameError:
            plt.show()


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/timerit/examples/benchmark_nested_break.py
    """
    benchmark_nested_break()
