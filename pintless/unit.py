from __future__ import annotations
from typing import Union

from .quantity import Quantity

ValidMagnitude = Union[int, float, complex]


class Unit:
    def __init__(self, name, unit_type, base_unit, multiplier) -> None:
        self.name = name
        self.unit_type = unit_type
        self.base_unit = base_unit
        self.multiplier = multiplier

    # op1 = (operator.neg, operator.truth)
    # op2_cmp = (operator.eq,)  # operator.lt)
    # op2_math = (operator.add, operator.sub, operator.mul, operator.truediv)

    def conversion_factor(self, target_unit: Unit) -> float:

        assert (
            self.unit_type == target_unit.unit_type
        ), f"Cannot convert between units of different types ({self.unit_type} != {target_unit.unit_type}"

        # convert to the base unit, then convert from that base unit to the new unit
        conversion_factor = self.multiplier * 1 / target_unit.multiplier
        return conversion_factor

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"<Unit('{self.name}')>"

    def __eq__(self, __o: object) -> bool:
        return (
            isinstance(__o, Unit)
            and self.name == __o.name
            and self.unit_type == __o.unit_type
            and self.base_unit == __o.base_unit
            and self.multiplier == __o.multiplier
        )

    def __mul__(self, __o: Union[Unit, ValidMagnitude]) -> Quantity:
        """Return a quantity using this unit"""

        # Return a compound unit
        if isinstance(__o, Unit):
            print(f"STUB: compound unit")

        # Create a Quantity
        return Quantity(__o, self)

    # TODO: this may need amending when compound units are a thing.
    __rmul__ = __mul__
