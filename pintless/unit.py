from __future__ import annotations
from typing import Union, List, Tuple

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

    __rmul__ = __mul__

    def __truediv__(self, __o: Unit) -> UnitDivision:
        """Dividing never produces a quantity, always another unit"""

        return UnitDivision(self, __o)


class UnitDivision(Unit):
    def __init__(self, numerator_unit, denominator_unit) -> None:

        assert not isinstance(numerator_unit, UnitDivision), "UnitDivision objects do not support UnitDivision objects as numerators or denominators: this should never happen unless the built-in arithmetic methods are not being used."
        assert not isinstance(denominator_unit, UnitDivision), "UnitDivision objects do not support UnitDivision objects as numerators or denominators: this should never happen unless the built-in arithmetic methods are not being used."

        self.numerator_unit = numerator_unit
        self.denominator_unit = denominator_unit
        self.name = f"{numerator_unit.name}/{denominator_unit.name}"
        self.unit_type = f"{numerator_unit.unit_type}/{denominator_unit.unit_type}"

    def simplify(self) -> Tuple[float, Unit]:
        """Cancel denominator and numerator units"""

        # Find list of unit types in numerator, and list in denominator, then cancel them.
        # Sort by unit type so we know we can match up
        units_in_numerator = self.numerator_unit.sorted_units if isinstance(self.numerator_unit, UnitProduct) else [self.numerator_unit]
        units_in_denominator = self.denominator_unit.sorted_units if isinstance(self.denominator_unit, UnitProduct) else [self.denominator_unit]
        new_denominator = []

        conversion_factor = 1
        for denom_unit in units_in_denominator:
            # Find a unit with the correct type in the numerator and cancel it.
            units_with_type = [u for u in units_in_numerator if u.unit_type == denom_unit.unit_type]
            if len(units_with_type) > 0:
                # TODO: calculate conversion factor
                unit_to_be_cancelled = units_with_type[0]
                units_in_numerator = [u for u in units_in_numerator if u != unit_to_be_cancelled]
                conversion_factor *= unit_to_be_cancelled.conversion_factor(denom_unit)
            else:
                new_denominator.append(denom_unit)

        # If denominator is empty, we should reduce down and output a simple UnitProduct or Unit obj.
        if len(new_denominator) == 0:
            if len(units_in_numerator) == 0:
                return conversion_factor, None
            if len(units_in_numerator) == 1:
                return conversion_factor, units_in_numerator[0]
            if len(units_in_numerator) > 1:
                return conversion_factor, UnitProduct(units_in_numerator)
        if len(new_denominator) == 1:
            if len(units_in_numerator) == 0:
                raise ValueError("Simplification cancelled everything from the numerator and I'm not sure what to do")
                # FIXME
            if len(units_in_numerator) == 1:
                return conversion_factor, UnitDivision(units_in_numerator[0], new_denominator[0])
            if len(units_in_numerator) > 1:
                return conversion_factor, UnitDivision(UnitProduct(units_in_numerator), new_denominator[0])

        # else len(new_denominator) > 1:
        if len(units_in_numerator) == 0:
            raise ValueError("Simplification cancelled everything from the numerator and I'm not sure what to do")
            # FIXME
        if len(units_in_numerator) == 1:
            return conversion_factor, UnitDivision(units_in_numerator[0], UnitProduct(new_denominator))
        if len(units_in_numerator) > 1:
            return conversion_factor, UnitDivision(UnitProduct(units_in_numerator), UnitProduct(new_denominator))

    def conversion_factor(self, target_unit: Unit) -> float:

        assert isinstance(
            target_unit, UnitDivision
        ), f"Cannot convert between units of different types: {self.unit_type} != {target_unit}"
        assert (
            self.unit_type == target_unit.unit_type
        ), f"Cannot convert between units of different types: {self.unit_type} != {target_unit.unit_type}"

        conversion_factor = self.numerator_unit.conversion_factor(
            target_unit.numerator_unit
        ) / self.denominator_unit.conversion_factor(target_unit.denominator_unit)

        return conversion_factor

    def __eq__(self, __o: object) -> bool:
        return (
            isinstance(__o, UnitDivision)
            and self.numerator_unit == __o.numerator_unit
            and self.denominator_unit == __o.denominator_unit
        )

    def __mul__(self, __o: Union[Unit, ValidMagnitude]) -> Union[Unit, Quantity]:
        """Return a quantity using this unit"""

        # If this is also a divided unit then the denominator has to have the same
        # unit types in it
        if isinstance(__o, UnitDivision):
            return UnitDivision(
                self.numerator_unit * __o.numerator_unit,
                self.denominator_unit * __o.denominator_unit,
            )

        # Denominator is 1 here so we multiply the numerator: 2*1/3 = 2/3
        if isinstance(__o, Unit) or isinstance(__o, UnitProduct):
            return UnitDivision(self.numerator_unit * __o, self.denominator_unit)

        # Create a Quantity with this type
        return Quantity(__o, self)

    __rmul__ = __mul__

    def __truediv__(self, __o: Unit) -> Union[None, Unit, UnitProduct]:
        """Divide these units by other units"""

        # If this has a denominator, flip it and then multiply it using the other mult rules.
        # (a / b) / (c / d) == ad / bc
        if isinstance(__o, UnitDivision):
            return UnitDivision(
                self.numerator_unit * __o.denominator_unit,
                self.denominator_unit * __o.numerator_unit,
            )

        # If we're dividing by a non-divided quantity we don't have a denominator,
        # it's essentially 1: 1/3 / 2 is 1/(2*3)
        return UnitDivision(self.numerator_unit, self.denominator_unit * __o)


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
        assert isinstance(
            target_unit, UnitProduct
        ), f"Cannot convert between units of different types: {self.sorted_unit_types} != {target_unit})"
        assert (
            self.sorted_unit_types == target_unit.sorted_unit_types
        ), f"Cannot convert between units with different base types ({self.sorted_unit_types} != {target_unit.sorted_unit_types})"

        # convert to the base unit, then convert from that base unit to the new unit
        conversion_factor = 1
        for unit_from, unit_to in zip(self.sorted_units, target_unit.sorted_units):
            conversion_factor *= unit_from.conversion_factor(unit_to)

        return conversion_factor

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, UnitProduct) and all(
            [a == b for a, b in zip(self.sorted_units, __o.sorted_units)]
        )

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

    __rmul__ = __mul__

    def __truediv__(self, __o: Unit) -> Union[None, Unit, UnitProduct]:

        return UnitDivision(self, __o)
