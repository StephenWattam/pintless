from __future__ import annotations
from typing import Union, List

from .quantity import Quantity

ValidMagnitude = Union[int, float, complex]


class Unit:
    def __init__(self, name, unit_type, base_unit, multiplier) -> None:
        self.name = name
        self.unit_type = unit_type
        self.base_unit = base_unit
        self.multiplier = multiplier

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

    def __mul__(self, __o: Union[Unit, ValidMagnitude]) -> Union[Unit, Quantity]:
        """Return a quantity using this unit"""

        # Return a compound unit
        if isinstance(__o, Unit):
            return UnitProduct([self, __o])

        # Create a Quantity
        return Quantity(__o, self)

    # TODO: this may need amending when compound units are a thing.
    __rmul__ = __mul__



class UnitProduct(Unit):
    """Represent units that have been multiplied together,
    e.g. kilowatt-hour.

    Because multiplication is symmetric the order doesn't
    matter when computing conversions"""

    def __init__(self, units: List[Unit]) -> None:

        self.sorted_units = sorted(units, key=lambda u: u.unit_type)
        self.sorted_unit_types = [u.unit_type for u in self.sorted_units]
        self.name = "*".join([u.name for u in self.sorted_units])
        self.unit_type = "*".join(self.sorted_unit_types)

    def conversion_factor(self, target_unit: Unit) -> float:

        # The other unit must be of the same unit type, which means a product of the same
        # unit types.
        assert isinstance(target_unit, UnitProduct), f"Cannot convert between units of different types: {self.sorted_unit_types} != {target_unit})"
        assert self.sorted_unit_types == target_unit.sorted_unit_types, f"Cannot convert between units with different base types ({self.sorted_unit_types} != {target_unit.sorted_unit_types})"

        # convert to the base unit, then convert from that base unit to the new unit
        conversion_factor = 1
        for unit_from, unit_to in zip(self.sorted_units, target_unit.sorted_units):
            conversion_factor *= unit_from.conversion_factor(unit_to)

        return conversion_factor

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, UnitProduct) and all([a == b for a, b in zip(self.sorted_units, __o.sorted_units)])

    def __mul__(self, __o: Union[Unit, ValidMagnitude]) -> Union[Unit, Quantity]:
        """Return a quantity using this unit"""

        # Return a compound unit
        if isinstance(__o, UnitProduct):
            return UnitProduct(self.sorted_units + __o.sorted_units)

        # Return a compound unit
        if isinstance(__o, Unit):
            return UnitProduct(self.sorted_units + [__o])

        # Create a Quantity
        return Quantity(__o, self)

    # TODO: this may need amending when compound units are a thing.
    __rmul__ = __mul__


    def __div__(self, __o: Union[Unit, UnitProduct]) -> Union[None, Unit, UnitProduct]:


        return UnitDivision(self, __o)


        # # Cancel these out if possible
        #     denominator_unit_types = __o.sorted_unit_types
        # if isinstance(__o, Unit):
        #     denominator_unit_types = [__o.unit_type]

        # # We now have a list of what to remove, so remove it one-by-one if it's there
        # remaining_units = [u for u in self.sorted_units if u not in denominator_unit_types]


        # if isinstance(__o, Unit):
        #     # Remove the unit's base type if it's in, else divide this type by the base type
        #     if __o.unit_type in self.sorted_unit_types:
        #         if len(remaining_units) == 0:
        #             return None  # No unit!
        #         if len(remaining_units) == 1:
        #             return remaining_units[0]
        #         return UnitProduct(remaining_units)
