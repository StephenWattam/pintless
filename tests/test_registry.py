import unittest

from pintless import Registry, UndefinedUnitError


class RegistryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.r = Registry()

    def test_create_registry(self):

        # With default units json
        r = Registry()
        assert isinstance(r, Registry)

    def test_compound_unit_aliasing(self):
        """Test basic (forward) aliasing: compound units have a simple name
        assigned by the registry, and will serialise to this name.

        This alias shouldn't affect any of the other comparisons
        """
        kwh = self.r.kWh
        assert kwh.name == "kWh"
        assert kwh == self.r.kW * self.r.H
        assert self.r("kWh") == self.r("kW H")

        hz = self.r.Hz
        assert hz.name == "Hz"
        assert hz * self.r.second == self.r.dimensionless_unit

    def test_scaled_dimensionless_units(self):

        r = Registry()

        dimensionless = r.dimensionless
        kdimensionless = r.kilodimensionless

        assert dimensionless.numerator_units[0].multiplier == 1
        assert kdimensionless.numerator_units[0].multiplier == 1000

    def test_scaled_complex_units(self):

        r = Registry()

        assert r.Hz != r.kHz
        assert r.kWh != r.Wh

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
        with self.assertRaises(UndefinedUnitError):
            unit = self.r.get_unit("noexisty")

        # Novel compound unit, created by arithmetic on existing units
        unit = self.r.get_unit("cm / hour")

        unit = self.r.get_unit("cm * mile / hour")
        unit = self.r.get_unit("cm / mile / hour")
        unit = self.r.get_unit("cm * Hz / hour")
        unit = self.r.get_unit("second * Hz")
        unit = self.r.get_unit("kWh * minute * Hz / dimensionless")
        # assert self.r.get_unit("cm/hour * kWh") == (self.r.get_unit("cm") * self.r.get_unit("watt"))

    def test_string_parser_data_types(self):
        """Most numbers in expressions will return floats, unless they are all digits"""
        assert isinstance(self.r("-4 kWh").magnitude, int)
        assert isinstance(self.r("4 kWh").magnitude, int)
        assert isinstance(self.r("4.0 kWh").magnitude, float)

        # Coerce to float
        assert isinstance(self.r("4.0 kWh / 3").magnitude, float)
        assert isinstance(self.r("4.0 * 3").magnitude, float)

    def test_create_quantities_from_string(self):
        """Numeric values in expressions will cause the parser to return a Quantity."""
        assert self.r.get_unit("4 kWh") == (self.r.kWh * 4)
        assert self.r.get_unit("4 * kWh") == (self.r.kWh * 4)
        assert self.r.get_unit("kW * H * 4") == (self.r.kWh * 4)
        assert self.r.get_unit("kW H 4") == (self.r.kWh * 4)
        assert self.r.get_unit("4 * 7") == 4 * 7 * self.r.dimensionless_unit

        assert self.r("GBP / watt hour") == self.r.GBP / self.r.watt * self.r.hour
        assert self.r("GBP / watt * hour") == self.r.GBP / self.r.watt * self.r.hour
        assert self.r("(GBP / watt) * hour") == (self.r.GBP / self.r.watt) * self.r.hour
        assert self.r("(GBP / watt) hour") == (self.r.GBP / self.r.watt) * self.r.hour
        assert self.r("GBP / (watt * hour)") == self.r.GBP / (self.r.watt * self.r.hour)
        assert self.r("GBP / (watt hour)") == self.r.GBP / (self.r.watt * self.r.hour)
        assert self.r("(4) * (7)") == 4 * 7 * self.r.dimensionless_unit
        assert self.r("(4) * (7 kWh)") == 4 * 7 * self.r.kWh

        with self.assertRaises(ValueError):
            self.r("(4 kWh")  # mismatched brackets

    def test_serialisation_to_from_string(self):
        """Ensure serialisation/deserialisation is reliable"""
        test_strings = [
            "4 kWh",
            "kWh",
            "",
            "hour / second",
            "GBP / watt_hour",
            "kWh / watt_hour",
        ]

        for test_string in test_strings:
            self.assertEqual(self.r(str(self.r(test_string))), self.r(test_string))

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
