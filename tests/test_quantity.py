import unittest

from pintless import Registry, Quantity


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

    def test_m_as(self):
        """Test output of magnitudes with dynamic conversion"""

        quantity = 100 * self.r.metre
        self.assertAlmostEqual(quantity.m_as("km"), 0.1)
        self.assertAlmostEqual(quantity.m_as("inch"), 3937.0078740157483)

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

    def test_complex_unit_conversion(self):
        """Unit conversion with compound units"""

        r = self.r

        # Convert both numerator and denominator at once
        x = 1 * r("km/hour")
        y = r.m / r.second
        self.assertEqual(x.to(y), Quantity(0.2777777777777778, r("meter/second")))
        self.assertAlmostEqual(x.m_as(y), 0.2777777777777778)

        # Compound units
        x = 1 * r("kWh")
        y = r.watt * r.second
        z = r.joule
        self.assertEqual(x.to(y), Quantity(3.6e6, y))
        self.assertEqual(x.to(z), Quantity(3.6e6, y))
        self.assertEqual(x.to(y), Quantity(3.6e6, z))

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
        assert 0 == 0 * r.kWh
        assert 0.0 == 0 * r.Hz
        self.assertListEqual(
            [0.0, 0, 0, 4 * r.kWh],
            [0 * r.Hz, 0.0 * r.joule, 0 * r.dimensionless, 4 * r.kWh],
        )
        self.assertEqual([0, 0.0, 0, 4 * r.kWh], Quantity([0, 0, 0, 4], r.kWh))
        self.assertNotEqual(Quantity([0, 0, 0, 4], r.kWh), [0, 0, 0, 0])

    def test_list_types(self):
        """Quantities support limited operations on lists"""

        self.assertEqual([1, 2, 3] * self.r.kWh, Quantity([1, 2, 3], self.r.kWh))
        self.assertEqual(
            [1000, 2000, 3000], ([1, 2, 3] * self.r.kWh).m_as(self.r.watt * self.r.hour)
        )

        # Basic conversions
        list_quantity_cm = [1, 2, 3] * self.r.cm
        list_quantity_inches = [4, 5, 6] * self.r.inch
        with self.assertRaises(ValueError):
            list_quantity_cm * list_quantity_inches
        self.assertListEqual(
            list_quantity_cm.to(self.r("inch")).magnitude,
            [Quantity(x, self.r.cm).to(self.r.inch).magnitude for x in [1, 2, 3]],
        )

        # Ensure arithmetic with non-lists works
        self.assertEqual(list_quantity_cm * 4, [4, 8, 12] * self.r.cm)
        self.assertEqual(
            list_quantity_cm * self.r("4 kW"), [4, 8, 12] * self.r.cm * self.r.kW
        )

        # Get items
        self.assertEqual(list_quantity_cm[1], Quantity(2, self.r.cm))
