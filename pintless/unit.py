from __future__ import annotations
from typing import Union, List, Tuple, Optional

from .quantity import Quantity

ValidMagnitude = Union[int, float, complex]
Numeric = Union[int, float]


class BaseUnit:
    """A simple unit type that contains:

     - A unit (e.g. millimeter), and a dimension (e.g. length).
     - A base unit (e.g. meter) and a multiplier to convert from this unit into that base unit.
     - A reference to the dimensionless unit

     This represents _part of_ a unit in the system: a full unit expression could be something that
     combines these building blocks using multiplication and division, e.g. ms/hour
     (i.e. meters * seconds / hours).
    """

    def __init__(self, name: str, unit_type: str, base_unit: str, multiplier: Numeric) -> None:
        self.name = name
        self.unit_type = unit_type
        self.base_unit = base_unit
        self.multiplier = multiplier

    def conversion_factor(self, target_unit: BaseUnit, dimensionless_unit: BaseUnit) -> float:

        if self.unit_type == dimensionless_unit.unit_type or target_unit.unit_type == dimensionless_unit.unit_type:
            return 1

        assert (
            self.unit_type == target_unit.unit_type
        ), f"Cannot convert between units of different types ({self.unit_type} != {target_unit.unit_type}"

        # convert to the base unit, then convert from that base unit to the new unit
        conversion_factor = self.multiplier * 1 / target_unit.multiplier
        return conversion_factor

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"<BaseUnit('{self.name}')>"

    def __eq__(self, __o: object) -> bool:
        return (
            isinstance(__o, Unit)
            and self.name == __o.name
            and self.unit_type == __o.unit_type
            and self.base_unit == __o.base_unit
            and self.multiplier == __o.multiplier
        )


class Unit:
    def __init__(self, numerator_units: List[BaseUnit], denominator_units: List[BaseUnit], dimensionless_base_unit: BaseUnit) -> None:

        self.dimensionless_base_unit = dimensionless_base_unit

        if len(numerator_units) == 0 and len(denominator_units) == 0:
            self.dimensionless_unit = self
        else:
            self.dimensionless_unit = Unit([], [], self.dimensionless_base_unit)

        # Remove dimensionless units.
        numerator_units = [u for u in numerator_units if u.unit_type != self.dimensionless_base_unit.unit_type]
        denominator_units = [u for u in denominator_units if u.unit_type != self.dimensionless_base_unit.unit_type]

        if len(numerator_units) == 0:
            numerator_units = [self.dimensionless_base_unit]
        if len(denominator_units) == 0:
            denominator_units = [self.dimensionless_base_unit]

        self.numerator_units: List[BaseUnit] = sorted(numerator_units, key=lambda u: u.unit_type)
        self.denominator_units: List[BaseUnit] = sorted(denominator_units, key=lambda u: u.unit_type)
        self.numerator_unit_types = [u.unit_type for u in self.numerator_units]
        self.denominator_unit_types = [u.unit_type for u in self.numerator_units]
        self.unit_type = f"{'*'.join([u.unit_type for u in self.numerator_units])}/{'*'.join([u.unit_type for u in self.denominator_units])}"

        # Generate name
        self.name = f"{'*'.join([u.name for u in self.numerator_units])}"
        if not all([u.unit_type == self.dimensionless_base_unit.unit_type for u in self.denominator_units]):
            self.name += f"/{'*'.join([u.name for u in self.denominator_units])}"

    def simplify(self) -> Tuple[float, Unit]:
        """Cancel denominator and numerator units"""

        def first_index(lst, unit_type: str):
            for i, u in enumerate(lst):
                if u.unit_type == unit_type:
                    return i
            return None

        # Find list of unit types in numerator, and list in denominator, then cancel them.
        # Sort by unit type so we know we can match up
        new_numerator: List[BaseUnit] = [u for u in self.numerator_units if u.unit_type != self.dimensionless_base_unit.unit_type]
        new_denominator = []

        conversion_factor = 1
        for denom_unit in self.denominator_units:
            # Find a unit with the correct type in the numerator and cancel it.
            index_to_cancel = first_index(new_numerator, denom_unit.unit_type)
            if index_to_cancel is not None:
                conversion_factor *= new_numerator[index_to_cancel].conversion_factor(denom_unit, self.dimensionless_base_unit)
                del new_numerator[index_to_cancel]
            else:
                new_denominator.append(denom_unit)

        # Special case where we have x/x remaining
        if len(new_numerator) == len(new_denominator) and all([a.unit_type == b.unit_type for a, b in zip(new_numerator, new_denominator)]):
            return conversion_factor, self.dimensionless_unit

        return conversion_factor, Unit(new_numerator, new_denominator, self.dimensionless_base_unit)

    def __str__(self) -> str:
        return f"<Unit ({self.name})>"

    def conversion_factor(self, target_unit: Unit) -> float:

        assert isinstance(
            target_unit, Unit
        ), f"Cannot compute conversion factor between unit and non-unit values"

        assert self.numerator_unit_types == target_unit.numerator_unit_types, f"Numerator types for object a ({self.numerator_unit_types}) do not match numerator types for object b ({target_unit.numerator_unit_types})"
        assert self.denominator_unit_types == target_unit.denominator_unit_types, f"Numerator types for object a ({self.denominator_unit_types}) do not match denominator types for object b ({target_unit.denominator_unit_types})"

        # Conversion factor for the numerator
        numerator_conversion_factor = 1
        for base_unit_from, base_unit_to in zip(self.numerator_units, target_unit.numerator_units):
            numerator_conversion_factor *= base_unit_from.conversion_factor(base_unit_to, self.dimensionless_base_unit)

        # Conversion factor for all the multiplied denominator items
        denominator_conversion_factor = 1
        for base_unit_from, base_unit_to in zip(self.denominator_units, target_unit.numerator_units):
            denominator_conversion_factor *= base_unit_from.conversion_factor(base_unit_to, self.dimensionless_base_unit)

        conversion_factor = numerator_conversion_factor / denominator_conversion_factor

        return conversion_factor

    def __eq__(self, __o: object) -> bool:
        return (
            isinstance(__o, Unit)
            and self.numerator_units == __o.numerator_units
            and self.denominator_units == __o.denominator_units
        )

    def __mul__(self, __o: Union[Unit, ValidMagnitude]) -> Union[Unit, Quantity]:
        """Return a quantity using this unit"""

        # If this is also a divided unit then the denominator has to have the same
        # unit types in it
        if isinstance(__o, Unit):
            # Multiply a/b by b/c to get ab * bc.
            # This means concatenating the lists, but ensuring there's only ever one 'dimensionless'

            new_numerators = self.numerator_units + __o.numerator_units
            new_denominators = self.denominator_units + __o.denominator_units

            # Filter out double dimensionless: dimensionless * dimensionless == dimensionless
            new_numerators = [u for u in new_numerators if u.unit_type != self.dimensionless_base_unit.unit_type]
            new_denominators = [u for u in new_denominators if u.unit_type != self.dimensionless_base_unit.unit_type]#: + [self.dimensionless_unit]


            return Unit(new_numerators, new_denominators, self.dimensionless_base_unit)

        # Must be some other (presumably numeric) quantity
        return Quantity(__o, self)

    __rmul__ = __mul__

    def __truediv__(self, __o: Unit) -> Union[None, Unit, UnitProduct]:
        """Divide these units by other units"""

        assert isinstance(__o, Unit), "Cannot divide unit by non-unit"

        # If this has a denominator, flip it and then multiply it using the other mult rules.
        # (a / b) / (c / d) == ad / bc

        new_numerators = self.numerator_units + __o.denominator_units
        new_denominators = self.denominator_units + __o.numerator_units

        # TODO: filter out double dimensionless: dimensionless * dimensionless == dimensionless

        return Unit(new_numerators, new_denominators, self.dimensionless_base_unit)
