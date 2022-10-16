import os
import json
from functools import lru_cache
from .quantity import Quantity
from .unit import Unit, UnitProduct, UnitRatio

DEFAULT_DEFINITION_FILE = "units.json"
PREFIX_KEY = "__prefixes__"
DIMENSIONLESS_UNIT_NAME = "dimensionless"

class Registry:
    def __init__(self, definition_file=None):

        if definition_file is None:
            definition_file = (
                os.path.dirname(os.path.realpath(__file__))
                + os.sep
                + DEFAULT_DEFINITION_FILE
            )

        # Read definitions from file
        with open(definition_file) as fin:
            defs = json.load(fin)

        # Assign definitions to various categories, and support forward/reverse lookup
        # by unit type
        self.units = set()
        self.base_type_for_utype = {}
        self.units_for_utype = {}
        self.utype_for_unit = {}
        self.product_types = {}
        self.ratio_types = {}

        # Read prefixes then process them later
        prefixes = defs[PREFIX_KEY]
        del defs[PREFIX_KEY]

        for utype, units in defs.items():

            # Create a forward index for the unit type
            utype = (
                f"[{utype}]"  # XXX: pint types have brackets.  This is for compat only
            )
            self.units_for_utype[utype] = {}

            # For every unit, for every prefix, calculate a multiplier down to the 'base unit'
            # for that unit type
            for unit_name, multiplier in units.items():

                # The first entry in the dict is the base type
                if utype not in self.base_type_for_utype:
                    self.base_type_for_utype[utype] = unit_name

                # handle compound types
                if (
                    isinstance(multiplier, dict)
                    and "__relation__" in multiplier
                    and multiplier["__relation__"] == "product"
                ):
                    assert (
                        "units" in multiplier
                    ), f"Missing 'units' list for product type '{unit_name}'"
                    assert (
                        len(multiplier["units"]) > 1
                    ), "List of units for a product type must be greater than 1"

                    for prefix, prefix_multiplier in prefixes.items():
                        self.product_types[prefix + unit_name] = [
                            prefix + multiplier["units"][0]
                        ] + multiplier["units"][1:]
                        self.units.add(prefix + unit_name)
                    continue

                if (
                    isinstance(multiplier, dict)
                    and "__relation__" in multiplier
                    and multiplier["__relation__"] == "ratio"
                ):
                    assert (
                        "units" in multiplier
                    ), f"Missing 'units' list for ratio type '{unit_name}'"
                    assert (
                        len(multiplier["units"]) == 2
                    ), f"Cannot create ratio type with number of units other than two (unit name: {unit_name})"
                    for prefix, prefix_multiplier in prefixes.items():
                        self.ratio_types[prefix + unit_name] = [
                            prefix + multiplier["units"][0],
                            multiplier["units"][1],
                        ]
                        self.units.add(prefix + unit_name)
                    continue

                # and all prefix forms
                for prefix, prefix_multiplier in prefixes.items():
                    self.units_for_utype[utype][prefix + unit_name] = (
                        prefix_multiplier * multiplier
                    )
                    self.utype_for_unit[prefix + unit_name] = utype
                    self.units.add(prefix + unit_name)

            # Check we have a base unit for the unit type
            assert (
                utype in self.base_type_for_utype
            ), f"No base unit defined for unit type {utype}"

        assert "dimensionless" in self.units, f"A unit with name '{DIMENSIONLESS_UNIT_NAME}' must be defined"

        # Define the "multiply method" on this registry
        for unit_name in self.units:
            setattr(self, unit_name, self.get_unit(unit_name))

    @lru_cache
    def get_unit(self, unit_name: str) -> Unit:

        if unit_name not in self.units:
            raise ValueError(f"Unit '{unit_name}' not round in registry")

        if unit_name in self.product_types:
            return UnitProduct([self.get_unit(u_n) for u_n in self.product_types[unit_name]])

        if unit_name in self.ratio_types:
            return UnitRatio(self.get_unit(self.ratio_types[unit_name][0]),
                             self.get_unit(self.ratio_types[unit_name][1]))

        # Base case, the unit itself
        unit_type = self.utype_for_unit[unit_name]
        base_type = self.base_type_for_utype[unit_type]
        multiplier = self.units_for_utype[unit_type][unit_name]

        if unit_name == DIMENSIONLESS_UNIT_NAME:
            return Unit(unit_name, unit_type, base_type, multiplier, None)
        return Unit(unit_name, unit_type, base_type, multiplier, self.get_unit(DIMENSIONLESS_UNIT_NAME))
