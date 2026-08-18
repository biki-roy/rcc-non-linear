import pytest
from rcc_non_linear import (
    Model,
    HingeRadau,
    HingeRadauTwo,
    HingeMidpoint,
    HingeEndpoint,
    UserHinge,
    Lobatto,
    Legendre,
    NewtonCotes,
    Radau,
    Trapezoidal,
    CompositeSimpson,
    UserDefined,
)

@pytest.fixture
def base_props():
    return {
        'fc': 6.1,
        'D': 48,
        'L': 324,
        'cover': 2,
        'nBars': 18,
        'db': 1.41,
        'fy': 75.2,
        'fu': 102.4,
        'Es': 29000,
        'Esh': 1247,
        'e_sh': 0.005,
        'e_ult': 0.122,
        'dh': 0.888,
        'sh': 6,
        'fyh': 54.8,
        'esm': 0.125,
        'P_axial': 570,
        'nAng': 12,
        'nRad': 6,
        'nRad_cover': 3
    }


def test_plastic_hinge_integrations(base_props):
    hinge_rules = [
        HingeRadau(),
        HingeRadauTwo(),
        HingeMidpoint(),
        HingeEndpoint(),
    ]
    for rule in hinge_rules:
        props = dict(base_props, integration=rule)
        model = Model(props)
        results_df, bilinear_df, yield_step = model.run_pushover_analysis(dU=1.0)
        assert len(results_df) > 3
        assert yield_step is not None
        assert len(bilinear_df) == 4


def test_distributed_plasticity_integrations(base_props):
    distributed_rules = [
        Lobatto(num_points=4),
        Legendre(num_points=4),
        NewtonCotes(num_points=4),
        Radau(num_points=4),
        Trapezoidal(num_points=4),
        CompositeSimpson(num_points=5),
    ]
    for rule in distributed_rules:
        props = dict(base_props, integration=rule)
        model = Model(props)
        results_df, bilinear_df, yield_step = model.run_pushover_analysis(dU=1.0)
        assert len(results_df) > 3
        assert yield_step is not None
        assert len(bilinear_df) == 4
