
import os
import json
from .quantity import Quantity
from .unit import Unit

DEFAULT_DEFINITION_FILE = "units.json"
PREFIX_KEY = "__prefixes__"


class Registry:

    def __init__(self, definition_file=None):

        if definition_file is None:
            definition_file = os.path.dirname(os.path.realpath(__file__)) + os.sep + DEFAULT_DEFINITION_FILE

        with open(definition_file) as fin:
            self._parse_definitions(json.load(fin))

        self._register_methods()

    def _register_methods(self):
        """Define a method to return a unit type for each unit."""

        for unit_type, units in self.units_for_utype.items():
            for unit_name, multiplier in units.items():
                base_type = self.base_type_for_utype[self.utype_for_unit[unit_name]]
                setattr(self, unit_name, Unit(unit_name, unit_type, base_type, multiplier))

    def _parse_definitions(self, defs):
        """Handle the unit hierarchy"""

        self.base_type_for_utype = {}
        self.units_for_utype = {}
        self.utype_for_unit = {}

        # Read prefixes then process them later
        prefixes = defs[PREFIX_KEY]
        del defs[PREFIX_KEY]

        for utype, units in defs.items():

            # Create a forward index for the unit type
            self.units_for_utype[utype] = {}

            # For every unit, for every prefix, calculate a multiplier down to the 'base unit'
            # for that unit type
            for unit_name, multiplier in units.items():

                # The first one in the list with a multiplier of 1 is the base unit
                if multiplier == 1:
                    self.base_type_for_utype[utype] = unit_name

                # Add the raw unit, converting to the base unit
                self.units_for_utype[utype][unit_name] = multiplier
                self.utype_for_unit[unit_name] = utype
                # and all prefix forms
                for prefix, prefix_multiplier in prefixes.items():
                    assert prefix[-1] == "-", f"Prefix does not have dash at the end: {prefix}"
                    expanded_unit_name = prefix[:-1] + unit_name
                    self.units_for_utype[utype][expanded_unit_name] = prefix_multiplier * multiplier
                    self.utype_for_unit[expanded_unit_name] = utype

            # Check we have a base unit for the unit type
            assert utype in self.base_type_for_utype, f"No base unit defined for unit type {utype}"
