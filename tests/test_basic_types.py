
from pintless import Registry, Quantity, Unit

r = Registry()

def test_create_types_by_multiplication():

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

def test_simple_unit_conversion():

    qmetres = 10 * r.m
    assert qmetres.magnitude == 10
    cm = qmetres.to(r.cm)
    assert cm.magnitude == 10 * 100


