


from pintless import Registry

reg = Registry()



quantity = 10 * reg.meter

ms = (reg.m * 3) * (reg.s * 30)
print(f"-> m*s: {ms}")
msi = ms * (6 * reg.inch)
print(f"-> m*s*inches: {msi}")


ms2 = (reg.m * 3) * (reg.s * 30)
print(f"-> m*s [2]: {ms2}")
print(f"ms + ms2 = {ms + ms2}")

# Unit only calculations
meter_hours = reg.m * reg.H   # meter*hours
mh50 = 50 * meter_hours
print(f"mh50: {mh50}")


# and division (should work on base units)
meters = meter_hours / reg.meter
hours = meter_hours / reg.hour
seconds = meter_hours / reg.second
print(f"meters: {meters}")
print(f"hours: {hours}")
print(f"seconds?: {seconds}")

time = 10 * reg.H
distance = 1 * reg.mile
print(f"time / distance: {time / distance}")

print(f"Cancelling: {distance/distance} and {time/time} and {mh50 / mh50}")
print(f"Cancelling with conversion: {(10 * reg.km) / (20 * reg.meter)}")



# Dimensionless numbers
print("Dimensionless numbers and interacting with floats")
a = 45 * reg.dimensionless
b = 50 * reg.dimensionless
print(f"Dimensionless number a={a}, b={b}, a+b={a+b}, a*b={a*b}, a/b={a/b}, a*10={a*10}")
print(f"Dimensionless * unit: {a * reg.hour}, *ratio: {a * reg.Hz}, *product: {a*reg.kWh}")


# product types
kwh = 10 * reg.kWh
print(f"-> {kwh} / 5h = {kwh / (5 * reg.hour)}")

# Ratio types
rate = 5 * reg.Hz
print(f"Ratio types: {rate} * 100s = ({rate * (100 * reg.second)})")


# Multiply quantities by units
start = 14 * reg.ms
second = start * reg.ms
third = second * reg.ms


import code; code.interact(local=locals())