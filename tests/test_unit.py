
import unittest

from pintless import Registry, Quantity, Unit


class UnitTest(unittest.TestCase):

    def setUp(self) -> None:
        self.r = Registry()

    def test_dimensionless_unit(self):

        unit = self.r.get_unit("meter")
        assert unit.dimensionless_unit == self.r.get_unit("")
        assert unit.dimensionless_unit == (unit / unit)

    def test_dimensionality(self):

        length_b = self.r.get_unit("meter")
        length_a = self.r.get_unit("inch")

        assert length_a.unit_type == "[length]/[dimensionless]"
        assert length_b.unit_type == "[length]/[dimensionless]"

        # length/length should cancel to be dimensionless
        assert (length_a / length_b).unit_type == "[dimensionless]/[dimensionless]"

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
