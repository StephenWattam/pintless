

# from pint import UnitRegistry
# ureg = UnitRegistry()


from pintless import Registry
ureg = Registry()

distance = 24.0 * ureg.meter

assert str(distance) == "24.0 meter"


assert distance.magnitude == 24.0
assert distance.units == ureg.meter
assert distance.dimensionality == "[length]"




time = 8.0 * ureg.second
assert str(time) == "8.0 second"
speed = distance / time
assert speed.units == ureg.meter / ureg.second

assert speed.magnitude == 3.0
assert str(speed) == "3.0 meter / second"
assert str(speed.dimensionality) == "[length] / [time]"


# print(f" ===> {speed.to('inch/minute')}")
# assert speed.to('inch/minute') == 7086.614173228347 * ureg.inch / ureg.minute
# assert speed.to(ureg.inch / ureg.minute) == speed.to("inch/minute")


assert str(speed) == "3.0 meter / second"

# speed.ito("inch/minute")
# assert str(speed) == "7086.614173228347 inch / minute"






print(f"------")
print(f"Stuff completed successfully, here's a REPL")
import code; code.interact(local=locals())