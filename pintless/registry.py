import os
import json
from functools import lru_cache
from .unit import BaseUnit, Unit
import logging
from typing import Optional, Any, Union
import pintless.quantity
import pintless.errors as errors

DEFAULT_DEFINITION_FILE = "default_units.json"
PREFIX_KEY = "__prefixes__"
DIMENSIONLESS_UNIT_NAME = "dimensionless"
MULTIPLY_TOKEN = "__multiply__"
DIVIDE_TOKEN = "__divide__"

logging.basicConfig()
log = logging.getLogger()


class Registry:

    Quantity = pintless.quantity.Quantity

    def __init__(
        self, definition_filename: Optional[str] = None, link_to_registry: bool = True
    ):

        self.link_to_registry = link_to_registry

        if definition_filename is None:
            definition_filename = (
                os.path.dirname(os.path.realpath(__file__))
                + os.sep
                + DEFAULT_DEFINITION_FILE
            )

        # Read definitions from file
        log.debug("Reading unit definitions from %s", definition_filename)
        with open(definition_filename) as fin:
            defs = json.load(fin)

        # Assign definitions to various categories, and support forward/reverse lookup
        # by unit type
        self.units = set()
        self.base_type_for_utype = {}
        self.units_for_utype = {}
        self.utype_for_unit = {}
        self.derived_types = {}

        # Read prefixes then process them later
        prefixes = defs[PREFIX_KEY]
        del defs[PREFIX_KEY]

        for utype, units in defs.items():

            # Create a forward index for the unit type
            utype = f"[{utype}]"  # XXX: pint types have brackets.
            self.units_for_utype[utype] = {}

            # For every unit, for every prefix, calculate a multiplier down to the 'base unit'
            # for that unit type
            for unit_name, multiplier in units.items():

                # The first entry in the dict is the base type
                if utype not in self.base_type_for_utype:
                    self.base_type_for_utype[utype] = unit_name

                # handle compound types
                if isinstance(multiplier, dict):
                    assert (
                        "numerator" in multiplier or "denominator" in multiplier
                    ), f"Missing numerator and/or denominator list for derived type '{unit_name}'"

                    numerator_list = (
                        multiplier["numerator"]
                        if "numerator" in multiplier
                        else [DIMENSIONLESS_UNIT_NAME]
                    )
                    denominator_list = (
                        multiplier["denominator"]
                        if "denominator" in multiplier
                        else [DIMENSIONLESS_UNIT_NAME]
                    )

                    for prefix, prefix_multiplier in prefixes.items():
                        self.derived_types[prefix + unit_name] = (
                            [prefix + numerator_list[0]] + numerator_list[1:],
                            denominator_list,
                        )
                        if prefix + unit_name in self.units:
                            log.warn(
                                "Detected duplicate unit in unit definition: %s",
                                prefix + unit_name,
                            )
                        log.debug(
                            "Adding derived type for unit: %s", prefix + unit_name
                        )
                        self.units.add(prefix + unit_name)
                    continue

                # and all prefix forms
                for prefix, prefix_multiplier in prefixes.items():
                    self.units_for_utype[utype][prefix + unit_name] = (
                        prefix_multiplier * multiplier
                    )
                    self.utype_for_unit[prefix + unit_name] = utype
                    if prefix + unit_name in self.units:
                        log.warn(
                            "Detected duplicate unit in unit definition: %s",
                            prefix + unit_name,
                        )
                    log.debug(
                        "Adding non-derived type for unit: %s of unit type %s",
                        prefix + unit_name,
                        utype,
                    )
                    self.units.add(prefix + unit_name)

            # Check we have a base unit for the unit type
            assert (
                utype in self.base_type_for_utype
            ), f"No base unit defined for unit type {utype}"

        assert (
            DIMENSIONLESS_UNIT_NAME in self.units
        ), f"A unit with name '{DIMENSIONLESS_UNIT_NAME}' must be defined"

        self.dimensionless_unit = Unit([], [], self._get_base_unit(DIMENSIONLESS_UNIT_NAME),
            self if self.link_to_registry else None,
            None
        )

        # Define the "multiply method" on this registry
        for unit_name in self.units:
            setattr(self, unit_name, self.get_unit(unit_name))

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        assert len(args) == 1
        assert len(kwds) == 0

        return self.get_unit(args[0])

    @lru_cache
    def get_unit(self, unit_name: str, support_expressions: bool = True) -> Union[Unit, pintless.quantity.Quantity]:
        """Return a Unit for a given type.  The unit will not have a value attached
        as it would in a Quantity object.

        Supports basic expressions of types of the form x/y where x and y are a list
        of units separated by multiplication symbols or spaces:

            m s / seconds
            kilowatt / hour
            second * second
            hour * watt * Hz

        """

        if unit_name not in self.units:
            # We may have a unit that is an expression.

            if support_expressions:
                return self._parse_unit_expression(unit_name)
            else:
                raise errors.UndefinedUnitError(f"Unit '{unit_name}' not round in registry")

        # Load either a derived type or a basic type
        if unit_name in self.derived_types:
            numerator_unit_list, denominator_unit_list = self.derived_types[unit_name]
        else:
            numerator_unit_list = [unit_name]
            denominator_unit_list = [DIMENSIONLESS_UNIT_NAME]

        return Unit(
            [self._get_base_unit(u) for u in numerator_unit_list],
            [self._get_base_unit(u) for u in denominator_unit_list],
            self._get_base_unit(DIMENSIONLESS_UNIT_NAME),
            self if self.link_to_registry else None,
            self.dimensionless_unit,
            unit_name
        )

    @lru_cache
    def _get_base_unit(self, base_unit_name: str) -> BaseUnit:
        """Return a simple base unit type.  Used to construct units."""

        if base_unit_name in self.derived_types:
            raise ValueError(f"Cannot instantiate base unit '{base_unit_name}', as it is a derived type")

        # Base case, the unit itself
        unit_type = self.utype_for_unit[base_unit_name]
        base_type = self.base_type_for_utype[unit_type]
        multiplier = self.units_for_utype[unit_type][base_unit_name]

        return BaseUnit(base_unit_name, unit_type, base_type, multiplier)

    def _parse_unit_expression(self, unit_expr: str) -> Union[Unit, pintless.quantity.Quantity]:
        """Parse an expression containing the following tokens:

         - unit name (any string without spaces)
         - *, to multiply units
         - /, to divide units
         - ' ' (a space), to multiply units

        Because we are dealing with multiply and divide operations only,
        the need to resolve a full parse tree isn't there: we can simply
        walk through the operations left-to-right.
        """

        def type_for_token(token: str):
            if token == "*" or token == "":
                return MULTIPLY_TOKEN
            if token == "/":
                return DIVIDE_TOKEN
            if token in self.units:
                return self.get_unit(token, support_expressions=False)
            else:
                try:
                    return pintless.quantity.Quantity(float(token), self.dimensionless_unit)
                except ValueError:
                    raise errors.UndefinedUnitError(f"Unit '{token}' not found in registry")

        # Replace * and / with whitespace separated versions, then split on whitespace.
        # Saves use of regex libs
        unit_expr = unit_expr.replace("*", " * ").replace("/", " / ")
        parts = unit_expr.split()
        parts = [type_for_token(s.strip()) for s in parts]
        log.debug("Parsed expression into component parts: %s", parts)

        # Empty expressions are dimensionless
        if len(parts) == 0:
            return self.get_unit(DIMENSIONLESS_UNIT_NAME)

        assert isinstance(parts[0], (pintless.quantity.Quantity, Unit)), "Expressions must start with a unit name or quantity"
        assert isinstance(parts[-1], (pintless.quantity.Quantity, Unit)), "Expressions must end with a unit name or quantity"

        # Because we apply operations left-to-right, we will bundle them into pairs
        # giving [(operation, unit)]
        #
        # Iterate through and, when we have both of these, put them in the list.
        operations = []
        current_op = None
        for i, part in enumerate(parts[1:]):
            if part == MULTIPLY_TOKEN:
                if current_op is not None:
                    raise ValueError(
                        f"Repeated multiplication token in expression token {i+2}: {part}"
                    )
                current_op = MULTIPLY_TOKEN
            elif part == DIVIDE_TOKEN:
                if current_op is not None:
                    raise ValueError(
                        f"Repeated division token in expression token {i+2}: {part}"
                    )
                current_op = DIVIDE_TOKEN
            elif isinstance(part, (pintless.quantity.Quantity, Unit)):
                if current_op is not None:
                    operations.append((current_op, part))
                    current_op = None
                else:
                    # two units following one another is multiplication, not a problem
                    operations.append((MULTIPLY_TOKEN, part))
            else:
                raise ValueError(
                    f"Unrecognised token in expression token {i+2}: {part}"
                )

        log.debug("Performing operations: %s", operations)

        # Now apply operations
        current_value: Unit = parts[0]
        for operation, operand in operations:
            assert operation in [MULTIPLY_TOKEN, DIVIDE_TOKEN]
            assert isinstance(operand, (pintless.quantity.Quantity, Unit))

            if operation == MULTIPLY_TOKEN:
                current_value = current_value * operand
            elif operation == DIVIDE_TOKEN:
                current_value = current_value / operand

        return current_value
