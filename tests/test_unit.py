import unittest

from pintless import Registry


class BaseUnitTest(unittest.TestCase):
    def setUp(self) -> None:
        self.r = Registry()

    def test_base_unit_equality(self):
        """
        Base units are the same if they are the same multiplier on top of
        the same base unit.

        This implies they have the same dimensionality
        """
        base_kw = self.r.kW.numerator_units[0]
        base_kw2 = self.r.kilowatt.numerator_units[0]
        assert base_kw == base_kw2


class UnitTest(unittest.TestCase):
    def setUp(self) -> None:
        self.r = Registry()

    def test_dimensionless_unit(self):
        """A unit that represents no unit"""
        # Division by self should result in dimensionless unit
        unit_strings = ["meter", "cm", "kWh", "GBP / (meter * meter)"]
        for unit_str in unit_strings:
            unit = self.r.get_unit(unit_str)
            assert unit.dimensionless_unit == self.r.get_unit("")
            assert unit.dimensionless_unit == (unit / unit)

        # Create dimensionless unit using empty string, numbers, explicitly
        assert self.r("") == self.r.dimensionless_unit
        assert self.r("").dimensionless_unit == self.r.dimensionless_unit
        assert self.r("4").unit == self.r.dimensionless_unit
        assert str(self.r.dimensionless_unit) == "dimensionless"

        # X / dimensionless = X
        assert self.r.cm / self.r.dimensionless_unit == self.r.cm
        assert self.r.kWh / self.r.dimensionless_unit == self.r.kWh

    def test_unit_arithmetic(self):
        """Basic tests of unit arithmetic"""
        self.assertEqual(str(self.r.kWh / self.r.m), "(kwatt*hour)/m")
        self.assertEqual(
            str(self.r.kWh / self.r.m * self.r.hour), "(kwatt*hour*hour)/m"
        )
        self.assertEqual(str(self.r.kWh / self.r.m * self.r.amp), "(amp*kwatt*hour)/m")

    def test_unit_names(self):
        """Test conversion to a string"""
        # Alias behavour
        assert str(self.r.kWh) == "kWh"

        # Basic arithmetic
        assert str(self.r.kW * self.r.hour) == "kW*hour"
        assert str(self.r.kilowatt * self.r.hour) == "kilowatt*hour"
        assert str(self.r.kW * self.r.hour / self.r.GBP) == "(kW*hour)/GBP"

    def test_dimensionality_check(self):
        """
        A relaxed form of equality, this can be used to check that one unit
        can be converted into another
        """
        unit_kwh = self.r.kWh
        unit_joules = self.r.joule
        unit_watts = self.r.watt
        assert unit_kwh.compatible_with(unit_joules)
        assert unit_kwh.compatible_with(unit_watts) is False

        assert self.r("kg/Mwatt*hour").compatible_with(self.r("g")) is False

    def test_derived_unit_conversion(self):

        l = 1 * self.r.litre
        vol = 0.001 * self.r.m * self.r.m * self.r.m
        vol2 = 1 * self.r.dm * self.r.dm * self.r.dm
        self.assertAlmostEqual(vol.to("litre").magnitude, l.magnitude)
        self.assertAlmostEqual(vol2.to("litre").magnitude, l.magnitude)

    def test_power_operator(self):

        assert self.r.m**1 == self.r.m
        assert self.r.m**2 == self.r.m * self.r.m
        assert self.r.m**3 == self.r.m * self.r.m * self.r.m

    def test_equality(self):

        r = self.r

        # Basic building blocks are the base units
        base_unit_a = r.meter.numerator_units[0]
        base_unit_b = r.meter.numerator_units[0]
        assert base_unit_a == base_unit_b

        base_unit_a = r.kilometer.numerator_units[0]
        base_unit_b = r.meter.numerator_units[0]
        assert base_unit_a != base_unit_b

        # Units with different scales in the same dimension
        # are not equal
        assert r.meter != r.kilometer
        assert r.dimensionless != r.kilodimensionless

        # Check product units
        assert r.meter * r.second == r.meter * r.second
        assert r.Hz == r.dimensionless / r.second

    def test_dimensionality(self):

        length_b = self.r.get_unit("meter")
        length_a = self.r.get_unit("inch")

        assert length_a.unit_type == "[length]/[dimensionless]"
        assert length_b.unit_type == "[length]/[dimensionless]"

        # length/length should cancel to be dimensionless
        assert (length_a / length_b).unit_type == "[dimensionless]/[dimensionless]"

    def test_conversion_factor(self):

        r = self.r

        # Basics.
        assert r.meter.conversion_factor(r.cm) == 100
        assert r.meter.conversion_factor(r.kilometer) == 0.001

        # Conversion for more complex types
        assert r.Hz.conversion_factor(r.kHz) == 0.001

        # Conversion between incompatible types
        with self.assertRaises(TypeError):
            r.meter.conversion_factor(r.hour)
        with self.assertRaises(TypeError):
            r.meter.conversion_factor(r.Hz)
        with self.assertRaises(TypeError):
            r.meter.conversion_factor(r.dimensionless)

    def test_simplify(self):

        r = self.r

        time = r.H
        distance = r.mile
        assert (time / distance).name == "H/mile"

        # Cancelling denominator units
        assert (r.kW * r.hour) / (r.mile * r.hour) == (r.kW / r.mile)

        # Cancelling with and without conversion factor
        self.assertEqual((10 * r.km) / (20 * r.km), 0.5 * r.dimensionless)
        self.assertEqual((10 * r.km) / (20 * r.meter), 500)
        self.assertEqual((10 * r.km) * (5 * r.meter), 50 * r.km * r.meter)
