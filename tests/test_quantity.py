

import unittest

from pintless import Registry, Quantity, Unit


class QuantityTest(unittest.TestCase):

    def setUp(self) -> None:
        self.r = Registry()

    def test_no_string_instantiation(self):
        """To create a Quantity from an expression, we must use a registry"""

        # This should not work
        with self.assertRaises(TypeError):
            Quantity(4.0, "kWh / mile")
        # But this should
        assert 4.0 * self.r.kWh / self.r.mile == self.r("4.0 kWh / mile")

    def test_create_types_by_multiplication(self):

        r = self.r

        # Simple unit
        value = 10 * r.meter

        assert 10 * r.meter == r.meter * 10
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

    def test_mix_quantities_and_units(self):

        q = 10 * self.r.m
        u = self.r.second

        self.assertEqual(q * u, u * q)

    def test_add_quantities(self):

        r = self.r

        length_a = 5 * r.meter
        length_b = 5 * r.inch
        rate_a = 10 * r.Hz

        # Sum with same dimension
        # assert isinstance(length_a + length_b, Quantity)

        # Sum with different dimensionality leads to failure
        with self.assertRaises(TypeError):
            rate_a + length_a
        with self.assertRaises(TypeError):
            14 + rate_a
        with self.assertRaises(TypeError):
            rate_a + 14

        # Sum with items that have no unit
        assert 5 + (10 * r.dimensionless) == Quantity(15, r.get_unit("dimensionless"))

    def test_compare_against_non_quantity(self):

        r = self.r

        assert 100 == 100 * r.dimensionless
        assert 100.0 == 100.0 * r.dimensionless
        assert "non-numeric-value" == "non-numeric-value" * r.dimensionless
