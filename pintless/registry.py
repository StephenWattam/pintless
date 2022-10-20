import os
import json
from functools import lru_cache
from .unit import BaseUnit, Unit
import logging

DEFAULT_DEFINITION_FILE = "units.json"
PREFIX_KEY = "__prefixes__"
DIMENSIONLESS_UNIT_NAME = "dimensionless"

logging.basicConfig()
log = logging.getLogger()

class Registry:
    def __init__(self, definition_filename=None):

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
                            numerator_list,
                            denominator_list,
                        )
                        if prefix + unit_name in self.units:
                            log.warn("Detected duplicate unit in unit definition: %s", prefix + unit_name)
                        log.debug("Adding derived type for unit: %s", prefix + unit_name)
                        self.units.add(prefix + unit_name)
                    continue

                # and all prefix forms
                for prefix, prefix_multiplier in prefixes.items():
                    self.units_for_utype[utype][prefix + unit_name] = (
                        prefix_multiplier * multiplier
                    )
                    self.utype_for_unit[prefix + unit_name] = utype
                    if prefix + unit_name in self.units:
                        log.warn("Detected duplicate unit in unit definition: %s", prefix + unit_name)
                    log.debug("Adding non-derived type for unit: %s of unit type %s", prefix + unit_name, utype)
                    self.units.add(prefix + unit_name)

            # Check we have a base unit for the unit type
            assert (
                utype in self.base_type_for_utype
            ), f"No base unit defined for unit type {utype}"

        assert (
            "dimensionless" in self.units
        ), f"A unit with name '{DIMENSIONLESS_UNIT_NAME}' must be defined"

        # Define the "multiply method" on this registry
        for unit_name in self.units:
            setattr(self, unit_name, self.get_unit(unit_name))

    @lru_cache
    def get_unit(self, unit_name: str) -> Unit:
        """Return a Unit for a given type.  The unit will not have a value attached
        as it would in a Quantity object.

        Does not support construction of units that are not already listed in the
        units list loaded by the registry, e.g. a registry containing "m" and "s"
        will not return anything for "m/s".  The way of defining such units is to
        define a derived unit "mps".
        """

        if unit_name not in self.units:
            raise ValueError(f"Unit '{unit_name}' not round in registry")

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
        )

    @lru_cache
    def _get_base_unit(self, base_unit_name: str) -> BaseUnit:
        """Return a simple base unit type.  Used to construct units."""

        assert (
            base_unit_name not in self.derived_types
        ), f"Cannot instantiate base unit '{base_unit_name}', as it is a derived type"

        # Base case, the unit itself
        unit_type = self.utype_for_unit[base_unit_name]
        base_type = self.base_type_for_utype[unit_type]
        multiplier = self.units_for_utype[unit_type][base_unit_name]

        return BaseUnit(base_unit_name, unit_type, base_type, multiplier)
