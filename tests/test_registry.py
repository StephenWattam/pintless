

import unittest

from pintless import Registry, Quantity, Unit


class RegistryTest(unittest.TestCase):

    def setUp(self) -> None:
        self.r = Registry()

    def test_create_registry(self):

        # With default units json
        r = Registry()
        assert isinstance(r, Registry)

    def test_create_units_linked_to_registry(self):

        # This is the default
        r = Registry(link_to_registry=True)

        unit = r.get_unit("meter")
        assert unit.registry == r

    def test_create_units_from_string(self):

        # centimeter
        unit = self.r.get_unit("cm")
        assert unit == (10 * self.r.cm).unit

        # Unit that doesn't exist
        with self.assertRaises(ValueError):
            unit = self.r.get_unit("noexisty")

        # Novel compound unit, created by arithmetic on existing units
        unit = self.r.get_unit("cm / hour")

        unit = self.r.get_unit("cm * mile / hour")
        unit = self.r.get_unit("cm / mile / hour")
        unit = self.r.get_unit("cm * Hz / hour")
        unit = self.r.get_unit("second * Hz")
        unit = self.r.get_unit("kWh * minute * Hz / dimensionless")
        assert self.r.get_unit("cm/hour * kWh") == (self.r.get_unit("cm") * self.r.get_unit("watt"))

    def test_create_types_by_multiplication(self):

        r = self.r

        # Simple unit
        value = 10 * r.meter

        assert value.unit == r.get_unit("meter")
        assert value.magnitude == 10

        # Multiplied unit
        value = 10 * r.kWh
        assert value.unit == r.get_unit("kWh")
        assert value.magnitude == 10

        # Divided unit
        value = 10 * r.Hz
        assert value.unit == r.get_unit("Hz")
        assert value.magnitude == 10

    def test_simple_unit_conversion(self):

        r = self.r

        qmetres = 10 * r.m
        assert qmetres.magnitude == 10
        cm = qmetres.to(r.cm)
        assert cm.magnitude == 10 * 100

