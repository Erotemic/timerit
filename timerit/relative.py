"""
Helpers for making relative statements about an increase or decrase
"""


class Relative:

    @staticmethod
    def percent_change(new, old):
        """
        `new` is `old` changed by `percent`

        Args:
            new (Number): the value before a change
            old (Number): the value after a change

        Returns:
            float:

        Notes:
            negative numbers are percent increases
            positive numbers are percent decreases

        Example:
            >>> Relative.percent_change(5, 1)
            -400.0
            >>> Relative.percent_change(1, 5)
            80.0
        """
        decrease = (old - new)
        frac = decrease / old
        percent = frac * 100.0
        return percent

    @staticmethod
    def percent_decrease(new, old):
        """
        `new` is `percent`% smaller than `old`

        Args:
            new (Number): the value before a change
            old (Number): the value after a change

        Returns:
            float:

        >>> Relative.percent_decrease(1, 5)
        80.0
        >>> Relative.percent_decrease(2153, 3469)
        37.9360...
        """
        assert new <= old, 'Not a decrease... want {} <= {}'.format(new, old)
        percent = Relative.percent_change(new, old)
        return percent

    @staticmethod
    def percent_increase(new, old):
        """
        `new` is `percent`% larger than `old`

        Args:
            new (Number): the value before a change
            old (Number): the value after a change

        Returns:
            float:

        Example:
            >>> Relative.percent_increase(5, 1)
            400.0
            >>> Relative.percent_increase(8.6, 8.5)
            1.176...
        """
        assert new >= old, 'Not an increase... want {} >= {}'.format(new, old)
        percent = -Relative.percent_change(new, old)
        return percent

    @staticmethod
    def percent_smaller(new, old):
        """
        `new` is `percent`% smaller than `old`

        Args:
            new (Number): the value before a change
            old (Number): the value after a change

        Returns:
            float: a percent decrease
        """
        percent = Relative.percent_decrease(new, old)
        return percent

    @staticmethod
    def percent_bigger(new, old):
        """
        `new` is `percent`% smaller than `old`

        Args:
            new (Number): the value before a change
            old (Number): the value after a change

        Returns:
            float: a percent increase
        """
        percent = Relative.percent_increase(new, old)
        return percent

    @staticmethod
    def percent_slower(new, old):
        """
        `new` is X percent slower than `old`

        Args:
            new (float): measure of duration before a change
            old (float): measure of duration after a change (with same units as new)

        Returns:
            float: a percent increase in duration

        Example:
            >>> from timerit.relative import Relative
            >>> old = 8.72848
            >>> new = 9.59755
            >>> print('{:.3f}% slower'.format(Relative.percent_slower(new, old)))
            9.957% slower
            >>> new = 3.6053
            >>> old = 1.3477
            >>> Relative.percent_slower(new, old)
            >>> print('{:.3f}% slower'.format(Relative.percent_slower(new, old)))
            167.515% slower
        """
        # Slowness is an increase in time
        return Relative.percent_increase(new, old)

    @staticmethod
    def percent_faster(new, old):
        """
        `new` is `percent`% faster than `old`

        Args:
            new (float): measure of duration before a change
            old (float): measure of duration after a change (with same units as new)

        Returns:
            float: a percent decrease in duration

        References:
            .. [SO8127862] https://stackoverflow.com/questions/8127862/how-do-you-calculate-how-much-faster-time-x-is-from-time-y-in-terms-of
            .. [SO716767] https://math.stackexchange.com/questions/716767/how-to-calculate-the-percentage-of-increase-decrease-with-negative-numbers/716770#716770

        Notes:
            Equivalent to Relative.percent_decrease, because Faster means time
            is decreasing.

        Example:
            >>> new = 8.59755
            >>> old = 8.72848
            >>> print('{:.3f}% faster'.format(Relative.percent_faster(new, old)))
            1.500% faster
            >>> new = 0.6053
            >>> old = 1.3477
            >>> Relative.percent_faster(new, old)
            >>> print('{:.3f}% faster'.format(Relative.percent_faster(new, old)))
            55.086% faster
        """
        return Relative.percent_decrease(new, old)
