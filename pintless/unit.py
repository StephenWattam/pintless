from __future__ import annotations
from typing import Union, List, Tuple, Optional
from functools import lru_cache

from .quantity import Quantity
import pintless.registry

ValidMagnitude = Union[int, float, complex]
Numeric = Union[int, float]


class BaseUnit:
    """
    A simple unit type that contains:

    - A unit (e.g. millimeter), and a dimension (e.g. length).
    - A base unit (e.g. meter) and a multiplier to convert from this unit into that base unit.
    - A reference to the dimensionless unit

    This represents _part of_ a unit in the system: a full unit expression could be something that
    combines these building blocks using multiplication and division, e.g. ms/hour
    (i.e. meters * seconds / hours).
    """

    def __init__(
        self, name: str, unit_type: str, base_unit: str, multiplier: Numeric
    ) -> None:
        self.name = name
        self.unit_type = unit_type
        self.base_unit = base_unit
        self.multiplier = multiplier

    def conversion_factor(self, target_unit: BaseUnit) -> float:
        """Return k such that a value in this unit * k = a value in target_unit."""

        if self.unit_type != target_unit.unit_type:
            raise TypeError(
                f"Cannot convert between units of different types ({self.unit_type} != {target_unit.unit_type}"
            )

        # convert to the base unit, then convert from that base unit to the new unit
        conversion_factor = self.multiplier * 1 / target_unit.multiplier
        return conversion_factor

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"<BaseUnit('{self.name} = {self.multiplier} * {self.base_unit}')>"

    def __hash__(self) -> int:
        return hash((self.name, self.unit_type, self.base_unit, self.multiplier))

    def __eq__(self, __o: object) -> bool:
        """Units are the same if their multiplier, base unit, and dimension are the same."""
        return (
            isinstance(__o, BaseUnit)
            and self.unit_type == __o.unit_type
            and self.base_unit == __o.base_unit
            and self.multiplier == __o.multiplier
        )


class Unit:
    """
    The main representation of a unit within Pintless.

    Multiplying an object by a instance of this class will produce a Quantity,
    assigning the unit to the value therein so that arithmetic can be performed
    on the value and the unit combined.

    Performing arithmetic operations on another Unit instance will result in the types
    that would result with value calculations, e.g. m/s divided by s == m.
    """

    def __init__(
        self,
        numerator_units: List[BaseUnit],
        denominator_units: List[BaseUnit],
        dimensionless_base_unit: BaseUnit,
        registry: Optional[pintless.registry.Registry],
        dimensionless_unit: Optional[Unit] = None,
        alias: Optional[str] = None,
    ) -> None:

        self.registry = registry
        self.dimensionless_base_unit = dimensionless_base_unit

        if len(numerator_units) == 0 and len(denominator_units) == 0:
            self.dimensionless_unit = self
        elif dimensionless_unit is not None:
            # Use arg if provided: this is an optimisation to share references
            # to the dimensionless unit
            self.dimensionless_unit = dimensionless_unit
        else:
            # Else create a new one.
            self.dimensionless_unit = Unit(
                [], [], self.dimensionless_base_unit, self.registry
            )

        self.numerator_units = numerator_units
        self.denominator_units = denominator_units

        if len(self.numerator_units) == 0:
            self.numerator_units = [self.dimensionless_base_unit]
        if len(self.denominator_units) == 0:
            self.denominator_units = [self.dimensionless_base_unit]

        self._numerator_unit_types = None
        self._denominator_unit_types = None
        self._unit_type = None

        # If this is None, it will be generated on first access
        self._name = alias

    @property
    def numerator_unit_types(self) -> Tuple[str]:
        if self._numerator_unit_types is not None:
            return self._numerator_unit_types

        self._numerator_unit_types = tuple(u.unit_type for u in self.numerator_units)
        return self._numerator_unit_types

    @property
    def denominator_unit_types(self) -> Tuple[str]:
        if self._denominator_unit_types is not None:
            return self._denominator_unit_types

        self._denominator_unit_types = tuple(
            u.unit_type for u in self.denominator_units
        )
        return self._denominator_unit_types

    @property
    def unit_type(self) -> str:
        if self._unit_type is not None:
            return self._unit_type

        self._unit_type = f"{'*'.join(self.numerator_unit_types)}/{'*'.join(self.denominator_unit_types)}"
        return self._unit_type

    @property
    def name(self) -> str:
        """
        Return the name of this unit.

        Generating this on instantiation costs performance, so this is computed on first call
        and cached.
        """
        if self._name is not None:
            return self._name

        self._name = f"{'*'.join(u.name for u in self.numerator_units)}"

        # If we have denominators
        if not all(
            u.unit_type == self.dimensionless_base_unit.unit_type
            for u in self.denominator_units
        ):

            if len(self.numerator_units) > 1:
                self._name = f"({self._name})"

            denom_name = "*".join(u.name for u in self.denominator_units)
            if len(self.denominator_units) > 1:
                denom_name = f"({denom_name})"
            self._name += f"/{denom_name}"

        return self._name

    def simplify(
        self, numerator_units: List[BaseUnit], denominator_units: List[BaseUnit]
    ) -> Tuple[List[BaseUnit], List[BaseUnit], float]:
        """
        Cancel denominator and numerator units, resulting in the simplest
        possible representation of the unit.  This is executed after multiplication
        or division to ensure that the resulting unit is sane and useful.

        Simplifying types may change units, resulting in a value change.  Because of this
        the method returns two items: a conversion factor that operates in the same way
        as .conversion_factor(), and the resulting Unit instance itself.
        """
        def first_index(lst: List[BaseUnit], unit_type: str) -> Optional[int]:
            """Return the index of the first item out of lst that is of the unit type unit_type"""
            for i, u in enumerate(lst):
                if u.unit_type == unit_type:
                    return i
            return None

        # Remove dimensionless units.
        numerator_units = [
            u
            for u in numerator_units
            if not (
                u.unit_type == self.dimensionless_base_unit.unit_type
                and u.multiplier == 1
            )
        ]
        denominator_units = [
            u
            for u in denominator_units
            if not (
                u.unit_type == self.dimensionless_base_unit.unit_type
                and u.multiplier == 1
            )
        ]

        numerator_units = sorted(numerator_units, key=lambda u: u.unit_type)
        denominator_units = sorted(denominator_units, key=lambda u: u.unit_type)

        # Find list of unit types in numerator, and list in denominator, then cancel them.
        # Sort by unit type so we know we can match up
        new_numerator: List[BaseUnit] = [
            u
            for u in numerator_units
            if u.unit_type != self.dimensionless_base_unit.unit_type
        ]
        new_denominator = []

        conversion_factor = 1
        for denom_unit in denominator_units:
            # Find a unit with the correct type in the numerator and cancel it.
            index_to_cancel = first_index(new_numerator, denom_unit.unit_type)
            if index_to_cancel is not None:
                conversion_factor *= new_numerator[index_to_cancel].conversion_factor(denom_unit)
                del new_numerator[index_to_cancel]
            else:
                new_denominator.append(denom_unit)

        # Special case where we have x/x remaining
        if len(new_numerator) == len(new_denominator) and all(
            a.unit_type == b.unit_type for a, b in zip(new_numerator, new_denominator)
        ):
            return [], [], conversion_factor

        return new_numerator, new_denominator, conversion_factor

    def __repr__(self) -> str:
        return f"<Unit ({self.name})>"

    def __str__(self) -> str:
        return self.name

    def conversion_factor(self, target_unit: Unit) -> float:
        """
        Calculate the ratio of the size of a value in the target unit relative
        to this unit.

        If you have a value in the current unit and wish to know how much larger it should
        be in the target unit, call this method and multiply the value by the result.

        This method is used by Quantity() to update values.
        """
        if not isinstance(target_unit, Unit):
            raise TypeError(
                "Cannot compute conversion factor between unit and non-unit values"
            )
        if self.unit_type != target_unit.unit_type:
            raise TypeError(
                f"Unable to convert from {self} to {target_unit} as they are defined in different dimensions"
            )

        # Conversion factor for the numerator
        numerator_conversion_factor = 1
        for base_unit_from, base_unit_to in zip(
            self.numerator_units, target_unit.numerator_units
        ):
            numerator_conversion_factor *= base_unit_from.conversion_factor(base_unit_to)

        # Conversion factor for all the multiplied denominator items
        denominator_conversion_factor = 1
        for base_unit_from, base_unit_to in zip(
            self.denominator_units, target_unit.denominator_units
        ):
            denominator_conversion_factor *= base_unit_from.conversion_factor(base_unit_to)

        conversion_factor = numerator_conversion_factor / denominator_conversion_factor

        return conversion_factor

    def __eq__(self, __o: object) -> bool:

        if (
            not isinstance(__o, Unit)
            or len(self.numerator_units) != len(__o.numerator_units)
            or len(self.denominator_units) != len(__o.denominator_units)
        ):
            return False

        for a, b in zip(self.numerator_units, __o.numerator_units):
            if a != b:
                return False
        for a, b in zip(self.denominator_units, __o.denominator_units):
            if a != b:
                return False

        return True

    def compatible_with(self, other: Unit) -> bool:
        """
        Returns true if both units have the same dimensionality, e.g. if it is
        possible to convert a quantity from this unit into the unit in 'other' or not.
        """
        return self.unit_type == other.unit_type

    # Set operations make this expensive, so cache the response
    @lru_cache
    def __hash__(self) -> int:
        return hash((set(self.numerator_units), set(self.denominator_units)))

    def __mul__(
        self, __o: Union[Unit, ValidMagnitude, Quantity]
    ) -> Union[Unit, Quantity]:
        """Return a quantity using this unit"""

        # If this is also a divided unit then the denominator has to have the same
        # unit types in it
        if isinstance(__o, Unit):
            # Multiply a/b by b/c to get ab * bc.
            # This means concatenating the lists, but ensuring there's only ever one 'dimensionless'

            new_numerators, new_denominators, _ = self.simplify(
                self.numerator_units + __o.numerator_units,
                self.denominator_units + __o.denominator_units,
            )

            return Unit(
                new_numerators,
                new_denominators,
                self.dimensionless_base_unit,
                self.registry,
            )

        if isinstance(__o, Quantity):
            return __o * self

        # Must be some other (presumably numeric) quantity
        return Quantity(__o, self)

    __rmul__ = __mul__

    def __pow__(self, __o: int) -> Union[Unit, Quantity]:
        val = self
        for _ in range(__o - 1):
            val = val * self
        return val

    def __truediv__(self, __o: Unit) -> Unit:
        """Divide these units by other units"""
        if not isinstance(__o, Unit):
            raise ValueError("Cannot divide unit by non-unit")

        # If this has a denominator, flip it and then multiply it using the other mult rules.
        # (a / b) / (c / d) == ad / bc

        new_numerators, new_denominators, _ = self.simplify(
            self.numerator_units + __o.denominator_units,
            self.denominator_units + __o.numerator_units,
        )

        return Unit(
            new_numerators,
            new_denominators,
            self.dimensionless_base_unit,
            self.registry,
        )
