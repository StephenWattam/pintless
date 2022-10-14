


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



import code; code.interact(local=locals())