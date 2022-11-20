from __future__ import annotations
from typing import Union, Any
import math

import pintless.unit as plu


class Quantity:
    """
    Represents a value paired with a unit.  The value can be any python object, but is
    expected to be a numeric type (typically float, int, complex) that responds to the
    usual __add__, __mul__, etc.

    Quantity objects can be constructed by multiplying a python object by a Unit object.

    Quantity objects can have their values extracted using .magnitude(), and can be converted
    to new units using .to() or .ito().  This follows the API established by the pint library.
    """

    def __init__(self, magnitude: Any, unit: plu.Unit) -> None:

        if isinstance(unit, str):
            raise TypeError(
                "Cannot instantiate a Quantity object using a string expression as a unit: use the unit registry to do this instead."
            )

        self.magnitude = magnitude
        self.unit: plu.Unit = unit

    @property
    def units(self) -> plu.Unit:
        """Pint compatibliity property, simply returns self.unit"""
        return self.unit

    @property
    def dimensionality(self) -> str:
        return self.unit.unit_type

    def m_as(self, target_unit: Union[str, plu.Unit]) -> Any:
        """
        Return the magnitude of this Quantity as if it is the unit given.
        Marginally faster than .to('x').magnitude as no new Quantity object is created.

        The unit may be provided as a string ("m/s") or as a Unit type.

        If it is provided as a string, it cannot contain any numbers, e.g. "400 miles".
        This prevents subtle conversion issues, but is also simpler, thus faster.

        To perform these conversions you must convert the unit then multiply by the constant (i.e. 400).
        """
        if isinstance(target_unit, str):
            if self.unit.registry is None:
                raise ValueError(
                    "Cannot process string input for conversion if a registry is not linked to the units.  Set link_to_registry=True when creating units."
                )
            target_unit = self.unit.registry.get_unit(target_unit)

        # This might happen if someone passes in a string containing numbers
        if not isinstance(target_unit, plu.Unit):
            raise ValueError("Cannot convert to a non-unit type (this may happen if converting to a string expression with numbers in it)")

        conversion_factor = self.unit.conversion_factor(target_unit)
        if isinstance(self.magnitude, list):
            return [x * conversion_factor for x in self.magnitude]
        return self.magnitude * conversion_factor

    def to(self, target_unit: Union[str, plu.Unit]) -> Quantity:
        """Convert this Quantity to another unit"""
        if isinstance(target_unit, str):
            if self.unit.registry is None:
                raise ValueError(
                    "Cannot process string input for conversion if a registry is not linked to the units.  Set link_to_registry=True when creating units."
                )
            target_unit = self.unit.registry.get_unit(target_unit)

        # This might happen if someone passes in a string containing numbers
        if not isinstance(target_unit, plu.Unit):
            raise ValueError("Cannot convert to a non-unit type (this may happen if converting to a string expression with numbers in it)")

        conversion_factor = self.unit.conversion_factor(target_unit)
        if isinstance(self.magnitude, list):
            new_magnitude = [x * conversion_factor for x in self.magnitude]
        else:
            new_magnitude = self.magnitude * conversion_factor

        return Quantity(new_magnitude, target_unit)

    def ito(self, target_unit: Union[str, plu.Unit]) -> None:
        """In-place version of to"""
        if isinstance(target_unit, str):
            if self.unit.registry is None:
                raise ValueError(
                    "Cannot process string input for conversion if a registry is not linked to the units.  Set link_to_registry=True when creating units."
                )
            target_unit = self.unit.registry.get_unit(target_unit)

        self.magnitude *= self.unit.conversion_factor(target_unit)
        self.unit = target_unit

    # https://docs.python.org/3/reference/datamodel.html#emulating-numeric-types

    def __bool__(self) -> bool:
        # This is valid because this lib doesn't support non-0-centred values (e.g. Celsius, Farenheit)
        return self.magnitude.__bool__()

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Quantity):
            try:
                return (
                    self.magnitude == __o.magnitude and self.unit == __o.unit
                ) or self.to(__o.unit).magnitude == __o.magnitude
            except TypeError:
                return False

        if isinstance(__o, list) and isinstance(self.magnitude, list):
            return len(__o) == len(self.magnitude) and all(
                __o[i] == self[i] for i in range(len(__o))
            )

        # Special case at 0, since we are a multiplicative system
        if __o == 0 and self.magnitude == 0:
            return True

        # Else assume the other value is dimensionless
        return Quantity(__o, self.unit.dimensionless_unit) == self

    def __lt__(self, __o: object) -> bool:
        return isinstance(
            __o, Quantity
        ) and self.magnitude < __o.magnitude * self.unit.conversion_factor(__o.unit)

    def __add__(self, __o: object) -> Quantity:
        if not isinstance(__o, Quantity):

            if __o == 0:
                return self

            return self + Quantity(__o, self.unit.dimensionless_unit)

        if self.unit.unit_type != __o.unit.unit_type:
            raise TypeError(
                f"Cannot sum quantities of different dimensionalities: {self.unit.unit_type} != {__o.unit.unit_type}"
            )

        # Convert other unit to this unit, then create new Quantity
        return Quantity(
            self.magnitude + (__o.magnitude * __o.unit.conversion_factor(self.unit)),
            self.unit,
        )

    __radd__ = __add__

    def __sub__(self, __o: object) -> Quantity:
        if not isinstance(__o, Quantity):

            if __o == 0:
                return self

            return self - Quantity(__o, self.unit.dimensionless_unit)

        if self.unit.unit_type != __o.unit.unit_type:
            raise TypeError(
                f"Cannot subtract quantities of different dimensionalities: {self.unit.unit_type} != {__o.unit.unit_type}"
            )

        # Convert other unit to this unit, then create new Quantity
        return Quantity(
            self.magnitude - (__o.magnitude * __o.unit.conversion_factor(self.unit)),
            self.unit,
        )

    __rsub__ = __sub__

    def __neg__(self) -> Quantity:
        """Unary negation of the obect, as in -1"""
        return Quantity(-self.magnitude, self.unit)

    def __pos__(self) -> Quantity:
        """Unary positation of the obect, as in -1"""
        return Quantity(+self.magnitude, self.unit)

    def __abs__(self) -> Quantity:
        """Unary positation of the obect, as in -1"""
        return Quantity(abs(self.magnitude), self.unit)

    def __mul__(self, __o: object) -> Quantity:
        """Multiply the Quantity.  Outputs something with compound units"""
        # Someone is 'adding' units to this quantity
        if isinstance(__o, plu.Unit):
            return Quantity(self.magnitude, self.unit * __o)

        if not isinstance(__o, Quantity):
            # Assume it's a magnitude.  Maybe warn on this condition?
            __o = Quantity(__o, self.unit.dimensionless_unit)

        # Multiply a/b by b/c to get ab * bc.
        # This is a copy of the logic in Unit, in an effort to increase performance.
        new_numerators, new_denominators, conversion_factor = self.unit.simplify(
            self.unit.numerator_units + __o.unit.numerator_units,
            self.unit.denominator_units + __o.unit.denominator_units,
        )
        new_unit = plu.Unit(
            new_numerators,
            new_denominators,
            self.unit.dimensionless_base_unit,
            self.unit.registry,
        )

        if isinstance(self.magnitude, list):
            if isinstance(__o.magnitude, list):
                raise ValueError("Cannot multiply two list types")
            new_magnitude = [
                x * __o.magnitude * conversion_factor for x in self.magnitude
            ]
        else:
            new_magnitude = self.magnitude * __o.magnitude * conversion_factor

        return Quantity(new_magnitude, new_unit)

    __rmul__ = __mul__

    def __truediv__(self, __o: object) -> Quantity:
        """'true' division, where 2/3 is 0.66 rather than 0"""
        if not isinstance(__o, Quantity):
            if isinstance(__o, plu.Unit):
                __o = Quantity(1, __o)
            else:
                # Assume it's a magnitude.  Maybe warn on this condition?
                __o = Quantity(__o, self.unit.dimensionless_unit)

        # If this has a denominator, flip it and then multiply it using the other mult rules.
        # (a / b) / (c / d) == ad / bc
        new_numerators, new_denominators, conversion_factor = self.unit.simplify(
            self.unit.numerator_units + __o.unit.denominator_units,
            self.unit.denominator_units + __o.unit.numerator_units,
        )
        new_unit = plu.Unit(
            new_numerators,
            new_denominators,
            self.unit.dimensionless_base_unit,
            self.unit.registry,
        )

        if isinstance(self.magnitude, list):
            new_magnitude = [
                (x / __o.magnitude) * conversion_factor for x in self.magnitude
            ]
        else:
            new_magnitude = (self.magnitude / __o.magnitude) * conversion_factor

        return Quantity(new_magnitude, new_unit)

    def __iter__(self):
        class QuantityIterator:
            """
            An iterator that iterates over the magnitude, returning its values with the correct unit.

            This class is returned if iterating over a Quantity with a list-type magnitude
            """

            def __init__(self, unit: plu.Unit, iterator):
                self.unit = unit
                self.iterator = iterator

            def __iter__(self):
                return self.iterator

            def __next__(self):
                # skipcq: PTC-W0063
                return next(self.iterator) * self.unit

        return QuantityIterator(self.unit, iter(self.magnitude))

    def __getitem__(self, i: int) -> Quantity:
        return self.magnitude[i] * self.unit

    def __len__(self) -> int:
        return len(self.magnitude)

    def __ge__(self, __o) -> bool:
        if not isinstance(__o, Quantity):
            if __o == 0:
                return self.magnitude > 0
            raise TypeError(f"Cannot compare Quantity and '{type(__o)}'")
        return self.magnitude > __o.to(self.unit).magnitude

    def __invert__(self) -> Quantity:
        """Unary positation of the obect, as in -1"""
        return Quantity(~self.magnitude, self.unit)

    def __round__(self, ndigits=None):
        return Quantity(round(self.magnitude, ndigits), self.unit)

    def __trunc__(self):
        return Quantity(math.trunc(self.magnitude), self.unit)

    def __floor__(self):
        return Quantity(math.floor(self.magnitude), self.unit)

    def __ceil__(self):
        return Quantity(math.ceil(self.magnitude), self.unit)

    def __complex__(self) -> complex:
        """Return a complex number with the imaginary component as 0"""
        return complex(self.magnitude, 0)

    def __float__(self) -> float:
        return float(self.magnitude)

    def __int__(self) -> int:
        return int(self.magnitude)

    def __str__(self) -> str:
        return f"{self.magnitude} {self.unit.name}"

    def __repr__(self) -> str:
        return f"<Quantity({self.magnitude}, '{self.unit.name}')>"
