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
OPEN_EXPR_TOKEN = "__start_expr__"
CLOSE_EXPR_TOKEN = "__end_expr__"

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
         - '(' and ')', to define order of operation

        Because we are dealing with multiply and divide operations only,
        the need to resolve a full parse tree isn't there: we can simply
        walk through the operations left-to-right.
        """

        def type_for_token(token: str):
            if token == "*" or token == "":
                return MULTIPLY_TOKEN
            if token == "/":
                return DIVIDE_TOKEN
            if token == "(":
                return OPEN_EXPR_TOKEN
            if token == ")":
                return CLOSE_EXPR_TOKEN
            if token in self.units:
                return self.get_unit(token, support_expressions=False)
            else:
                try:
                    return pintless.quantity.Quantity(float(token), self.dimensionless_unit)
                except ValueError:
                    raise errors.UndefinedUnitError(f"Unit '{token}' not found in registry")

        # Replace * and / with whitespace separated versions, then split on whitespace.
        # Saves use of regex libs
        unit_expr = unit_expr.replace("*", " * ").replace("/", " / ").replace("(", " ( ").replace(")", " ) ")
        parts = unit_expr.split()
        parts = [type_for_token(s.strip()) for s in parts]
        log.debug("Parsed expression into component parts: %s", parts)

        # Empty expressions are dimensionless
        if len(parts) == 0:
            return self.get_unit(DIMENSIONLESS_UNIT_NAME)

        # Implicit multiplication --- insert multiplication tokens between any tokens that don't
        # currently have them
        new_parts = []
        for a, b in zip(parts[:-1], parts[1:]):
            new_parts.append(a)

            # already there, get skipped
            if a == MULTIPLY_TOKEN or b == MULTIPLY_TOKEN or a == DIVIDE_TOKEN or b == DIVIDE_TOKEN or (a == OPEN_EXPR_TOKEN and b == OPEN_EXPR_TOKEN) or (a == CLOSE_EXPR_TOKEN and b == CLOSE_EXPR_TOKEN) or a == OPEN_EXPR_TOKEN or b == CLOSE_EXPR_TOKEN:
                continue
            else:
                new_parts.append(MULTIPLY_TOKEN)
        new_parts.append(parts[-1])

        parts = new_parts

        # Shunting yard implementation to order the operations
        ops = []    # stack
        output_queue = []
        # print(f"\nEXPR: {unit_expr}")
        # print(f"TOKENS: {parts}")
        parts.reverse()
        # print(f"TOKENS (reversed): {parts}")
        while len(parts) > 0:
            token = parts.pop()

            if token in (DIVIDE_TOKEN, MULTIPLY_TOKEN):
                while len(ops) > 0 and ops[-1] != OPEN_EXPR_TOKEN:
                    output_queue.append(ops.pop())
                ops.append(token)
            elif token == OPEN_EXPR_TOKEN:
                ops.append(token)
            elif token == CLOSE_EXPR_TOKEN:
                assert len(ops) > 0, "Parenthesis mismatch: closed but never opened"
                while ops[-1] != OPEN_EXPR_TOKEN:
                    output_queue.append(ops.pop())
                assert ops[-1] == OPEN_EXPR_TOKEN, "Parenthesis mismatch"
                ops.pop()   # Discard open paren
            else:  # either a Quantity or a Unit
                output_queue.append(token)

        # Clean up by moving remaining ops onto the output queue
        while len(ops) > 0:
            assert ops[-1] != OPEN_EXPR_TOKEN, "Parenthesis mismatch"
            output_queue.append(ops.pop())

        # print(f"RPN: {output_queue}")

        operands = []
        for op in output_queue:
            # print(f"EVAL: {operands}")
            if op == DIVIDE_TOKEN:
                assert len(operands) >= 2, f"Expected two operands for divide operation but got {len(operands)}"
                b = operands.pop()
                a = operands.pop()
                operands.append(a / b)
                # print(f"EVAL: /")
            elif op == MULTIPLY_TOKEN:
                assert len(operands) >= 2, f"Expected two operands for divide operation but got {len(operands)}"
                b = operands.pop()
                a = operands.pop()
                operands.append(a * b)
                # print(f"EVAL: *")
            else:
                operands.append(op)

        assert len(operands) == 1, f"Incomplete expression: {unit_expr} --- some tokens remained after evaluation: {operands[1:]}"

        return operands[0]
