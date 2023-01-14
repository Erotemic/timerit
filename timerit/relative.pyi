from numbers import Number


class Relative:

    @staticmethod
    def percent_change(new: Number, old: Number) -> float:
        ...

    @staticmethod
    def percent_decrease(new: Number, old: Number) -> float:
        ...

    @staticmethod
    def percent_increase(new: Number, old: Number) -> float:
        ...

    @staticmethod
    def percent_smaller(new: Number, old: Number) -> float:
        ...

    @staticmethod
    def percent_bigger(new: Number, old: Number) -> float:
        ...

    @staticmethod
    def percent_slower(new: float, old: float) -> float:
        ...

    @staticmethod
    def percent_faster(new: float, old: float) -> float:
        ...
