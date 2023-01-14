
"""
This inspriation for this was to benchamrk a candidate speedup for
~/code/networkx/networkx/generators/nonisomorphic_trees.py in _split_tree.
Funny story. It turns out the most common param they used was nearly at the
crossover point where all methods do about as well as each other.
"""


def benchmark_template():
    import ubelt as ub
    import pandas as pd
    import timerit
    import itertools as it

    # def f(x):
    #     return x * 3 + 1
    lut = {x: x * 3 + 1 for x in range(100000)}
    f = lut.__getitem__

    def method_plus(N):
        [0] + [f(i) for i in range(N)]

    def method_chain_gen(N):
        list(it.chain([0], (f(i) for i in range(N))))

    def method_chain_map(N):
        list(it.chain([0], map(f, range(N))))

    def method_insert(N):
        r = [f(i) for i in range(N)]
        r.insert(0, 0)

    method_lut = locals()  # can populate this some other way

    # Change params here to modify number of trials
    ti = timerit.Timerit(100, bestof=10, verbose=1)

    # if True, record every trail run and show variance in seaborn
    # if False, use the standard timerit min/mean measures
    RECORD_ALL = True

    # These are the parameters that we benchmark over
    basis = {
        'method': ['method_plus', 'method_chain_gen', 'method_chain_map', 'method_insert'],
        'N': list(range(1, 100)),
    }
    xlabel = 'N'
    # Set these to param labels that directly transfer to method kwargs
    kw_labels = ['N']
    # Set these to empty lists if they are not used
    group_labels = {
        'style': [],
        'size': [],
    }
    group_labels['hue'] = list(
        (ub.oset(basis) - {xlabel}) - set.union(*map(set, group_labels.values())))
    grid_iter = list(ub.named_product(basis))

    # For each variation of your experiment, create a row.
    rows = []
    for params in grid_iter:
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
        ax.set_title('Benchmark Name')
        ax.set_xlabel('Size of List')
        ax.set_ylabel('Time to prepend a zero to a new list')
        # ax.set_xscale('log')
        ax.set_yscale('log')

        try:
            __IPYTHON__
        except NameError:
            plt.show()


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/timerit/examples/benchmark_template.py
    """
    benchmark_template()
