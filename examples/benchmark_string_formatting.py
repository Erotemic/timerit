

def benchmark_template():
    import ubelt as ub
    import pandas as pd
    import timerit
    import inspect

    plot_labels = {
        'x': 'Number of arguments',
        'y': 'Seconds',
        'title': 'string % op vs .format method',
    }

    # Some bookkeeping needs to be done to build a dictionary that maps the
    # method names to the functions themselves.
    method_lut = {}
    def register_method(func):
        method_lut[func.__name__] = func
        return func

    # Define the methods you want to benchmark. The arguments should be
    # parameters that you want to vary in the test.

    @register_method
    def format_method(template, args):
        ret = template.format(*args)
        return ret

    @register_method
    def percent_operator(template, args):
        ret = template % args
        return ret

    # Change params here to modify number of trials
    ti = timerit.Timerit(1000, bestof=30, verbose=1)

    # if True, record every trail run and show variance in seaborn
    # if False, use the standard timerit min/mean measures
    RECORD_ALL = True

    # These are the parameters that we benchmark over
    basis = {
        'method': list(method_lut),
        'num_vars': [0, 30],
        'arg_type': ['int', 'padded_int', 'float', 'padded_float', 'string'],
    }
    # Set these to param labels that directly transfer to method kwargs
    kw_labels = list(inspect.signature(ub.peek(method_lut.values())).parameters)
    # i.e.
    # kw_labels = ['xparam', 'y', 'z']
    # Set these to empty lists if they are not used, removing dict items breaks
    # the code.
    xlabel = 'num_vars'
    group_labels = {
        'style': ['arg_type'],
        # 'size': ['zparam'],
    }
    group_labels['hue'] = list(
        (ub.oset(basis) - {xlabel}) - set.union(*map(set, group_labels.values())))
    grid_iter = list(ub.named_product(basis))

    # For each variation of your experiment, create a row.
    rows = []
    for params in grid_iter:
        params = ub.udict(params)
        group_keys = {}
        for gname, labels in group_labels.items():
            group_keys[gname + '_key'] = ub.urepr(
                params & labels, compact=1, si=1)
        key = ub.urepr(params, compact=1, si=1)
        # Make any modifications you need to compute input kwargs for each
        # method here.
        kwargs = params & kw_labels

        if params['arg_type'] == 'int':
            arg_part = 3
        elif params['arg_type'] == 'float':
            arg_part = 1 / 3
        elif params['arg_type'] == 'padded_int':
            arg_part = 3
        elif params['arg_type'] == 'string':
            arg_part = '3'

        if params['method'] == 'format_method':
            if params['arg_type'] == 'int':
                template_part = '{:d}'
            elif params['arg_type'] == 'float':
                template_part = '{:f}'
            elif params['arg_type'] == 'padded_float':
                template_part = '{:05.3}'
            elif params['arg_type'] == 'padded_int':
                template_part = '{:03d}'
            elif params['arg_type'] == 'string':
                template_part = '{:s}'
            kwargs['template'] = ''.join([template_part] * params['num_vars'])
            kwargs['args'] = tuple([arg_part] * params['num_vars'])

        elif params['method'] == 'percent_operator':
            if params['arg_type'] == 'int':
                template_part = '%d'
            elif params['arg_type'] == 'float':
                template_part = '%f'
            elif params['arg_type'] == 'padded_float':
                template_part = '%05.3f'
            elif params['arg_type'] == 'padded_int':
                template_part = '%03d'
            elif params['arg_type'] == 'string':
                template_part = '%s'
            kwargs['template'] = ''.join([template_part] * params['num_vars'])
            kwargs['args'] = tuple([arg_part] * params['num_vars'])

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
        ax.set_title(plot_labels['title'])
        ax.set_xlabel(plot_labels['x'])
        ax.set_ylabel(plot_labels['y'])
        # ax.set_xscale('log')
        # ax.set_xscale('log')
        # ax.set_yscale('log')

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
