"""A small script to benchmark the unit library against pint."""

import time
# from random import random
from typing import Union

from pint import UnitRegistry
from pintless import Registry


def run_benchmark(r: Union[UnitRegistry, Registry]) -> float:
    start = time.time()

    for _ in range(10_000):

        # Basic arithmetic
        length_a = 10 * r.meter
        length_b = 10 * r.inch
        result = length_a + length_b * 10

        # Unit arithmetic
        result = length_a * r.kWh
        result = r.kWh / r.second
        result = r.Hz * r.hour

        # Parsing strings
        result = length_a.to("inch")
        result = length_b.to("mile")

        # Some more arithmetic with just units
        l = 1 * r.litre
        vol = 0.001 * r.m * r.m * r.m
        vol2 = 1 * r.dm * r.dm * r.dm

        r("4 kWh") == (r.kWh * 4)
        r("4 * kWh") == (r.kWh * 4)

        r("kelvin / watt hour") == r.kelvin / r.watt * r.hour
        r("kelvin / watt * hour") == r.kelvin / r.watt * r.hour
        r("(kelvin / watt) * hour") == (r.kelvin / r.watt) * r.hour
        r("(kelvin / watt) hour") == (r.kelvin / r.watt) * r.hour
        r("kelvin / (watt * hour)") == r.kelvin / (r.watt * r.hour)
        r("kelvin / (watt hour)") == r.kelvin / (r.watt * r.hour)
        r("(4) * (7 kWh)") == 4 * 7 * r.kWh

        # The latest pint objects to this pattern, though earlier versions support it
        # a_list = [random() * 300 for x in range(1000)]
        # list_type = r.cm * a_list
        # for _ in range(100):
        #     i = int(random() * len(a_list))
        #     quantity = list_type[i]
        #     string = str(quantity)
        # new_list = list_type.to(r("inch"))

    end = time.time()

    return end - start


pintful_reg = UnitRegistry()
time_pint = run_benchmark(pintful_reg)
pintless_reg = Registry()
time_pintless = run_benchmark(pintless_reg)

print(f"    Time (pint): {time_pint:0.4}s")
print(f"Time (pintless): {time_pintless:0.4}s")
print("")
print(f"Pintless is {time_pint/time_pintless:0.4} times faster")
