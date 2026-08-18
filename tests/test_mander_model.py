import pytest
from rcc_non_linear.concrete_models.mander_model import CircConcreteMander, RectConcreteMander

def test_circular_mander_confined_properties():
    cm = CircConcreteMander(
        fc_prime=6.1,
        D=48,
        cover=2.0,
        dh=0.888,
        sh=6.0,
        fyh=54.8,
        esm=0.125
    )
    conf_props = cm.confined_props()
    unconf_props = cm.unconfined_props()

    # Confined peak strength |f'cc| should be higher than unconfined |f'co|
    fcc, eps_cc, ecu = abs(conf_props[0]), abs(conf_props[1]), abs(conf_props[3])
    fco, eps_co, spall = abs(unconf_props[0]), abs(unconf_props[1]), abs(unconf_props[3])

    assert fcc > fco
    assert eps_cc > eps_co
    assert ecu > spall
    assert cm.fcc_prime > cm.fc_prime


def test_rectangular_mander_confined_properties():
    rm = RectConcreteMander(
        fc_prime=5.5,
        B=20,
        H=30,
        cover=1.5,
        dh=0.375,
        sh=3.0,
        fyh=68.0,
        esm=0.12,
        nx=2,
        ny=2,
        ke=0.75
    )
    conf_props = rm.confined_props()
    unconf_props = rm.unconfined_props()

    fcc, eps_cc, ecu = abs(conf_props[0]), abs(conf_props[1]), abs(conf_props[3])
    fco, eps_co, spall = abs(unconf_props[0]), abs(unconf_props[1]), abs(unconf_props[3])

    assert fcc > fco
    assert eps_cc > eps_co
    assert ecu > spall
    assert rm.k > 1.0
