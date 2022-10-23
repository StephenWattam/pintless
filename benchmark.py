"""A small script to benchmark the unit library against pint."""

from pint import UnitRegistry
from pintless import Registry
from typing import Union
import time


def run_benchmark(r: Union[UnitRegistry, Registry]) -> float:
    start = time.time()

    for _ in range(100_000):

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
        # result = r.get_unit("mile / hour")

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
